# Rune Mommy

Top-down **pixel** multiplayer. Project Zomboid camera and weight, GTA-lite street heat, visual-novel talk. Lightweight. Browser only.

Not 3D. Not a Jagex clone. Shake shops in `data/shops.json` stay.

## Windows 11

1. Install [Node.js 18+ LTS](https://nodejs.org) with the Windows `.msi`. Leave **Add to PATH** checked.
2. Close Terminal, open a new **PowerShell** or **Command Prompt**.
3. Go to the repo folder:

```powershell
cd $HOME\Downloads\Rune_mommy
```

(or wherever you cloned it)

4. Install and run:

```powershell
npm install
npm start
```

5. Open [http://localhost:8080](http://localhost:8080) in two Edge or Chrome windows. Pick two names. You should see each other walk.

If `npm` is not recognized, Node is not on PATH. Reinstall Node, then open a **new** Terminal. Do not use Git Bash unless you know it.

Two-window check: walk, type chat, click an NPC, click the other player and Trade.

## Controls

- Left-click ground: walk
- Left-click person/NPC: talk, attack, or trade
- Chat box + Enter. Whisper: `/w Name hi`
- I inventory, T trade

## Editing (bots)

Push every save to `main` so we do not merge-conflict. Huge code lives in this repo, not chat.
