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

const QUEUE_SCHEMA_VERSION = 2;
const STARTUP_ARM_DELAY_MS = 2000;

const DEFAULT_SETTINGS = {
  owner: "AnishKumar-gesgts",
  repo: "Second-Brain",
  branch: "main",
  secretName: "",
  intervalMinutes: 5,
  autoPush: true,
  pushOnLoad: true,
  commitPrefix: "Obsidian auto-push",
  pendingChanged: [],
  pendingDeleted: [],
  queueSchemaVersion: 0,
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
const IGNORED_COMPONENTS = new Set([".git", ".git-backup", "node_modules", ".trash"]);

module.exports = class VaultAutoPushPlugin extends Plugin {
  async onload() {
    await this.loadSettings();

    this.changedPaths = new Set(this.settings.pendingChanged || []);
    this.deletedPaths = new Set(this.settings.pendingDeleted || []);
    this.pushing = false;
    this.trackingEnabled = false;
    this.lastPush = null;
    this.lastError = null;
    this.lastSkipped = [];
    this.timerId = null;
    this.persistTimer = null;
    this.armTimer = null;

    this.addSettingTab(new VaultAutoPushSettingTab(this.app, this));

    this.addCommand({
      id: "push-now",
      name: "Push vault to GitHub now",
      callback: () => void this.pushNow(true),
    });

    this.addRibbonIcon("upload-cloud", "Push vault to GitHub", () => void this.pushNow(true));

    // Obsidian can emit create/modify events for many existing files while the
    // vault is starting. Ignore all file events until startup has settled.
    this.registerEvent(this.app.vault.on("create", (file) => {
      if (this.trackingEnabled && file instanceof TFile) this.markChanged(file.path);
    }));
    this.registerEvent(this.app.vault.on("modify", (file) => {
      if (this.trackingEnabled && file instanceof TFile) this.markChanged(file.path);
    }));
    this.registerEvent(this.app.vault.on("delete", (file) => {
      if (this.trackingEnabled && file instanceof TFile) this.markDeleted(file.path);
    }));
    this.registerEvent(this.app.vault.on("rename", (file, oldPath) => {
      if (this.trackingEnabled && file instanceof TFile) {
        this.markDeleted(oldPath);
        this.markChanged(file.path);
      }
    }));

    this.registerDomEvent(document, "visibilitychange", () => {
      if (
        document.visibilityState === "visible" &&
        this.trackingEnabled &&
        this.settings.autoPush &&
        this.settings.pushOnLoad &&
        (this.changedPaths.size || this.deletedPaths.size)
      ) {
        void this.pushNow(false);
      }
    });

    this.configureTimer();

    this.app.workspace.onLayoutReady(() => {
      // Give Obsidian a short grace period to finish its startup event burst.
      this.armTimer = window.setTimeout(async () => {
        this.armTimer = null;
        this.trackingEnabled = true;
        await this.persistQueue();

        if (
          this.settings.pushOnLoad &&
          this.settings.autoPush &&
          (this.changedPaths.size || this.deletedPaths.size)
        ) {
          void this.pushNow(false);
        }
      }, STARTUP_ARM_DELAY_MS);
    });
  }

  onunload() {
    if (this.timerId !== null) window.clearInterval(this.timerId);
    if (this.persistTimer !== null) window.clearTimeout(this.persistTimer);
    if (this.armTimer !== null) window.clearTimeout(this.armTimer);
    void this.persistQueue();
  }

  async loadSettings() {
    const saved = await this.loadData();
    this.settings = Object.assign({}, DEFAULT_SETTINGS, saved || {});

    // Schema 2 intentionally clears queues created by the old startup scanner
    // and by startup create-event storms. After this one-time reset, only real
    // post-startup edits are queued and persisted.
    if ((Number(this.settings.queueSchemaVersion) || 0) < QUEUE_SCHEMA_VERSION) {
      this.settings.pendingChanged = [];
      this.settings.pendingDeleted = [];
      delete this.settings.fileIndex;
      this.settings.queueSchemaVersion = QUEUE_SCHEMA_VERSION;
      await this.saveData(this.settings);
    }

    if (!Array.isArray(this.settings.pendingChanged)) this.settings.pendingChanged = [];
    if (!Array.isArray(this.settings.pendingDeleted)) this.settings.pendingDeleted = [];
  }

  async saveSettings() {
    await this.persistQueue();
    this.configureTimer();
  }

  configureTimer() {
    if (this.timerId !== null) window.clearInterval(this.timerId);
    this.timerId = null;
    if (!this.settings.autoPush) return;

    const minutes = Math.max(1, Number(this.settings.intervalMinutes) || 5);
    this.timerId = window.setInterval(() => {
      if (
        this.trackingEnabled &&
        !this.pushing &&
        (this.changedPaths.size || this.deletedPaths.size)
      ) {
        void this.pushNow(false);
      }
    }, minutes * 60_000);
    this.registerInterval(this.timerId);
  }

  shouldIgnore(path) {
    if (!path) return true;
    if (IGNORED_PATHS.has(path)) return true;
    return path.split("/").some((part) => IGNORED_COMPONENTS.has(part));
  }

  markChanged(path) {
    if (!this.trackingEnabled || this.shouldIgnore(path)) return;
    this.deletedPaths.delete(path);
    this.changedPaths.add(path);
    this.schedulePersist();
  }

  markDeleted(path) {
    if (!this.trackingEnabled || this.shouldIgnore(path)) return;
    this.changedPaths.delete(path);
    this.deletedPaths.add(path);
    this.schedulePersist();
  }

  schedulePersist() {
    if (this.persistTimer !== null) window.clearTimeout(this.persistTimer);
    this.persistTimer = window.setTimeout(() => {
      this.persistTimer = null;
      void this.persistQueue();
    }, 1000);
  }

  async persistQueue() {
    this.settings.pendingChanged = [...this.changedPaths];
    this.settings.pendingDeleted = [...this.deletedPaths];
    this.settings.queueSchemaVersion = QUEUE_SCHEMA_VERSION;
    await this.saveData(this.settings);
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

  async createBlob(path) {
    const stat = await this.app.vault.adapter.stat(path);
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

  async pushNow(showNotice) {
    if (!this.trackingEnabled) {
      if (showNotice) new Notice("Vault Auto Push: finishing startup; try again in a moment.");
      return;
    }

    if (this.pushing) {
      if (showNotice) new Notice("Vault Auto Push: a push is already running.");
      return;
    }

    if (!this.settings.owner || !this.settings.repo || !this.settings.branch) {
      if (showNotice) new Notice("Vault Auto Push: configure the repository first.");
      return;
    }

    const pathsToUpload = [...this.changedPaths].filter((p) => !this.shouldIgnore(p));
    const pathsToDelete = [...this.deletedPaths].filter((p) => !this.shouldIgnore(p));

    if (pathsToUpload.length === 0 && pathsToDelete.length === 0) {
      this.lastPush = new Date();
      if (showNotice) new Notice("Vault Auto Push: nothing changed.");
      return;
    }

    this.pushing = true;
    this.lastError = null;
    this.lastSkipped = [];

    try {
      const head = await this.github(`/git/ref/heads/${encodeURIComponent(this.settings.branch)}`);
      const headSha = head.object.sha;
      const baseCommit = await this.github(`/git/commits/${headSha}`);
      const baseTreeSha = baseCommit.tree.sha;

      const tree = [];
      const uploaded = [];
      const deleted = [];

      for (const path of pathsToUpload) {
        if (!(await this.app.vault.adapter.exists(path))) {
          this.changedPaths.delete(path);
          this.deletedPaths.add(path);
          continue;
        }
        const blob = await this.createBlob(path);
        if (!blob) continue;
        tree.push({ path, mode: "100644", type: "blob", sha: blob.sha });
        uploaded.push(path);
      }

      for (const path of pathsToDelete) {
        tree.push({ path, mode: "100644", type: "blob", sha: null });
        deleted.push(path);
      }

      if (tree.length > 0) {
        const newTree = await this.github("/git/trees", "POST", {
          base_tree: baseTreeSha,
          tree,
        });

        if (newTree.sha !== baseTreeSha) {
          const commit = await this.github("/git/commits", "POST", {
            message: `${this.settings.commitPrefix} ${new Date().toISOString()}`,
            tree: newTree.sha,
            parents: [headSha],
          });

          await this.github(`/git/refs/heads/${encodeURIComponent(this.settings.branch)}`, "PATCH", {
            sha: commit.sha,
            force: false,
          });
        }
      }

      for (const path of uploaded) this.changedPaths.delete(path);
      for (const path of deleted) this.deletedPaths.delete(path);
      await this.persistQueue();

      this.lastPush = new Date();
      if (showNotice) {
        if (tree.length === 0 && this.lastSkipped.length) {
          new Notice(`Vault Auto Push: skipped ${this.lastSkipped.length} oversized file(s).`);
        } else {
          const suffix = this.lastSkipped.length ? ` Skipped ${this.lastSkipped.length} oversized file(s).` : "";
          new Notice(`Vault Auto Push: pushed successfully.${suffix}`);
        }
      }
    } catch (error) {
      this.lastError = error instanceof Error ? error.message : String(error);
      console.error("Vault Auto Push", error);
      await this.persistQueue();
      if (showNotice) new Notice(`Vault Auto Push failed: ${this.lastError}`);
    } finally {
      this.pushing = false;
    }
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
        ? "iOS detected. Scheduled pushes run while Obsidian is active; pending changes persist across restarts."
        : Platform.isMobile
          ? "Mobile Obsidian detected."
          : "Desktop Obsidian detected.",
    });
    status.createEl("div", { text: `Repository: ${this.plugin.settings.owner}/${this.plugin.settings.repo}` });
    status.createEl("div", { text: `Pending: ${this.plugin.changedPaths.size} changed, ${this.plugin.deletedPaths.size} deleted` });
    status.createEl("div", {
      text: !this.plugin.trackingEnabled
        ? "Status: finishing startup…"
        : this.plugin.pushing
          ? "Status: pushing…"
          : this.plugin.lastPush
            ? `Last push/check: ${this.plugin.lastPush.toLocaleString()}`
            : "Status: idle",
    });
    if (this.plugin.lastError) status.createEl("div", { cls: "vault-auto-push-error", text: this.plugin.lastError });

    new Setting(containerEl)
      .setName("Push now")
      .setDesc("Push only files currently queued as changed or deleted.")
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
      .setDesc("Push queued changes on the repeating timer while Obsidian is running.")
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
      .setDesc("If pending changes exist, push them when Obsidian starts or returns to the foreground.")
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
