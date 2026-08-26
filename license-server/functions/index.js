const { onRequest } = require('firebase-functions/v2/https');
const { defineSecret } = require('firebase-functions/params');
const { initializeApp } = require('firebase-admin/app');
const { getFirestore, FieldValue, Timestamp } = require('firebase-admin/firestore');
const crypto = require('crypto');

initializeApp();
const db = getFirestore();

const lootlabsApiToken = defineSecret('LOOTLABS_API_TOKEN');
const lootlabsPostbackSecret = defineSecret('LOOTLABS_POSTBACK_SECRET');

const LOOT_LINK = 'https://loot-link.com/s?zTsiS0pO';
const CLAIM_TTL_MS = 20 * 60 * 1000;
const LICENSE_TTL_MS = 24 * 60 * 60 * 1000;

function normalizeKey(v) {
  return String(v || '').trim().toUpperCase().replace(/\s+/g, '');
}

function keyId(key) {
  return crypto.createHash('sha256').update(key).digest('hex');
}

function randomKey() {
  const raw = crypto.randomBytes(12).toString('hex').toUpperCase();
  return `RIU-${raw.slice(0, 6)}-${raw.slice(6, 12)}-${raw.slice(12, 18)}-${raw.slice(18, 24)}`;
}

function reply(res, code, body) {
  res.status(code).json(body);
}

function baseUrl(req) {
  const proto = req.get('x-forwarded-proto') || req.protocol || 'https';
  const host = req.get('host');
  const pathOnly = String(req.originalUrl || '').split('?')[0];
  const reqPath = String(req.path || '/');
  const rootPath = pathOnly.endsWith(reqPath) ? pathOnly.slice(0, pathOnly.length - reqPath.length) : '';
  return `${proto}://${host}${rootPath}`.replace(/\/$/, '');
}

function htmlPage(title, body, script = '') {
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><style>
  :root{color-scheme:dark}body{margin:0;background:#090b13;color:#fff;font-family:Inter,Segoe UI,Arial,sans-serif;display:grid;place-items:center;min-height:100vh}.card{width:min(520px,calc(100vw - 40px));background:#121725;border:1px solid #2a3347;border-radius:20px;padding:26px;box-shadow:0 20px 60px #0008}.brand{font-size:12px;font-weight:800;letter-spacing:.14em;color:#8b5cf6}.title{font-size:28px;font-weight:800;margin:10px 0 8px}.muted{color:#98a2b8;line-height:1.55}.key{font-family:Consolas,monospace;font-size:19px;background:#0b0f19;border:1px solid #38445f;border-radius:12px;padding:15px;margin:18px 0;word-break:break-all}.btn{width:100%;height:44px;border:0;border-radius:11px;background:#7c3aed;color:#fff;font-weight:800;cursor:pointer}.ok{color:#4ade80}.wait{color:#fbbf24}</style></head><body><main class="card"><div class="brand">RIUCLICKER 1.1</div>${body}</main>${script}</body></html>`;
}

async function startClaim(req, res) {
  const deviceId = String(req.query.deviceId || '').trim();
  if (deviceId.length < 12) return res.status(400).send(htmlPage('RiuClicker', '<div class="title">Invalid device</div><div class="muted">Open GET KEY from inside RiuClicker.</div>'));

  const claimId = crypto.randomBytes(20).toString('hex');
  const now = Timestamp.now();
  const expiresAt = Timestamp.fromMillis(Date.now() + CLAIM_TTL_MS);
  await db.collection('claims').doc(claimId).set({ deviceId, createdAt: now, expiresAt, completed: false, issued: false });

  const destination = `${baseUrl(req)}/claim?claimId=${encodeURIComponent(claimId)}`;
  const token = lootlabsApiToken.value();
  if (!token) return res.status(503).send(htmlPage('RiuClicker', '<div class="title">Key server setup required</div><div class="muted">LOOTLABS_API_TOKEN is not configured on the server.</div>'));

  try {
    const apiRes = await fetch('https://creators.lootlabs.gg/api/public/url_encryptor', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination_url: destination, api_token: token })
    });
    const payload = await apiRes.json();
    if (!apiRes.ok || !payload || !payload.message) throw new Error('LootLabs encryptor failed');

    const data = String(payload.message);
    const url = `${LOOT_LINK}&puid=${encodeURIComponent(claimId)}&data=${data}`;
    return res.redirect(302, url);
  } catch (err) {
    console.error(err);
    return res.status(502).send(htmlPage('RiuClicker', '<div class="title">Could not open key flow</div><div class="muted">LootLabs API did not respond. Try again in a moment.</div>'));
  }
}

async function postback(req, res) {
  const expected = lootlabsPostbackSecret.value();
  const provided = String(req.query.secret || '');
  if (!expected || !provided || !crypto.timingSafeEqual(Buffer.from(provided), Buffer.from(expected))) {
    return res.status(403).send('forbidden');
  }

  const claimId = String(req.query.click_id || '').trim();
  const uniqueId = String(req.query.unique_id || '').trim();
  const ip = String(req.query.ip || '').trim();
  if (!claimId) return res.status(400).send('missing click_id');

  const ref = db.collection('claims').doc(claimId);
  const snap = await ref.get();
  if (!snap.exists) return res.status(404).send('unknown claim');
  const d = snap.data();
  if (d.expiresAt && d.expiresAt.toMillis() <= Date.now()) return res.status(410).send('expired');

  await ref.update({ completed: true, completedAt: Timestamp.now(), lootlabsUniqueId: uniqueId, completionIp: ip });
  return res.status(200).send('ok');
}

