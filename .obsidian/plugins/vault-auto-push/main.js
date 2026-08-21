const {
  Notice,
  Platform,
  Plugin,
  PluginSettingTab,
  SecretComponent,
  Setting,
  TFile,
  requestUrl,
} = require("obsidian");

const DEFAULT_SETTINGS = {
  owner: "AnishKumar-gesgts",
  repo: "Second-Brain",
  branch: "main",
  secretName: "",
  intervalMinutes: 5,
  autoPush: true,
  pushOnLoad: true,
  commitPrefix: "Obsidian auto-push",
  fileIndex: {},
};

const MAX_FILE_BYTES = 95 * 1024 * 1024;
const IGNORED_PATHS = new Set([
  ".DS_Store",
  ".obsidian/workspace.json",
  ".obsidian/workspace-mobile.json",
  ".obsidian/plugins/vault-auto-push/data.json",
  "Coding Output/Latex/basic-miktex-25.12-x64.exe",
  "Coding Output/Latex/strawberry-perl-5.42.0.1-64bit.msi",
]);
const IGNORED_PREFIXES = [".trash/", ".git/", "node_modules/"];

module.exports = class VaultAutoPushPlugin extends Plugin {
  async onload() {
    await this.loadSettings();

    this.changedPaths = new Set();
    this.deletedPaths = new Set();
    this.pushing = false;
    this.scanning = false;
    this.lastPush = null;
    this.lastError = null;
    this.lastSkipped = [];
    this.timerId = null;

    this.addSettingTab(new VaultAutoPushSettingTab(this.app, this));

    this.addCommand({
      id: "push-now",
      name: "Push vault to GitHub now",
      callback: () => void this.pushNow(true),
    });

    this.addRibbonIcon("upload-cloud", "Push vault to GitHub", () => void this.pushNow(true));

    // Vault events can include folders. Only queue real files for upload.
    this.registerEvent(this.app.vault.on("create", (file) => {
      if (file instanceof TFile) this.markChanged(file.path);
    }));
    this.registerEvent(this.app.vault.on("modify", (file) => {
      if (file instanceof TFile) this.markChanged(file.path);
    }));
    this.registerEvent(this.app.vault.on("delete", (file) => {
      if (file instanceof TFile) this.markDeleted(file.path);
      // Folder deletions are detected by the next metadata scan.
    }));
    this.registerEvent(this.app.vault.on("rename", (file, oldPath) => {
      if (file instanceof TFile) {
        this.markDeleted(oldPath);
        this.markChanged(file.path);
      }
      // Folder renames are detected by the next metadata scan.
    }));

    this.registerDomEvent(document, "visibilitychange", () => {
      if (
        document.visibilityState === "visible" &&
        this.settings.autoPush &&
        this.settings.pushOnLoad
      ) {
        void this.pushNow(false);
      }
    });

    this.configureTimer();

    this.app.workspace.onLayoutReady(async () => {
      try {
        // If upgrading from an older version, build a metadata baseline only.
        await this.scanForChanges(true);
        if (this.settings.pushOnLoad && this.settings.autoPush) {
          void this.pushNow(false);
        }
      } catch (error) {
        this.recordError(error);
      }
    });
  }

  onunload() {
    if (this.timerId !== null) window.clearInterval(this.timerId);
  }

  async loadSettings() {
    const saved = await this.loadData();
    this.settings = Object.assign({}, DEFAULT_SETTINGS, saved || {});
    if (!this.settings.fileIndex || typeof this.settings.fileIndex !== "object") {
      this.settings.fileIndex = {};
    }
  }

  async saveSettings() {
    await this.saveData(this.settings);
    this.configureTimer();
  }

  async saveStateOnly() {
    await this.saveData(this.settings);
  }

  configureTimer() {
    if (this.timerId !== null) window.clearInterval(this.timerId);
    this.timerId = null;
    if (!this.settings.autoPush) return;

    const minutes = Math.max(1, Number(this.settings.intervalMinutes) || 5);
    this.timerId = window.setInterval(() => void this.pushNow(false), minutes * 60_000);
    this.registerInterval(this.timerId);
  }

  shouldIgnore(path) {
    if (!path) return true;
    if (IGNORED_PATHS.has(path)) return true;
    if (path.split("/").includes(".git-backup")) return true;
    return IGNORED_PREFIXES.some((prefix) => path.startsWith(prefix));
  }

  markChanged(path) {
    if (this.shouldIgnore(path)) return;
    this.deletedPaths.delete(path);
    this.changedPaths.add(path);
  }

  markDeleted(path) {
    if (this.shouldIgnore(path)) return;
    this.changedPaths.delete(path);
    this.deletedPaths.add(path);
  }

  getToken() {
    if (!this.settings.secretName) return null;
    return this.app.secretStorage.getSecret(this.settings.secretName);
  }

  async github(path, method = "GET", body = undefined) {
    const token = this.getToken();
    if (!token) throw new Error("No GitHub token selected in Vault Auto Push settings.");

    const response = await requestUrl({
      url: `https://api.github.com/repos/${encodeURIComponent(this.settings.owner)}/${encodeURIComponent(this.settings.repo)}${path}`,
      method,
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${token}`,
        "X-GitHub-Api-Version": "2022-11-28",
      },
      contentType: "application/json",
      body: body === undefined ? undefined : JSON.stringify(body),
      throw: false,
    });

    if (response.status < 200 || response.status >= 300) {
      const message = response.json?.message || response.text || `HTTP ${response.status}`;
      throw new Error(`GitHub API ${response.status}: ${message}`);
    }
    return response.json;
  }

  async collectLocalMetadata() {
    const result = {};

    const walk = async (folder) => {
      const listing = await this.app.vault.adapter.list(folder);

      for (const path of listing.files) {
        if (this.shouldIgnore(path)) continue;
        const stat = await this.app.vault.adapter.stat(path);
        // Defensive check: some adapters can surface unusual entries.
        if (!stat || stat.type === "folder") continue;
        result[path] = {
          mtime: Number(stat.mtime) || 0,
          size: Number(stat.size) || 0,
        };
      }

      for (const child of listing.folders) {
        if (this.shouldIgnore(`${child}/placeholder`)) continue;
        await walk(child);
      }
    };

    await walk("");
    return result;
  }

  async scanForChanges(baselineIfEmpty = false) {
    if (this.scanning) return;
    this.scanning = true;

    try {
      const current = await this.collectLocalMetadata();
      const previous = this.settings.fileIndex || {};
      const previousPaths = Object.keys(previous);

      if (baselineIfEmpty && previousPaths.length === 0) {
        this.settings.fileIndex = current;
        await this.saveStateOnly();
        return;
      }

      for (const [path, meta] of Object.entries(current)) {
        const old = previous[path];
        if (!old || old.mtime !== meta.mtime || old.size !== meta.size) {
          this.markChanged(path);
        }
      }

      for (const path of previousPaths) {
        if (!(path in current)) this.markDeleted(path);
      }
    } finally {
      this.scanning = false;
    }
  }

  async createBlob(path) {
    const stat = await this.app.vault.adapter.stat(path);

    // Never attempt readBinary() on a directory.
    if (!stat || stat.type === "folder") {
      this.changedPaths.delete(path);
      return null;
    }

    if ((Number(stat.size) || 0) > MAX_FILE_BYTES) {
      this.lastSkipped.push(path);
      this.changedPaths.delete(path);
      return null;
    }

    const data = await this.app.vault.adapter.readBinary(path);
    return await this.github("/git/blobs", "POST", {
      content: arrayBufferToBase64(data),
      encoding: "base64",
    });
  }

  async updateIndex(uploaded, deleted, skipped) {
    const index = this.settings.fileIndex || {};

    for (const path of uploaded) {
      const stat = await this.app.vault.adapter.stat(path);
      if (stat && stat.type !== "folder") {
        index[path] = {
          mtime: Number(stat.mtime) || 0,
          size: Number(stat.size) || 0,
        };
      }
    }

    // Record skipped large files too so they are not retried every five minutes.
    for (const path of skipped) {
      const stat = await this.app.vault.adapter.stat(path);
      if (stat && stat.type !== "folder") {
        index[path] = {
          mtime: Number(stat.mtime) || 0,
          size: Number(stat.size) || 0,
        };
      }
    }

    for (const path of deleted) delete index[path];
    this.settings.fileIndex = index;
    await this.saveStateOnly();
  }

  async pushNow(showNotice) {
    if (this.pushing) {
      if (showNotice) new Notice("Vault Auto Push: a push is already running.");
      return;
    }

    if (!this.settings.owner || !this.settings.repo || !this.settings.branch) {
      if (showNotice) new Notice("Vault Auto Push: configure the repository first.");
      return;
    }

    this.pushing = true;
    this.lastError = null;
    this.lastSkipped = [];

    try {
      await this.scanForChanges(false);

      const pathsToUpload = [...this.changedPaths].filter((p) => !this.shouldIgnore(p));
      const pathsToDelete = [...this.deletedPaths].filter((p) => !this.shouldIgnore(p));

      if (pathsToUpload.length === 0 && pathsToDelete.length === 0) {
        this.lastPush = new Date();
        if (showNotice) new Notice("Vault Auto Push: nothing changed.");
        return;
      }

      const head = await this.github(`/git/ref/heads/${encodeURIComponent(this.settings.branch)}`);
      const headSha = head.object.sha;
      const baseCommit = await this.github(`/git/commits/${headSha}`);
      const baseTreeSha = baseCommit.tree.sha;

      const tree = [];
      const uploaded = [];

      for (const path of pathsToUpload) {
        if (!(await this.app.vault.adapter.exists(path))) continue;
        const blob = await this.createBlob(path);
        if (!blob) continue;
        tree.push({ path, mode: "100644", type: "blob", sha: blob.sha });
        uploaded.push(path);
      }

      for (const path of pathsToDelete) {
        tree.push({ path, mode: "100644", type: "blob", sha: null });
      }

      if (tree.length > 0) {
        const newTree = await this.github("/git/trees", "POST", {
          base_tree: baseTreeSha,
          tree,
        });

        if (newTree.sha !== baseTreeSha) {
          const stamp = new Date().toISOString();
          const commit = await this.github("/git/commits", "POST", {
            message: `${this.settings.commitPrefix} ${stamp}`,
            tree: newTree.sha,
            parents: [headSha],
          });

          // Never force; fail rather than overwrite another device's newer commit.
          await this.github(`/git/refs/heads/${encodeURIComponent(this.settings.branch)}`, "PATCH", {
            sha: commit.sha,
            force: false,
          });
        }
      }

      for (const path of uploaded) this.changedPaths.delete(path);
      for (const path of pathsToDelete) this.deletedPaths.delete(path);
      await this.updateIndex(uploaded, pathsToDelete, this.lastSkipped);

      this.lastPush = new Date();
      if (showNotice) {
        if (tree.length === 0 && this.lastSkipped.length) {
          new Notice(`Vault Auto Push: no upload needed; skipped ${this.lastSkipped.length} oversized file(s).`);
        } else {
          const suffix = this.lastSkipped.length
            ? ` Skipped ${this.lastSkipped.length} oversized file(s).`
            : "";
          new Notice(`Vault Auto Push: pushed successfully.${suffix}`);
        }
      }
    } catch (error) {
      this.recordError(error);
      if (showNotice) new Notice(`Vault Auto Push failed: ${this.lastError}`);
    } finally {
      this.pushing = false;
    }
  }

  recordError(error) {
    this.lastError = error instanceof Error ? error.message : String(error);
    console.error("Vault Auto Push", error);
  }
};

class VaultAutoPushSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.toggleClass("vault-auto-push-mobile", Platform.isMobile);

    containerEl.createEl("h2", { text: "Vault Auto Push" });

    const status = containerEl.createDiv({ cls: "vault-auto-push-status" });
    status.createEl("strong", { text: Platform.isMobile ? "Mobile mode" : "Desktop mode" });
    status.createEl("div", {
      text: Platform.isIosApp
        ? "iOS detected. Scheduled pushes run while Obsidian is active; iOS may suspend background timers."
        : Platform.isMobile
          ? "Mobile Obsidian detected."
          : "Desktop Obsidian detected.",
    });
    status.createEl("div", { text: `Repository: ${this.plugin.settings.owner}/${this.plugin.settings.repo}` });
    status.createEl("div", {
      text: this.plugin.pushing
        ? "Status: pushing…"
        : this.plugin.lastPush
          ? `Last check: ${this.plugin.lastPush.toLocaleString()}`
          : "Last check: not yet",
    });
    if (this.plugin.lastSkipped.length) {
      status.createEl("div", { text: `Skipped oversized files: ${this.plugin.lastSkipped.length}` });
    }
    if (this.plugin.lastError) {
      status.createEl("div", { cls: "vault-auto-push-error", text: this.plugin.lastError });
    }

    new Setting(containerEl)
      .setName("Push now")
      .setDesc("Scan metadata and push only files that changed.")
      .addButton((button) => button.setButtonText("Push now").setCta().onClick(async () => {
        await this.plugin.pushNow(true);
        this.display();
      }));

    new Setting(containerEl)
      .setName("GitHub owner")
      .addText((text) => text.setValue(this.plugin.settings.owner).onChange(async (value) => {
        this.plugin.settings.owner = value.trim();
        await this.plugin.saveSettings();
      }));

    new Setting(containerEl)
      .setName("Repository")
      .addText((text) => text.setValue(this.plugin.settings.repo).onChange(async (value) => {
        this.plugin.settings.repo = value.trim();
        await this.plugin.saveSettings();
      }));

    new Setting(containerEl)
      .setName("Branch")
      .addText((text) => text.setValue(this.plugin.settings.branch).onChange(async (value) => {
        this.plugin.settings.branch = value.trim() || "main";
        await this.plugin.saveSettings();
      }));

    new Setting(containerEl)
      .setName("GitHub token")
      .setDesc("SecretStorage entry containing the fine-grained GitHub PAT.")
      .addComponent((el) => new SecretComponent(this.app, el)
        .setValue(this.plugin.settings.secretName)
        .onChange(async (value) => {
          this.plugin.settings.secretName = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName("Automatic push")
      .setDesc("Push changed files on a repeating timer while Obsidian is running.")
      .addToggle((toggle) => toggle.setValue(this.plugin.settings.autoPush).onChange(async (value) => {
        this.plugin.settings.autoPush = value;
        await this.plugin.saveSettings();
      }));

    new Setting(containerEl)
      .setName("Interval")
      .setDesc("Minutes between automatic push attempts.")
      .addText((text) => text
        .setPlaceholder("5")
        .setValue(String(this.plugin.settings.intervalMinutes))
        .onChange(async (value) => {
          const parsed = Number(value);
          if (Number.isFinite(parsed) && parsed >= 1) {
            this.plugin.settings.intervalMinutes = parsed;
            await this.plugin.saveSettings();
          }
        }));

    new Setting(containerEl)
      .setName("Push on app load/resume")
      .setDesc("Runs a metadata scan on startup/resume; file bodies are read only when changed.")
      .addToggle((toggle) => toggle.setValue(this.plugin.settings.pushOnLoad).onChange(async (value) => {
        this.plugin.settings.pushOnLoad = value;
        await this.plugin.saveSettings();
      }));
  }
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  let binary = "";
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, Math.min(i + chunkSize, bytes.length)));
  }
  return btoa(binary);
}
