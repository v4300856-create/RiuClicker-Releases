const { onRequest } = require('firebase-functions/v2/https');
const { defineSecret } = require('firebase-functions/params');
const { initializeApp } = require('firebase-admin/app');
const { getFirestore, FieldValue, Timestamp } = require('firebase-admin/firestore');
const crypto = require('crypto');

initializeApp();
const db = getFirestore();
const gatewayToken = defineSecret('RIU_GATEWAY_TOKEN');

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

exports.licenseApi = onRequest({ region: 'europe-west1', cors: false }, async (req, res) => {
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
        if (devices.length >= maxDevices) return { ok: false, message: 'Device limit reached.' };
        devices.push(deviceId);
        tx.update(ref, {
          devices,
          activatedAt: d.activatedAt || now,
          lastSeenAt: now,
          activationCount: FieldValue.increment(1)
        });
      } else {
        tx.update(ref, { lastSeenAt: now });
      }

      return {
        ok: true,
        message: 'License valid.',
        plan: String(d.plan || 'FREE-KEY'),
        expiresAt: d.expiresAt ? d.expiresAt.toDate().toISOString() : null
      };
    });

    return reply(res, result.ok ? 200 : 403, result);
  } catch (err) {
    console.error(err);
    return reply(res, 500, { ok: false, message: 'Server error.' });
  }
});

// Set the Loot-Link final destination to:
// https://europe-west1-YOUR_PROJECT.cloudfunctions.net/issueKey?gateway=YOUR_SECRET
// This endpoint generates a fresh 24-hour, one-device key and displays it instead of downloading the clicker.
exports.issueKey = onRequest({ region: 'europe-west1', cors: false, secrets: [gatewayToken] }, async (req, res) => {
  if (req.method !== 'GET') return res.status(405).send('GET required');

  const supplied = String(req.query.gateway || '');
  if (!supplied || supplied !== gatewayToken.value()) return res.status(403).send('Invalid gateway');

  const key = makeKey();
  const now = Timestamp.now();
  const expiresAt = Timestamp.fromMillis(now.toMillis() + 24 * 60 * 60 * 1000);

  await db.collection('licenses').doc(keyId(key)).set({
    plan: 'LOOT-LINK-24H',
    disabled: false,
    devices: [],
    maxDevices: 1,
    createdAt: now,
    expiresAt,
    activationCount: 0,
    source: 'loot-link'
  });

  res.set('Cache-Control', 'no-store');
  res.status(200).send(`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RiuClicker Key</title><style>body{margin:0;background:#080b12;color:#f7f7ff;font-family:Segoe UI,Arial,sans-serif;display:grid;place-items:center;min-height:100vh}.card{width:min(560px,90vw);background:#111421;border:1px solid #31364b;border-radius:20px;padding:28px;box-shadow:0 20px 60px #0008}h1{margin:0 0 8px;font-size:28px}.muted{color:#949aaf}.key{margin:22px 0;padding:16px;border-radius:12px;background:#0d101b;border:1px solid #8b5cf6;font:700 20px Consolas,monospace;word-break:break-all;user-select:all}.ok{color:#4ade80}</style></head><body><div class="card"><div class="muted">RIUCLICKER 1.1</div><h1>Your key is ready</h1><p class="muted">Copy this key into RiuClicker. It expires in 24 hours and activates on one PC.</p><div class="key">${key}</div><div class="ok">Key generated successfully.</div></div></body></html>`);
});
