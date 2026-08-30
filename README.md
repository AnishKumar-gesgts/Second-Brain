# Second Brain

Private Obsidian vault synchronized to GitHub.

## Vault Git

This repository contains an Obsidian plugin at:

`.obsidian/plugins/vault-auto-push/`

The plugin:

- detects desktop vs mobile Obsidian automatically;
- uses a compact mobile-friendly settings layout;
- queues vault changes for an explicitly requested push;
- provides explicit **Push now** and fast-forward **Pull now** controls;
- batches changed/deleted files into one GitHub commit;
- never force-updates the branch, so a remote change causes a safe failure rather than an overwrite;
- stores the GitHub token using Obsidian SecretStorage instead of plugin `data.json`.

## First-time setup

1. Get the vault onto the device and make sure these files exist locally under `.obsidian/plugins/vault-auto-push/`:
   - `manifest.json`
   - `main.js`
   - `styles.css`
2. In Obsidian, open **Settings → Community plugins** and enable **Vault Git**.
3. Open **Settings → Vault Git**.
4. Confirm:
   - Owner: `AnishKumar-gesgts`
   - Repository: `Second-Brain`
   - Branch: `main`
5. Create a fine-grained GitHub personal access token restricted to this repository with **Contents: Read and write** permission.
6. In the plugin's **GitHub token** field, create/select a SecretStorage entry containing that token.
7. Press **Push now** once and verify that the vault files appear in GitHub.

## iPhone / iPad behavior

The plugin does not invoke a shell Git executable. It talks directly to GitHub's Git Data API, which allows the same core synchronization logic to run on mobile.

All Git operations remain manual. Pending file changes persist until a successful push.

## Safety model

Push and pull are intentionally manual. Before each push the plugin reads the current remote branch head and updates the branch with `force: false`. Pull uses fast-forward-only Git and preserves local-only plugin settings.

Ignored paths include:

- `.obsidian/workspace.json`
- `.obsidian/workspace-mobile.json`
- `.obsidian/plugins/vault-auto-push/data.json`
- `.obsidian/plugins/codex-navigator/data.json`
- `.trash/`
- `.git/`
- `node_modules/`
- `.DS_Store`

Both plugins' `data.json` files are local-only. The Codex Workspace data contains chat history, tokens, and desktop-specific provider settings and is removed from Git tracking so a later pull cannot replace it. A manual push of the staged deletion is still required to remove the old copy from GitHub.

## Local Ollama models

Codex Workspace can use either Codex or Ollama for in-vault chats. Choose the provider in a chat tab or set the default in **Settings → Codex Workspace**. Set the local server (normally `http://127.0.0.1:11434`), enter an installed model, and use **Refresh** to load the models detected on this computer. Ollama requests stay on the desktop and are not sent to GitHub; local chat/configuration data is ignored by the vault Git plugin.
