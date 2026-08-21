# Second Brain

Private Obsidian vault synchronized to GitHub.

## Vault Auto Push

This repository contains an Obsidian plugin at:

`.obsidian/plugins/vault-auto-push/`

The plugin:

- detects desktop vs mobile Obsidian automatically;
- uses a compact mobile-friendly settings layout;
- snapshots vault changes to this private GitHub repository;
- attempts automatic pushes every 5 minutes while Obsidian is running;
- performs a push check when Obsidian loads or resumes;
- batches changed/deleted files into one GitHub commit;
- never force-updates the branch, so a remote change causes a safe failure rather than an overwrite;
- stores the GitHub token using Obsidian SecretStorage instead of plugin `data.json`.

## First-time setup

1. Get the vault onto the device and make sure these files exist locally under `.obsidian/plugins/vault-auto-push/`:
   - `manifest.json`
   - `main.js`
   - `styles.css`
2. In Obsidian, open **Settings → Community plugins** and enable **Vault Auto Push**.
3. Open **Settings → Vault Auto Push**.
4. Confirm:
   - Owner: `AnishKumar-gesgts`
   - Repository: `Second-Brain`
   - Branch: `main`
   - Interval: `5`
5. Create a fine-grained GitHub personal access token restricted to this repository with **Contents: Read and write** permission.
6. In the plugin's **GitHub token** field, create/select a SecretStorage entry containing that token.
7. Press **Push now** once and verify that the vault files appear in GitHub.

## iPhone / iPad behavior

The plugin does not invoke a shell Git executable. It talks directly to GitHub's Git Data API, which allows the same core synchronization logic to run on mobile.

However, iOS may suspend Obsidian after it goes into the background. Therefore the 5-minute timer is only reliable while Obsidian is active. The plugin also performs a push check when the app becomes active again.

## Safety model

This version is intentionally push-first. It does **not** pull or merge remote changes. Before each push it reads the current remote branch head and updates the branch with `force: false`. If another device has changed the branch, GitHub should reject a non-fast-forward update instead of allowing the plugin to erase the remote change.

Ignored paths include:

- `.obsidian/workspace.json`
- `.obsidian/workspace-mobile.json`
- `.obsidian/plugins/vault-auto-push/data.json`
- `.trash/`
- `.git/`
- `node_modules/`
- `.DS_Store`

The plugin's own `data.json` is excluded so status/config writes do not continuously trigger new backup commits.
