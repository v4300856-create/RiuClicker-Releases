rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /licenses/{licenseId} {
      allow read, write: if false;
    }
  }
}
