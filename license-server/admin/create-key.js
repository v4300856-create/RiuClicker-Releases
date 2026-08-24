const { initializeApp, applicationDefault } = require('firebase-admin/app');
const { getFirestore, Timestamp } = require('firebase-admin/firestore');
const crypto = require('crypto');

initializeApp({ credential: applicationDefault() });
const db = getFirestore();

function part(n = 4) {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let out = '';
  const bytes = crypto.randomBytes(n);
  for (let i = 0; i < n; i++) out += alphabet[bytes[i] % alphabet.length];
  return out;
}
function makeKey() { return `RIU-${part()}-${part()}-${part()}`; }
function id(key) { return crypto.createHash('sha256').update(key).digest('hex'); }

(async () => {
  const plan = String(process.argv[2] || 'LIFETIME').toUpperCase();
  const days = Number(process.argv[3] || 0);
  const maxDevices = Math.max(1, Number(process.argv[4] || 1));
  const key = makeKey();
  const now = new Date();
  const expiresAt = days > 0 ? Timestamp.fromDate(new Date(now.getTime() + days * 86400000)) : null;

  await db.collection('licenses').doc(id(key)).set({
    plan,
    createdAt: Timestamp.now(),
    expiresAt,
    maxDevices,
    devices: [],
    disabled: false,
    activationCount: 0
  });

  console.log(key);
  console.log(`plan=${plan} days=${days || 'lifetime'} maxDevices=${maxDevices}`);
})().catch(err => { console.error(err); process.exit(1); });
