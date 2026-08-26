const { onRequest } = require('firebase-functions/v2/https');
const { defineSecret } = require('firebase-functions/params');
const { initializeApp } = require('firebase-admin/app');
const { getFirestore, FieldValue, Timestamp } = require('firebase-admin/firestore');
const crypto = require('crypto');

initializeApp();
const db = getFirestore();
const lootlabsApiToken = defineSecret('LOOTLABS_API_TOKEN');

const LOOT_LINK = 'https://loot-link.com/s?zTsiS0pO';
const CLAIM_TTL_MS = 20 * 60 * 1000;
const LICENSE_TTL_MS = 24 * 60 * 60 * 1000;

function normalizeKey(v) {
  return String(v || '').trim().toUpperCase().replace(/\s+/g, '');
}

function keyId(key) {
  return crypto.createHash('sha256').update(key).digest('hex');
}

function makeKey() {
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

function escapeHtml(v) {
  return String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function page(body) {
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RiuClicker Key</title><style>
  :root{color-scheme:dark}body{margin:0;background:#080b12;color:#f7f7ff;font-family:Segoe UI,Arial,sans-serif;display:grid;place-items:center;min-height:100vh}.card{width:min(560px,calc(100vw - 40px));background:#111421;border:1px solid #31364b;border-radius:20px;padding:28px;box-shadow:0 20px 60px #0008}.brand{font-size:12px;font-weight:800;letter-spacing:.14em;color:#8b5cf6}.title{font-size:28px;font-weight:800;margin:10px 0 8px}.muted{color:#949aaf;line-height:1.55}.key{margin:22px 0;padding:16px;border-radius:12px;background:#0d101b;border:1px solid #8b5cf6;font:700 20px Consolas,monospace;word-break:break-all;user-select:all}.btn{width:100%;height:44px;border:0;border-radius:11px;background:#7c3aed;color:white;font-weight:800;cursor:pointer}.ok{color:#4ade80;margin-top:14px}</style></head><body><div class="card"><div class="brand">RIUCLICKER 1.1</div>${body}</div></body></html>`;
}

async function startKeyFlow(req, res) {
  const deviceId = String(req.query.deviceId || '').trim();
  if (deviceId.length < 12) return res.status(400).send(page('<div class="title">Invalid device</div><div class="muted">Open GET KEY from inside RiuClicker.</div>'));

  const claimId = crypto.randomBytes(20).toString('hex');
  const now = Timestamp.now();
  const claimExpiresAt = Timestamp.fromMillis(Date.now() + CLAIM_TTL_MS);
  await db.collection('claims').doc(claimId).set({
    deviceId,
    createdAt: now,
    expiresAt: claimExpiresAt,
    issued: false
  });

  const token = lootlabsApiToken.value();
  if (!token) return res.status(503).send(page('<div class="title">Key server is not configured</div><div class="muted">LOOTLABS_API_TOKEN is missing on the server.</div>'));

  const destination = `${baseUrl(req)}/claim?claimId=${encodeURIComponent(claimId)}`;

  try {
    const apiRes = await fetch('https://creators.lootlabs.gg/api/public/url_encryptor', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ destination_url: destination, api_token: token })
    });
    const data = await apiRes.json();
    if (!apiRes.ok || !data || typeof data.message !== 'string' || !data.message)
      throw new Error('LootLabs redirect encryption failed');

    // The encrypted &data destination overrides the old Loot-Link destination.
    // This prevents the completed flow from downloading RiuClicker again.
    return res.redirect(302, `${LOOT_LINK}&puid=${encodeURIComponent(claimId)}&data=${data.message}`);
  } catch (err) {
    console.error(err);
    return res.status(502).send(page('<div class="title">Could not start key flow</div><div class="muted">LootLabs API did not respond. Try again in a moment.</div>'));
  }
}

