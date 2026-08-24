const { initializeApp, applicationDefault } = require('firebase-admin/app');
const { getFirestore, Timestamp } = require('firebase-admin/firestore');
const crypto = require('crypto');

initializeApp({ credential: applicationDefault() });
const db = getFirestore();
const norm = k => String(k || '').trim().toUpperCase().replace(/\s+/g, '');
const id = k => crypto.createHash('sha256').update(norm(k)).digest('hex');

(async () => {
  const key = norm(process.argv[2]);
  const action = String(process.argv[3] || '').toLowerCase();
  const value = process.argv[4];
  if (!key || !action) throw new Error('Usage: node manage-key.js KEY <disable|enable|reset|extend> [days]');

  const ref = db.collection('licenses').doc(id(key));
  const snap = await ref.get();
  if (!snap.exists) throw new Error('Key not found');

  if (action === 'disable') await ref.update({ disabled: true });
  else if (action === 'enable') await ref.update({ disabled: false });
  else if (action === 'reset') await ref.update({ devices: [] });
  else if (action === 'extend') {
    const days = Math.max(1, Number(value || 30));
    const d = snap.data();
    const base = d.expiresAt && d.expiresAt.toMillis() > Date.now() ? d.expiresAt.toMillis() : Date.now();
    await ref.update({ expiresAt: Timestamp.fromMillis(base + days * 86400000) });
  } else throw new Error('Unknown action');

  console.log(`OK: ${action}`);
})().catch(err => { console.error(err.message || err); process.exit(1); });
