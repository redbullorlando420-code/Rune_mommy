# Rune Mommy

Top-down pixel multiplayer (Project Zomboid camera). Chat, trade, combat, gathering. Lightweight. Browser only.

## Windows 11

1. Install Node.js 18+ LTS from https://nodejs.org (Windows .msi, add to PATH).
2. Open a **new** PowerShell.
3. `cd` into this folder, then:

```powershell
npm install
npm start
```

4. Open http://localhost:8080 in two Edge or Chrome windows. Pick two names.

If `npm` is not recognized, reopen Terminal after installing Node.

Left-click ground to walk. Click people to talk, fight, or trade. Chat at the bottom.

`data/shops.json` is the ten Clermont shake shops. Do not empty it.

The server serves `client/index.html` at `/` and aliases `/game.js` to `client/js/main.js`.