async function claimKey(req, res) {
  const claimId = String(req.query.claimId || '').trim();
  if (!claimId) return res.status(400).send(page('<div class="title">Missing key session</div>'));

  const claimRef = db.collection('claims').doc(claimId);
  const result = await db.runTransaction(async tx => {
    const snap = await tx.get(claimRef);
    if (!snap.exists) return { state: 'missing' };
    const d = snap.data();
    if (d.expiresAt && d.expiresAt.toMillis() <= Date.now()) return { state: 'expired' };
    if (d.issuedKey) return { state: 'issued', key: d.issuedKey, expiresAt: d.licenseExpiresAt?.toDate?.()?.toISOString?.() || null };

    const key = makeKey();
    const expiresAt = Timestamp.fromMillis(Date.now() + LICENSE_TTL_MS);
    tx.set(db.collection('licenses').doc(keyId(key)), {
      plan: 'LOOTLINK-24H',
      disabled: false,
      devices: [String(d.deviceId || '')],
      maxDevices: 1,
      createdAt: Timestamp.now(),
      activatedAt: Timestamp.now(),
      expiresAt,
      activationCount: 0,
      source: 'lootlabs-encrypted-redirect'
    });
    tx.update(claimRef, {
      issued: true,
      issuedKey: key,
      issuedAt: Timestamp.now(),
      licenseExpiresAt: expiresAt
    });
    return { state: 'issued', key, expiresAt: expiresAt.toDate().toISOString() };
  });

  if (result.state === 'missing') return res.status(404).send(page('<div class="title">Unknown key session</div><div class="muted">Return to RiuClicker and press GET KEY again.</div>'));
  if (result.state === 'expired') return res.status(410).send(page('<div class="title">Key session expired</div><div class="muted">Return to RiuClicker and press GET KEY again.</div>'));

  const key = escapeHtml(result.key);
  return res.status(200).send(page(`<div class="title">Your key is ready</div><div class="muted">Copy it into RiuClicker. This key is valid for 24 hours and is already bound to the PC that started GET KEY.</div><div id="key" class="key">${key}</div><button class="btn" onclick="navigator.clipboard.writeText(document.getElementById('key').innerText);this.innerText='COPIED'">COPY KEY</button><div class="ok">KEY GENERATED SUCCESSFULLY</div>`));
}

async function licenseRequest(req, res) {
  if (req.method !== 'POST') return reply(res, 405, { ok: false, message: 'POST required' });

  const action = String(req.body?.action || '');
  const key = normalizeKey(req.body?.key);
  const deviceId = String(req.body?.deviceId || '').trim();
  const app = String(req.body?.app || '');

  if (app !== 'RiuClicker' || !['activate', 'validate'].includes(action) || !key || key.length < 12 || deviceId.length < 12)
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

      tx.update(ref, {
        devices,
        lastSeenAt: now,
        activationCount: FieldValue.increment(action === 'activate' ? 1 : 0)
      });

      return {
        ok: true,
        message: 'License valid.',
        plan: String(d.plan || 'LOOTLINK-24H'),
        expiresAt: d.expiresAt ? d.expiresAt.toDate().toISOString() : null
      };
    });
    return reply(res, result.ok ? 200 : 403, result);
  } catch (err) {
    console.error(err);
    return reply(res, 500, { ok: false, message: 'Server error.' });
  }
}

exports.licenseApi = onRequest({ region: 'europe-west1', cors: false, secrets: [lootlabsApiToken] }, async (req, res) => {
  try {
    const path = String(req.path || '/').replace(/\/+$/, '') || '/';
    if (req.method === 'GET' && path === '/start') return await startKeyFlow(req, res);
    if (req.method === 'GET' && path === '/claim') return await claimKey(req, res);
    if (path === '/' || path === '/license') return await licenseRequest(req, res);
    return reply(res, 404, { ok: false, message: 'Not found' });
  } catch (err) {
    console.error(err);
    return reply(res, 500, { ok: false, message: 'Server error.' });
  }
});
