const { onRequest } = require('firebase-functions/v2/https');
const { initializeApp } = require('firebase-admin/app');
const { getFirestore, FieldValue, Timestamp } = require('firebase-admin/firestore');
const crypto = require('crypto');

initializeApp();
const db = getFirestore();

function normalizeKey(v) {
  return String(v || '').trim().toUpperCase().replace(/\s+/g, '');
}

function keyId(key) {
  return crypto.createHash('sha256').update(key).digest('hex');
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
        plan: String(d.plan || 'PRO'),
        expiresAt: d.expiresAt ? d.expiresAt.toDate().toISOString() : null
      };
    });

    return reply(res, result.ok ? 200 : 403, result);
  } catch (err) {
    console.error(err);
    return reply(res, 500, { ok: false, message: 'Server error.' });
  }
});
