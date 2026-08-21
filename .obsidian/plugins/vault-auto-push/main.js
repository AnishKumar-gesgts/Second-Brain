const {
  Notice,
  Platform,
  Plugin,
  PluginSettingTab,
  SecretComponent,
  Setting,
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
};

const IGNORED_PATHS = new Set([
  ".DS_Store",
  ".obsidian/workspace.json",
  ".obsidian/workspace-mobile.json",
  ".obsidian/plugins/vault-auto-push/data.json",
]);

const IGNORED_PREFIXES = [".trash/", ".git/", "node_modules/"];

module.exports = class VaultAutoPushPlugin extends Plugin {
  async onload() {
    await this.loadSettings();
    this.changedPaths = new Set();
    this.deletedPaths = new Set();
    this.fullSnapshotNeeded = true;
    this.pushing = false;
    this.lastPush = null;
    this.lastError = null;
    this.timerId = null;

    this.addSettingTab(new VaultAutoPushSettingTab(this.app, this));

    this.addCommand({
      id: "push-now",
      name: "Push vault to GitHub now",
      callback: () => this.pushNow(true),
    });

    this.addRibbonIcon("upload-cloud", "Push vault to GitHub", () => this.pushNow(true));

    this.registerEvent(this.app.vault.on("create", (file) => this.markChanged(file.path)));
    this.registerEvent(this.app.vault.on("modify", (file) => this.markChanged(file.path)));
    this.registerEvent(this.app.vault.on("delete", (file) => this.markDeleted(file.path)));
    this.registerEvent(this.app.vault.on("rename", (file, oldPath) => {
      this.markDeleted(oldPath);
      this.markChanged(file.path);
    }));

    this.registerDomEvent(document, "visibilitychange", () => {
      if (document.visibilityState === "visible") {
        this.fullSnapshotNeeded = true;
        if (this.settings.autoPush) void this.pushNow(false);
      }
    });

    this.configureTimer();

    if (this.settings.pushOnLoad && this.settings.autoPush) {
      this.app.workspace.onLayoutReady(() => void this.pushNow(false));
    }
  }

  onunload() {
    if (this.timerId !== null) window.clearInterval(this.timerId);
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
    this.configureTimer();
  }

  configureTimer() {
    if (this.timerId !== null) window.clearInterval(this.timerId);
    this.timerId = null;
    if (!this.settings.autoPush) return;

    const ms = Math.max(1, Number(this.settings.intervalMinutes) || 5) * 60_000;
    this.timerId = window.setInterval(() => void this.pushNow(false), ms);
    this.registerInterval(this.timerId);
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

  shouldIgnore(path) {
    if (!path) return true;
    if (IGNORED_PATHS.has(path)) return true;
    return IGNORED_PREFIXES.some((prefix) => path.startsWith(prefix));
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

  async getHead() {
    return await this.github(`/git/ref/heads/${encodeURIComponent(this.settings.branch)}`);
  }

  async getCommit(sha) {
    return await this.github(`/git/commits/${sha}`);
  }

  async getRemoteTree(treeSha) {
    const tree = await this.github(`/git/trees/${treeSha}?recursive=1`);
    if (tree.truncated) {
      throw new Error("GitHub returned a truncated repository tree. The vault is too large for this plugin version.");
    }
    return tree.tree || [];
  }

  async createBlob(path) {
    const data = await this.app.vault.adapter.readBinary(path);
    return await this.github("/git/blobs", "POST", {
      content: arrayBufferToBase64(data),
      encoding: "base64",
    });
  }

  async collectLocalFiles() {
    const result = [];
    const walk = async (folder) => {
      const listing = await this.app.vault.adapter.list(folder);
      for (const file of listing.files) {
        if (!this.shouldIgnore(file)) result.push(file);
      }
      for (const child of listing.folders) {
        if (!this.shouldIgnore(`${child}/placeholder`)) await walk(child);
      }
    };
    await walk("");
    return result;
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

    try {
      const head = await this.getHead();
      const headSha = head.object.sha;
      const baseCommit = await this.getCommit(headSha);
      const baseTreeSha = baseCommit.tree.sha;

      let pathsToUpload;
      let pathsToDelete;

      if (this.fullSnapshotNeeded) {
        const localFiles = await this.collectLocalFiles();
        const localSet = new Set(localFiles);
        const remoteTree = await this.getRemoteTree(baseTreeSha);
        const remoteFiles = remoteTree
          .filter((entry) => entry.type === "blob" && !this.shouldIgnore(entry.path))
          .map((entry) => entry.path);

        pathsToUpload = localFiles;
        pathsToDelete = remoteFiles.filter((path) => !localSet.has(path));
      } else {
        pathsToUpload = [...this.changedPaths].filter((path) => !this.shouldIgnore(path));
        pathsToDelete = [...this.deletedPaths].filter((path) => !this.shouldIgnore(path));
      }

      if (pathsToUpload.length === 0 && pathsToDelete.length === 0) {
        this.lastPush = new Date();
        if (showNotice) new Notice("Vault Auto Push: nothing changed.");
        return;
      }

      const tree = [];
      for (const path of pathsToUpload) {
        if (!(await this.app.vault.adapter.exists(path))) continue;
        const blob = await this.createBlob(path);
        tree.push({ path, mode: "100644", type: "blob", sha: blob.sha });
      }

      for (const path of pathsToDelete) {
        tree.push({ path, mode: "100644", type: "blob", sha: null });
      }

      if (tree.length === 0) {
        this.lastPush = new Date();
        return;
      }

      const newTree = await this.github("/git/trees", "POST", {
        base_tree: baseTreeSha,
        tree,
      });

      if (newTree.sha === baseTreeSha) {
        this.changedPaths.clear();
        this.deletedPaths.clear();
        this.fullSnapshotNeeded = false;
        this.lastPush = new Date();
        if (showNotice) new Notice("Vault Auto Push: already up to date.");
        return;
      }

      const stamp = new Date().toISOString();
      const commit = await this.github("/git/commits", "POST", {
        message: `${this.settings.commitPrefix} ${stamp}`,
        tree: newTree.sha,
        parents: [headSha],
      });

      // Do not force: if the remote branch moved since getHead(), fail instead of overwriting it.
      await this.github(`/git/refs/heads/${encodeURIComponent(this.settings.branch)}`, "PATCH", {
        sha: commit.sha,
        force: false,
      });

      this.changedPaths.clear();
      this.deletedPaths.clear();
      this.fullSnapshotNeeded = false;
      this.lastPush = new Date();
      if (showNotice) new Notice("Vault Auto Push: pushed successfully.");
    } catch (error) {
      this.lastError = error instanceof Error ? error.message : String(error);
      console.error("Vault Auto Push", error);
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
        ? "iOS detected. Scheduled pushes run while Obsidian is active; iOS may suspend timers in the background."
        : Platform.isMobile
          ? "Mobile Obsidian detected."
          : "Desktop Obsidian detected.",
    });
    status.createEl("div", { text: `Repository: ${this.plugin.settings.owner}/${this.plugin.settings.repo}` });
    status.createEl("div", {
      text: this.plugin.lastPush ? `Last check: ${this.plugin.lastPush.toLocaleString()}` : "Last check: not yet",
    });
    if (this.plugin.lastError) status.createEl("div", { cls: "vault-auto-push-error", text: this.plugin.lastError });

    new Setting(containerEl)
      .setName("Push now")
      .setDesc("Create one GitHub commit containing all current vault changes.")
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
      .setDesc("Choose or create a SecretStorage entry containing a fine-grained GitHub PAT with Contents: Read and write for this private repository.")
      .addComponent((el) => new SecretComponent(this.app, el)
        .setValue(this.plugin.settings.secretName)
        .onChange(async (value) => {
          this.plugin.settings.secretName = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName("Automatic push")
      .setDesc("Push changes on a repeating timer while Obsidian is running.")
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
      .setDesc("Useful on mobile because the OS can suspend background timers.")
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
