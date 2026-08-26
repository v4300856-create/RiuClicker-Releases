# RiuClicker 1.1 key system

This backend makes `GET KEY` behave like a real key system instead of downloading RiuClicker again.

## User flow

1. RiuClicker calls the deployed `licenseApi/start?deviceId=...` endpoint.
2. The server creates a short-lived claim for that PC.
3. The server uses the LootLabs Redirect API to encrypt a one-time claim page URL.
4. The browser is redirected to:
   `https://loot-link.com/s?zTsiS0pO&puid=...&data=...`
5. After the LootLabs tasks are completed, the encrypted destination overrides the old download destination.
6. The final page generates a fresh 24-hour key, binds it to the PC that started the flow, and shows a `COPY KEY` button.
7. The user pastes the key into RiuClicker and `licenseApi` validates it online.

The client never downloads or reinstalls RiuClicker from `GET KEY`.

## Required Firebase setup

Create/select a Firebase project with Firestore enabled. From `license-server`:

```bash
firebase login
firebase use YOUR_PROJECT_ID
cd functions
npm install
cd ..
firebase functions:secrets:set LOOTLABS_API_TOKEN
firebase deploy --only functions,firestore:rules
```

`LOOTLABS_API_TOKEN` must be the API token from the same LootLabs creator account that owns the link `https://loot-link.com/s?zTsiS0pO`. The Redirect API only works with links created using that account/token.

After deploy, set the GitHub Actions repository variable `RIU_LICENSE_ENDPOINT` to:

`https://europe-west1-YOUR_PROJECT_ID.cloudfunctions.net/licenseApi`

Then re-run **Publish RiuClicker 1.1**.

## Loot-Link destination

You do **not** need to change the old destination manually for the RiuClicker flow. The server adds an encrypted `&data=` destination for each key session, which overrides the original destination after completion.

Do not put the LootLabs API token inside the client or the public repository.