async function issueOrReadClaim(claimId) {
  const ref = db.collection('claims').doc(claimId);
  return db.runTransaction(async tx => {
    const snap = await tx.get(ref);
    if (!snap.exists) return { state: 'missing' };
    const d = snap.data();
    if (d.expiresAt && d.expiresAt.toMillis() <= Date.now()) return { state: 'expired' };
    if (!d.completed) return { state: 'waiting' };
    if (d.issuedKey) return { state: 'issued', key: d.issuedKey, expiresAt: d.licenseExpiresAt?.toDate?.()?.toISOString?.() || null };

    const key = randomKey();
    const licenseExpiresAt = Timestamp.fromMillis(Date.now() + LICENSE_TTL_MS);
    tx.set(db.collection('licenses').doc(keyId(key)), {
      plan: 'LOOTLINK-24H',
      disabled: false,
      maxDevices: 1,
      devices: [String(d.deviceId || '')],
      createdAt: Timestamp.now(),
      activatedAt: Timestamp.now(),
      expiresAt: licenseExpiresAt,
      source: 'lootlabs'
    });
    tx.update(ref, { issued: true, issuedKey: key, issuedAt: Timestamp.now(), licenseExpiresAt });
    return { state: 'issued', key, expiresAt: licenseExpiresAt.toDate().toISOString() };
  });
}

async function claimPage(req, res) {
  const claimId = String(req.query.claimId || '').trim();
  if (!claimId) return res.status(400).send(htmlPage('RiuClicker Key', '<div class="title">Missing claim</div>'));

  const result = await issueOrReadClaim(claimId);
  if (result.state === 'missing') return res.status(404).send(htmlPage('RiuClicker Key', '<div class="title">Unknown key session</div><div class="muted">Press GET KEY inside RiuClicker and try again.</div>'));
  if (result.state === 'expired') return res.status(410).send(htmlPage('RiuClicker Key', '<div class="title">Session expired</div><div class="muted">Return to RiuClicker and press GET KEY again.</div>'));
  if (result.state === 'waiting') {
    const body = '<div class="title">Finishing verification…</div><div class="muted">LootLabs completion is being confirmed. This page will refresh automatically.</div><div class="wait" style="margin-top:16px">WAITING FOR POSTBACK</div>';
    const script = '<script>setTimeout(()=>location.reload(),2000)</script>';
    return res.status(202).send(htmlPage('RiuClicker Key', body, script));
  }

  const safeKey = String(result.key).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const body = `<div class="title">Your key is ready</div><div class="muted">Copy this key and paste it into RiuClicker. It is bound to the PC that started the key flow and is valid for 24 hours.</div><div id="key" class="key">${safeKey}</div><button class="btn" onclick="navigator.clipboard.writeText(document.getElementById('key').innerText);this.innerText='COPIED'">COPY KEY</button><div class="ok" style="margin-top:15px">KEY ISSUED SUCCESSFULLY</div>`;
  return res.status(200).send(htmlPage('RiuClicker Key', body));
}

async function validateLicense(req, res) {
  if (req.method !== 'POST') return reply(res, 405, { ok: false, message: 'POST required' });

  const action = String(req.body?.action || '');
  const key = normalizeKey(req.body?.key);
  const deviceId = String(req.body?.deviceId || '').trim();
  const app = String(req.body?.app || '');

  if (app !== 'RiuClicker' || !key || key.length < 12 || deviceId.length < 12)
    return reply(res, 400, { ok: false, message: 'Invalid request' });

  const ref = db.collection('licenses').doc(keyId(key));
  try {
    const result = await db.runTransaction(async tx => {
      const snap = await tx.get(ref);
      if (!snap.exists) return { ok: false, message: 'License key not found.' };

      const d = snap.data();
      if (d.disabled === true) return { ok: false, message: 'License is disabled.' };

      const now = Timestamp.now();
      if (d.expiresAt && d.expiresAt.toMillis() <= now.toMillis())
        return { ok: false, message: 'License has expired.' };

      const devices = Array.isArray(d.devices) ? d.devices : [];
      const maxDevices = Math.max(1, Number(d.maxDevices || 1));
      if (!devices.includes(deviceId)) {
        if (action !== 'activate') return { ok: false, message: 'This PC is not activated.' };
        if (devices.length >= maxDevices) return { ok: false, message: 'This key is bound to another PC.' };
        devices.push(deviceId);
      }

      tx.update(ref, { devices, lastSeenAt: now, activationCount: FieldValue.increment(action === 'activate' ? 1 : 0) });
      return { ok: true, message: 'License valid.', plan: String(d.plan || 'PRO'), expiresAt: d.expiresAt ? d.expiresAt.toDate().toISOString() : null };
    });
    return reply(res, result.ok ? 200 : 403, result);
  } catch (err) {
    console.error(err);
    return reply(res, 500, { ok: false, message: 'Server error.' });
  }
}

exports.licenseApi = onRequest({ region: 'europe-west1', cors: false, secrets: [lootlabsApiToken, lootlabsPostbackSecret] }, async (req, res) => {
  try {
    const path = String(req.path || '/').replace(/\/+$/, '') || '/';
    if (req.method === 'GET' && path === '/start') return await startClaim(req, res);
    if (req.method === 'GET' && path === '/postback') return await postback(req, res);
    if (req.method === 'GET' && path === '/claim') return await claimPage(req, res);
    if (path === '/' || path === '/license') return await validateLicense(req, res);
    return reply(res, 404, { ok: false, message: 'Not found' });
  } catch (err) {
    console.error(err);
    return reply(res, 500, { ok: false, message: 'Server error.' });
  }
});
