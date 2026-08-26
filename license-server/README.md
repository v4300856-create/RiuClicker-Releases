# RiuClicker 1.1 key system

This is the production key backend used by RiuClicker 1.1.

## Flow

1. RiuClicker `GET KEY` opens `https://loot-link.com/s?zTsiS0pO` in the default browser.
2. Loot-Link must redirect to the deployed `issueKey` function after completion.
3. `issueKey` generates a fresh 24-hour key and shows it as text in the browser. It does **not** download RiuClicker.
4. The user pastes the key into RiuClicker.
5. RiuClicker calls `licenseApi` to activate/validate the key and bind it to one PC.

## Deploy

Install Firebase CLI, create/select a Firebase project with Firestore, then from this folder:

```bash
firebase login
firebase use YOUR_PROJECT_ID
cd functions
npm install
cd ..
firebase functions:secrets:set RIU_GATEWAY_TOKEN
firebase deploy --only functions,firestore:rules
```

After deployment, set the repository Actions variable `RIU_LICENSE_ENDPOINT` to:

`https://europe-west1-YOUR_PROJECT_ID.cloudfunctions.net/licenseApi`

`RIU_GET_KEY_URL` may be left empty because the client already defaults to:

`https://loot-link.com/s?zTsiS0pO`

## Loot-Link final destination

Set the final destination of the Loot-Link to:

`https://europe-west1-YOUR_PROJECT_ID.cloudfunctions.net/issueKey?gateway=YOUR_RIU_GATEWAY_TOKEN`

That final destination is what makes Loot-Link show a generated key instead of downloading the autoclicker.

Do not use the GitHub release `.exe` URL as the Loot-Link final destination.
