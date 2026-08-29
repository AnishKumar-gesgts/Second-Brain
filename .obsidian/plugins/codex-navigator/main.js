const { Plugin, ItemView, PluginSettingTab, Setting, Notice, setIcon, FuzzySuggestModal, MarkdownRenderer, requestUrl, Platform } = require("obsidian");

// Node and Electron APIs do not exist in Obsidian Mobile. Load them lazily only
// on desktop so the rest of the workspace can run on iOS and Android.
let spawn = null;
if (!Platform.isMobile) ({ spawn } = require("child_process"));

function baseName(filePath) {
  return String(filePath || "").split(/[\\/]/).pop() || "attachment";
}

const HOME_VIEW = "codex-workspace-home";
const CHAT_VIEW = "codex-workspace-chat";
const CANVAS_VIEW = "codex-workspace-canvas-checkup";
const CANVAS_DATA_PATH = "Machine/Canvas Checkup/assignments.json";
const CANVAS_NOTE_PATH = "Canvas Checkup.md";

const DEFAULT_SETTINGS = {
  codexPath: "codex",
  model: "gpt-5.6-luna",
  reasoningEffort: "low",
  openHomeOnStartup: true,
  defaultPermission: "workspace-write",
  permissionMigrationVersion: 0,
  notionToken: "",
  notionDatabaseId: "",
  notionSyncEnabled: false,
  notionAutoSync: false,
  notionLastSync: "",
  notionPanelWidth: 34,
  notionEmbedUrl: "https://schedulemgmt.notion.site/ebd//15163c0b69ed805085d1df7f4207ac0a?v=15163c0b69ed81729f38000c5bf2c2b6",
  homeRequestModel: "gpt-5.6-luna",
  canvasBaseUrl: "https://iusd.instructure.com",
  canvasToken: "",
  canvasSyncEnabled: false,
  canvasLastSync: "",
  canvasLastReset: ""
};

const MODEL_OPTIONS = [
  { value: "gpt-5.6-luna", label: "GPT-5.6 Luna", detail: "Fast" },
  { value: "gpt-5.6-terra", label: "GPT-5.6 Terra", detail: "Balanced" },
  { value: "gpt-5.6-sol", label: "GPT-5.6 Sol", detail: "Deep" }
];

class VaultFilePicker extends FuzzySuggestModal {
  constructor(app, onChoose) {
    super(app);
    this.onChoose = onChoose;
    this.setPlaceholder("Attach a file from this vault…");
  }

  getItems() {
    return this.app.vault.getFiles().filter((file) => !file.path.startsWith("Sample Obsidian Vault/") && !file.path.startsWith(".obsidian/"));
  }

  getItemText(file) { return file.path; }
  onChooseItem(file) { this.onChoose(file); }
}

function makeId() {
  return `chat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function iconButton(parent, icon, label, handler) {
  const button = parent.createEl("button", { cls: "cw-icon-button", attr: { title: label, "aria-label": label } });
  setIcon(button, icon);
  button.addEventListener("click", handler);
  return button;
}

function todayKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function timerElement(tag, className, text) {
  const element = (timerElement.ownerDocument || document).createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function timerButton(label, className, handler) {
  const button = timerElement("button", className || "", label);
  button.type = "button";
  button.addEventListener("click", handler);
  return button;
}

function formatClock(totalSeconds, showHours = false) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return showHours || hours > 0
    ? `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`
    : `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

function buildTimerWidget(parent, plugin, options = {}) {
  timerElement.ownerDocument = parent.ownerDocument || document;
  const widget = timerElement("section", "cw-timer-widget");
  const header = timerElement("div", "cw-timer-header");
  const title = timerElement("div", "cw-timer-title");
  title.append(timerElement("span", "cw-eyebrow", "FOCUS TOOLS"), timerElement("h2", "", options.popout ? "Focus timer" : "Timer, stopwatch & alarm"));
  const actions = timerElement("div", "cw-timer-actions");
  const popout = timerButton(options.popout ? "Close" : "Pop out", "cw-timer-secondary", () => {
    if (options.popout) options.close(); else plugin.openTimerPopout();
  });
  actions.append(popout);
  header.append(title, actions);
  widget.append(header);

  const tabs = timerElement("div", "cw-timer-tabs");
  const body = timerElement("div", "cw-timer-body");
  const display = timerElement("div", "cw-timer-display", "05:00");
  const status = timerElement("div", "cw-timer-status", "Ready");
  const controls = timerElement("div", "cw-timer-controls");
  const settings = timerElement("div", "cw-timer-settings");
  const alarmRow = timerElement("div", "cw-alarm-row");
  const timerInputs = timerElement("div", "cw-timer-inputs");
  const timerHours = timerElement("input", "", ""); timerHours.type = "number"; timerHours.min = "0"; timerHours.max = "99"; timerHours.value = "0"; timerHours.setAttribute("aria-label", "Timer hours");
  const timerMinutes = timerElement("input", "", ""); timerMinutes.type = "number"; timerMinutes.min = "0"; timerMinutes.max = "59"; timerMinutes.value = "5"; timerMinutes.setAttribute("aria-label", "Timer minutes");
  const timerSeconds = timerElement("input", "", ""); timerSeconds.type = "number"; timerSeconds.min = "0"; timerSeconds.max = "59"; timerSeconds.value = "0"; timerSeconds.setAttribute("aria-label", "Timer seconds");
  timerInputs.append(timerHours, timerMinutes, timerSeconds);
  const alarmInput = timerElement("input"); alarmInput.type = "time"; alarmInput.setAttribute("aria-label", "Alarm time");
  const alarmLabel = timerElement("label", "cw-alarm-label", "Alarm"); alarmLabel.append(alarmInput);
  const alarmToggle = timerElement("input"); alarmToggle.type = "checkbox"; alarmToggle.setAttribute("aria-label", "Enable alarm");
  const alarmEnable = timerElement("label", "cw-alarm-enable", "Enable"); alarmEnable.prepend(alarmToggle);
  alarmRow.append(alarmLabel, alarmEnable);
  settings.append(timerInputs, alarmRow);
  body.append(display, status, controls, settings);
  widget.append(tabs, body);
  parent.appendChild(widget);

  let mode = "timer";
  const setMode = (next) => { mode = next; render(); };
  ["timer", "stopwatch", "alarm"].forEach((name) => {
    const tab = timerButton(name[0].toUpperCase() + name.slice(1), name === mode ? "is-active" : "", () => setMode(name));
    tabs.append(tab);
  });
  const readDuration = () => (Number(timerHours.value || 0) * 3600) + (Number(timerMinutes.value || 0) * 60) + Number(timerSeconds.value || 0);
  const startTimer = () => { const duration = readDuration(); if (duration <= 0) return new Notice("Set a timer duration first."); plugin.startTimer(duration); };
  const reset = () => mode === "timer" ? plugin.resetTimer(readDuration()) : mode === "stopwatch" ? plugin.resetStopwatch() : plugin.setAlarm("", false);
  const pause = () => mode === "timer" ? plugin.pauseTimer() : mode === "stopwatch" ? plugin.pauseStopwatch() : undefined;
  controls.append(timerButton("Start", "mod-cta", () => mode === "timer" ? startTimer() : mode === "stopwatch" ? plugin.startStopwatch() : plugin.setAlarm(alarmInput.value, alarmToggle.checked)), timerButton("Pause", "", pause), timerButton("Reset", "", reset));
  alarmInput.addEventListener("change", () => { if (alarmToggle.checked) plugin.setAlarm(alarmInput.value, true); });
  alarmToggle.addEventListener("change", () => plugin.setAlarm(alarmInput.value, alarmToggle.checked));

  const render = () => {
    const state = plugin.timerState;
    tabs.querySelectorAll("button").forEach((button, index) => button.classList.toggle("is-active", ["timer", "stopwatch", "alarm"][index] === mode));
    timerInputs.style.display = mode === "timer" ? "flex" : "none";
    alarmRow.style.display = mode === "alarm" ? "flex" : "none";
    if (mode === "timer") {
      display.textContent = formatClock(plugin.getTimerRemaining());
      status.textContent = state.timerRunning ? "Timer running" : state.timerRemaining > 0 && state.timerRemaining !== state.timerDuration ? "Paused" : "Ready";
    } else if (mode === "stopwatch") {
      display.textContent = formatClock(plugin.getStopwatchElapsed(), true);
      status.textContent = state.stopwatchRunning ? "Stopwatch running" : state.stopwatchElapsed ? "Paused" : "Ready";
    } else {
      display.textContent = state.alarmTime || "--:--";
      status.textContent = state.alarmEnabled ? "Alarm armed" : "Set an alarm time";
      alarmInput.value = state.alarmTime || alarmInput.value;
      alarmToggle.checked = state.alarmEnabled;
    }
  };
  plugin.registerTimerWidget(widget, render);
  render();
  return widget;
}

class WorkspaceHomeView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType() { return HOME_VIEW; }
  getDisplayText() { return "Home"; }
  getIcon() { return "home"; }

  async onOpen() {
    await this.render();
  }

  async render() {
    const root = this.containerEl.children[1];
    root.empty();
    root.addClass("cw-home");

    const hero = root.createDiv({ cls: "cw-home-hero" });
    const heroText = hero.createDiv();
    heroText.createEl("span", { cls: "cw-eyebrow", text: "SECOND BRAIN" });
    heroText.createEl("h1", { text: "Home" });
    heroText.createEl("p", { text: new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric", year: "numeric" }) });
    const heroActions = hero.createDiv({ cls: "cw-hero-actions" });
    const newChat = heroActions.createEl("button", { cls: "mod-cta", text: "New Codex chat" });
    newChat.addEventListener("click", () => this.plugin.openNewChat());
    const refresh = heroActions.createEl("button", { text: "Refresh" });
    refresh.addEventListener("click", () => this.render());
    const notionSync = heroActions.createEl("button", { text: "Sync Notion" });
    notionSync.addEventListener("click", async () => {
      notionSync.disabled = true;
      try { await this.plugin.syncNotionTasks(); this.plugin.refreshNotionEmbed(); await this.render(); } finally { notionSync.disabled = false; }
    });
    const notionPush = heroActions.createEl("button", { text: "Push task status" });
    notionPush.addEventListener("click", () => this.plugin.pushNotionTaskStatus());

    const bookmarks = root.createDiv({ cls: "cw-bookmarks-bar", attr: { "aria-label": "Workspace bookmarks" } });
    bookmarks.createSpan({ cls: "cw-bookmarks-label", text: "Bookmarks" });
    this.bookmark(bookmarks, "home", "Home", () => this.plugin.openHome());
    this.bookmark(bookmarks, "search", "Google", () => this.plugin.openGooglePrompt());
    this.bookmark(bookmarks, "message-square-plus", "Codex chat", () => this.plugin.openNewChat());
    this.bookmark(bookmarks, "file-search", "Files", () => this.plugin.openFileSearch());
    this.bookmark(bookmarks, "graduation-cap", "Canvas Checkup", () => this.plugin.openCanvasCheckup());

    const searchCard = root.createDiv({ cls: "cw-search-card" });
    const googleMark = searchCard.createDiv({ cls: "cw-google-mark", text: "G" });
    const searchInput = searchCard.createEl("input", {
      attr: { type: "search", placeholder: "Search Google in an Obsidian tab…", "aria-label": "Search Google" }
    });
    const searchButton = searchCard.createEl("button", { cls: "mod-cta", text: "Search" });
    const submitSearch = () => {
      const query = searchInput.value.trim();
      if (query) this.plugin.openGoogleSearch(query);
    };
    searchButton.addEventListener("click", submitSearch);
    searchInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") submitSearch();
    });

    const quick = root.createDiv({ cls: "cw-quick-grid" });
    this.quickAction(quick, "message-square-plus", "New Codex chat", "Start a separate conversation tab", () => this.plugin.openNewChat());
    this.quickAction(quick, "calendar-days", "Today", "Open or create today’s daily note", () => this.plugin.openTodayNote());
    this.quickAction(quick, "check-square", "Task board", "Open the task dashboard", () => this.plugin.openVaultFile("Tasks/Task Board.md"));
    this.quickAction(quick, "inbox", "Task inbox", "Capture and organize loose tasks", () => this.plugin.openVaultFile("Tasks/Task Inbox.md"));
    this.quickAction(quick, "cloud", "Notion tasks", "Sync scheduled tasks with Notion", () => this.plugin.syncNotionTasks().then(() => { this.plugin.refreshNotionEmbed(); return this.render(); }));
    this.quickAction(quick, "graduation-cap", "Canvas Checkup", "See active assignments and their directions", () => this.plugin.openCanvasCheckup());

    buildTimerWidget(root, this.plugin);

    const content = root.createDiv({ cls: "cw-home-columns" });
    const notionPanel = content.createDiv({ cls: "cw-panel cw-notion-panel" });
    const notionHeader = notionPanel.createDiv({ cls: "cw-panel-header" });
    notionHeader.createEl("h2", { text: "Notion tasks" });
    notionHeader.createEl("span", { text: "Live Notion view" });
    const embed = notionPanel.createEl("iframe", {
      cls: "cw-notion-embed",
      attr: {
        src: this.plugin.settings.notionEmbedUrl || DEFAULT_SETTINGS.notionEmbedUrl,
        width: "100%",
        height: "600",
        frameborder: "0",
        allowfullscreen: "true",
        title: "Notion task database"
      }
    });
    embed.addEventListener("error", () => new Notice("The Notion embed could not be loaded. Use the Notion URL setting or open the page directly."));
    const codexBar = notionPanel.createDiv({ cls: "cw-codex-schedule-bar" });
    const codexInput = codexBar.createEl("input", { attr: { type: "text", placeholder: "Ask Codex to adjust your Notion schedule…", "aria-label": "Adjust Notion schedule with Codex" } });
    const codexSend = codexBar.createEl("button", { cls: "mod-cta", text: "Ask Codex" });
    const notionSyncButton = codexBar.createEl("button", { cls: "mod-cta", text: "Sync Notion" });
    const codexResult = notionPanel.createDiv({ cls: "cw-codex-schedule-result" });
    const submitScheduleRequest = async () => {
      const request = codexInput.value.trim();
      if (!request || codexSend.disabled) return;
      codexSend.disabled = true;
      codexResult.setText("Codex is working…");
      try { codexResult.setText(await this.plugin.runHomeCodexRequest(request)); }
      catch (error) { codexResult.setText(`Codex request failed: ${error.message}`); }
      finally { codexSend.disabled = false; }
    };
    codexSend.addEventListener("click", submitScheduleRequest);
    notionSyncButton.addEventListener("click", async () => {
      notionSyncButton.disabled = true;
      codexResult.setText("Syncing Notion…");
      try { await this.plugin.syncNotionTasks(); this.plugin.refreshNotionEmbed(); codexResult.setText("Notion sync completed and the Notion page was refreshed."); }
      finally { notionSyncButton.disabled = false; }
    });
    codexInput.addEventListener("keydown", (event) => { if (event.key === "Enter") submitScheduleRequest(); });

    content.style.setProperty("--cw-notion-width", `${this.plugin.settings.notionPanelWidth || 34}%`);
    content.style.setProperty("--cw-today-width", `${100 - (this.plugin.settings.notionPanelWidth || 34)}%`);
    const divider = content.createDiv({ cls: "cw-panel-resizer", attr: { title: "Drag to resize task panels", role: "separator", "aria-label": "Resize Notion and Today task panels" } });
    divider.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      const move = (moveEvent) => {
        const rect = content.getBoundingClientRect();
        const percent = Math.max(20, Math.min(50, ((moveEvent.clientX - rect.left) / rect.width) * 100));
        this.plugin.settings.notionPanelWidth = Math.round(percent);
        content.style.setProperty("--cw-notion-width", `${this.plugin.settings.notionPanelWidth}%`);
        content.style.setProperty("--cw-today-width", `${100 - this.plugin.settings.notionPanelWidth}%`);
      };
      const stop = () => {
        document.removeEventListener("pointermove", move);
        document.removeEventListener("pointerup", stop);
        this.plugin.savePluginData();
      };
      document.addEventListener("pointermove", move);
      document.addEventListener("pointerup", stop, { once: true });
    });

    const taskPanel = content.createDiv({ cls: "cw-panel cw-today-panel" });
    const taskHeader = taskPanel.createDiv({ cls: "cw-panel-header" });
    taskHeader.createEl("h2", { text: "Today" });
    taskHeader.createEl("span", { text: "Daily tasks and reminders" });
    const taskList = taskPanel.createDiv({ cls: "cw-list" });
    const tasks = (await this.plugin.collectTasks(40)).filter((task) => task.file.path === `Daily Notes/${todayKey()}.md`).slice(0, 12);
    if (!tasks.length) {
      taskList.createDiv({ cls: "cw-empty", text: "No open tasks yet. Add “- [ ]” anywhere in your notes." });
    } else {
      tasks.forEach((task) => {
        const row = taskList.createDiv({ cls: "cw-task-row" });
        row.createSpan({ cls: "cw-task-box" });
        const body = row.createDiv();
        body.createDiv({ cls: "cw-task-text", text: task.text });
        body.createDiv({ cls: "cw-task-source", text: task.file.basename });
        row.addEventListener("click", () => this.plugin.openFile(task.file));
      });
    }

    const recentPanel = content.createDiv({ cls: "cw-panel" });
    recentPanel.addClass("cw-recent-panel");
    const recentHeader = recentPanel.createDiv({ cls: "cw-panel-header" });
    recentHeader.createEl("h2", { text: "Recent notes" });
    recentHeader.createEl("span", { text: "Continue where you left off" });
    const recentList = recentPanel.createDiv({ cls: "cw-list" });
    const recent = this.plugin.getRecentNotes(10);
    if (!recent.length) {
      recentList.createDiv({ cls: "cw-empty", text: "Your recently edited notes will appear here." });
    } else {
      recent.forEach((file) => {
        const row = recentList.createDiv({ cls: "cw-recent-row" });
        const fileIcon = row.createSpan();
        setIcon(fileIcon, "file-text");
        const body = row.createDiv();
        body.createDiv({ cls: "cw-task-text", text: file.basename.replace(/\s*-\s*[a-f0-9]{8}(?:-[a-f0-9-]+)?\.md$/i, ".md").replace(/\.md$/i, "") });
        body.createDiv({ cls: "cw-task-source", text: file.parent?.path || "Vault" });
        row.addEventListener("click", () => this.plugin.openFile(file));
      });
    }
  }

  renderTaskRows(list, tasks, emptyText) {
    if (!tasks.length) {
      list.createDiv({ cls: "cw-empty", text: emptyText });
      return;
    }
    tasks.forEach((task) => {
      const row = list.createDiv({ cls: "cw-task-row" });
      row.createSpan({ cls: "cw-task-box" });
      const body = row.createDiv();
      body.createDiv({ cls: "cw-task-text", text: task.text });
      body.createDiv({ cls: "cw-task-source", text: task.file.basename });
      row.addEventListener("click", () => this.plugin.openFile(task.file));
    });
  }

  quickAction(parent, icon, title, description, handler) {
    const card = parent.createDiv({ cls: "cw-quick-action" });
    const mark = card.createDiv({ cls: "cw-quick-icon" });
    setIcon(mark, icon);
    const text = card.createDiv();
    text.createEl("strong", { text: title });
    text.createEl("span", { text: description });
    card.addEventListener("click", handler);
  }

  bookmark(parent, icon, label, handler) {
    const button = parent.createEl("button", { cls: "cw-bookmark", attr: { title: label, "aria-label": label } });
    const mark = button.createSpan({ cls: "cw-bookmark-icon" });
    setIcon(mark, icon);
    button.createSpan({ text: label });
    button.addEventListener("click", handler);
  }
}

class CanvasCheckupView extends ItemView {
  constructor(leaf, plugin) { super(leaf); this.plugin = plugin; }
  getViewType() { return CANVAS_VIEW; }
  getDisplayText() { return "Canvas Checkup"; }
  getIcon() { return "graduation-cap"; }
  async onOpen() { await this.render(); }

  async render() {
    if (this.renderPromise) return this.renderPromise;
    this.renderPromise = this.renderContent();
    try {
      await this.renderPromise;
    } finally {
      this.renderPromise = null;
    }
  }

  async renderContent() {
    const root = this.containerEl.children[1];
    root.empty();
    root.addClass("cw-canvas");
    const data = await this.plugin.readCanvasData();
    const hero = root.createDiv({ cls: "cw-canvas-hero" });
    const title = hero.createDiv();
    title.createEl("span", { cls: "cw-eyebrow", text: "SCHOOL DASHBOARD" });
    title.createEl("h1", { text: "Canvas Checkup" });
    title.createEl("p", { text: data.updatedAt ? `Last checked ${this.plugin.formatCanvasDate(data.updatedAt)}` : "Sign in and run the first check to load assignments." });
    const actions = hero.createDiv({ cls: "cw-hero-actions" });
    const sync = actions.createEl("button", { cls: "mod-cta", text: "Check now" });
    sync.addEventListener("click", async () => {
      sync.disabled = true; sync.setText("Checking…");
      try { await this.plugin.syncCanvasAssignments(); } finally { sync.disabled = false; }
    });
    const openCanvas = actions.createEl("button", { text: "Open Canvas" });
    openCanvas.addEventListener("click", () => window.open(`${this.plugin.settings.canvasBaseUrl || DEFAULT_SETTINGS.canvasBaseUrl}/`, "_blank"));
    if (data.error) {
      const alert = root.createDiv({ cls: "cw-canvas-alert" });
      alert.createEl("strong", { text: "Canvas needs attention" });
      alert.createEl("span", { text: data.error });
    }
    const assignments = Array.isArray(data.assignments) ? data.assignments : [];
    const assignmentBucket = (item) => item.bucket || (item.status === "Graded" || item.status === "Excused" ? "graded" : item.status === "Submitted; awaiting grade" ? "submitted" : "pending");
    const pending = assignments.filter((item) => assignmentBucket(item) === "pending");
    const submitted = assignments.filter((item) => assignmentBucket(item) === "submitted");
    const graded = assignments.filter((item) => assignmentBucket(item) === "graded");
    const summary = root.createDiv({ cls: "cw-canvas-summary" });
    const dueSoon = pending.filter((item) => item.dueAt && new Date(item.dueAt).getTime() - Date.now() <= 7 * 86400000 && new Date(item.dueAt).getTime() >= Date.now() - 86400000).length;
    [["Pending", pending.length], ["Due in 7 days", dueSoon], ["Submitted", submitted.length]].forEach(([label, value]) => {
      const card = summary.createDiv({ cls: "cw-canvas-stat" });
      card.createDiv({ cls: "cw-canvas-stat-value", text: String(value) });
      card.createDiv({ cls: "cw-canvas-stat-label", text: label });
    });
    const summaryText = data.summary || "";
    if (summaryText) {
      const analysis = root.createDiv({ cls: "cw-canvas-analysis" });
      analysis.createEl("span", { cls: "cw-eyebrow", text: "CHECK STATUS" });
      analysis.createEl("p", { text: summaryText });
    }
    const toolbar = root.createDiv({ cls: "cw-canvas-toolbar" });
    toolbar.createEl("h2", { text: "Assignments" });
    const filter = toolbar.createEl("input", { attr: { type: "search", placeholder: "Filter by assignment or class…", "aria-label": "Filter Canvas assignments" } });
    const tabs = root.createDiv({ cls: "cw-canvas-tabs", attr: { role: "tablist", "aria-label": "Assignment status" } });
    const list = root.createDiv({ cls: "cw-canvas-list" });
    let activeTab = "pending";
    const tabButtons = [["pending", "Pending", pending.length], ["submitted", "Submitted", submitted.length], ["graded", "Graded", graded.length]].map(([key, label, count]) => {
      const button = tabs.createEl("button", { cls: "cw-canvas-tab", text: `${label} (${count})`, attr: { role: "tab", "aria-selected": key === activeTab ? "true" : "false" } });
      button.addEventListener("click", () => { activeTab = key; tabButtons.forEach(([tabKey, tab]) => { tab.toggleClass("is-active", tabKey === activeTab); tab.setAttr("aria-selected", tabKey === activeTab ? "true" : "false"); }); draw(); });
      button.toggleClass("is-active", key === activeTab);
      return [key, button];
    });
    const renderCard = (item) => {
      const card = list.createEl("article", { cls: "cw-canvas-assignment" });
      const header = card.createDiv({ cls: "cw-canvas-assignment-header" });
      const heading = header.createDiv();
      heading.createEl("h3", { text: item.name || "Untitled assignment" });
      const completion = header.createEl("label", { cls: "cw-canvas-completion", attr: { title: "Mark this assignment as done for this view" } });
      const checkbox = completion.createEl("input", { attr: { type: "checkbox", "aria-label": `Mark ${item.name || "assignment"} as done` } });
      completion.createSpan({ text: "Done" });
      const submittedToCanvas = item.bucket === "submitted" || item.bucket === "graded" || item.status === "Submitted; awaiting grade" || item.status === "Graded" || item.status === "Excused";
      checkbox.checked = submittedToCanvas;
      card.toggleClass("is-confirmed", submittedToCanvas);
      checkbox.addEventListener("change", () => card.toggleClass("is-confirmed", checkbox.checked));
      header.createDiv({ cls: "cw-canvas-points", text: item.points == null ? "Points not listed" : `${item.points} pts` });
      const meta = card.createDiv({ cls: "cw-canvas-meta" });
      meta.createSpan({ text: item.dueAt ? `Due ${this.plugin.formatCanvasDate(item.dueAt)}` : "No due date" });
      meta.createSpan({ text: item.status || "Not submitted" });
      if (item.gradedAt) meta.createSpan({ text: `Graded ${this.plugin.formatCanvasDate(item.gradedAt)}` });
      const directions = card.createDiv({ cls: "cw-canvas-directions" });
      directions.createEl("h4", { text: "Directions" });
      directions.createEl("p", { text: item.directions || "No written directions were included on Canvas." });
      if (item.url) { const link = card.createEl("a", { text: "Open assignment in Canvas", href: item.url }); link.setAttr("target", "_blank"); link.setAttr("rel", "noopener"); }
    };
    const draw = () => {
      list.empty();
      const query = filter.value.trim().toLowerCase();
      const source = activeTab === "pending" ? pending : activeTab === "submitted" ? submitted : graded;
      const visible = source.filter((item) => !query || `${item.name} ${item.course}`.toLowerCase().includes(query));
      if (!visible.length) { list.createDiv({ cls: "cw-empty", text: source.length ? "No assignments match this filter." : `No ${activeTab} assignments are cached yet.` }); return; }
      if (activeTab === "pending") {
        const courses = new Map();
        visible.forEach((item) => { const course = item.course || "Course not listed"; if (!courses.has(course)) courses.set(course, []); courses.get(course).push(item); });
        for (const [course, items] of courses) {
          const section = list.createDiv({ cls: "cw-canvas-course-section" }); section.createEl("h2", { text: course });
          const dueDates = new Map();
          items.forEach((item) => { const key = item.dueAt ? new Date(item.dueAt).toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" }) : "No due date"; if (!dueDates.has(key)) dueDates.set(key, []); dueDates.get(key).push(item); });
          for (const [date, dueItems] of dueDates) { section.createEl("h3", { cls: "cw-canvas-date-heading", text: date }); dueItems.forEach(renderCard); }
        }
      } else {
        let shown = 5;
        const show = () => { list.empty(); visible.slice(0, shown).forEach(renderCard); if (shown < visible.length) { const more = list.createEl("button", { cls: "cw-canvas-load-more", text: `Load 5 more (${visible.length - shown} remaining)` }); more.addEventListener("click", () => { shown += 5; show(); }); } };
        show();
      }
    };
    filter.addEventListener("input", draw); draw();
  }
}

class CodexChatView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
    this.chatId = null;
    this.runningProcess = null;
    this.stdoutBuffer = "";
    this.finalAnswer = "";
    this.startedThreadId = null;
    this.pendingAttachments = [];
  }

  getViewType() { return CHAT_VIEW; }
  getDisplayText() { return this.chat?.title || "New Codex Chat"; }
  getIcon() { return "sparkles"; }
  getState() { return { chatId: this.chatId }; }

  async setState(state) {
    this.chatId = state?.chatId || this.chatId || makeId();
    this.chat = this.plugin.ensureChat(this.chatId);
    if (this.containerEl.children[1]) this.render();
  }

  async onOpen() {
    this.chatId = this.chatId || makeId();
    this.chat = this.plugin.ensureChat(this.chatId);
    this.render();
  }

  async onClose() {
    this.stopRun();
    await this.plugin.savePluginData();
  }

  render() {
    const root = this.containerEl.children[1];
    root.empty();
    root.addClass("cw-chat");

    const header = root.createDiv({ cls: "cw-chat-header" });
    const identity = header.createDiv({ cls: "cw-chat-identity" });
    const mark = identity.createDiv({ cls: "cw-codex-mark" });
    setIcon(mark, "sparkles");
    const heading = identity.createDiv();
    heading.createEl("strong", { text: this.chat.title });
    heading.createEl("span", { text: Platform.isMobile ? "Vault workspace · Codex chat requires desktop" : (this.chat.threadId ? "Persistent Codex CLI conversation" : "New Codex CLI conversation") });

    const actions = header.createDiv({ cls: "cw-chat-actions" });
    const modelSelect = actions.createEl("select", { cls: "dropdown cw-model-select", attr: { autocomplete: "off", "aria-label": "Codex model", title: "Choose model" } });
    MODEL_OPTIONS.forEach((model) => {
      const option = modelSelect.createEl("option", { text: `${model.label} · ${model.detail}` });
      option.value = model.value;
    });
    modelSelect.value = this.chat.model || this.plugin.settings.model || "gpt-5.6-luna";
    modelSelect.addEventListener("change", async () => {
      this.chat.model = modelSelect.value;
      const selected = MODEL_OPTIONS.find((item) => item.value === modelSelect.value);
      this.composerModel?.setText(selected?.label || modelSelect.value);
      await this.plugin.savePluginData();
    });

    const effortSelect = actions.createEl("select", { cls: "dropdown cw-effort-select", attr: { autocomplete: "off", "aria-label": "Reasoning effort", title: "Reasoning effort" } });
    [["low", "Low"], ["medium", "Medium"], ["high", "High"]].forEach(([value, label]) => {
      const option = effortSelect.createEl("option", { text: label });
      option.value = value;
    });
    effortSelect.value = this.chat.reasoningEffort || this.plugin.settings.reasoningEffort || "low";
    effortSelect.addEventListener("change", async () => {
      this.chat.reasoningEffort = effortSelect.value;
      await this.plugin.savePluginData();
    });

    const permission = actions.createEl("select", { cls: "dropdown", attr: { autocomplete: "off", "aria-label": "Conversation file permission" } });
    const read = permission.createEl("option", { text: "Read only" });
    read.value = "read-only";
    const edit = permission.createEl("option", { text: "Allow vault edits" });
    edit.value = "workspace-write";
    permission.value = this.chat.permission || "workspace-write";
    permission.disabled = Boolean(this.chat.threadId);
    permission.title = this.chat.threadId ? "Permission is fixed when a Codex thread starts. Open a new chat to change it." : "Choose before sending the first message.";
    permission.addEventListener("change", async () => {
      this.chat.permission = permission.value;
      if (permission.value === "workspace-write") new Notice("This conversation may edit files inside the vault.");
      await this.plugin.savePluginData();
    });
    iconButton(actions, "search", "Search Google", () => this.showGoogleSearch());
    iconButton(actions, "message-square-plus", "New chat tab", () => this.plugin.openNewChat());

    this.googleBar = root.createDiv({ cls: "cw-chat-google" });
    this.googleBar.hide();
    const googleInput = this.googleBar.createEl("input", { attr: { type: "search", placeholder: "Search Google…" } });
    const googleButton = this.googleBar.createEl("button", { cls: "mod-cta", text: "Search" });
    const doGoogle = () => {
      if (googleInput.value.trim()) this.plugin.openGoogleSearch(googleInput.value.trim());
    };
    googleButton.addEventListener("click", doGoogle);
    googleInput.addEventListener("keydown", (event) => { if (event.key === "Enter") doGoogle(); });

    this.messages = root.createDiv({ cls: "cw-chat-messages" });
    if (Platform.isMobile) {
      const mobileNotice = this.messages.createDiv({ cls: "cw-mobile-notice" });
      setIcon(mobileNotice.createSpan({ cls: "cw-mobile-notice-icon" }), "smartphone");
      const mobileCopy = mobileNotice.createDiv();
      mobileCopy.createEl("strong", { text: "Codex chat needs the desktop app" });
      mobileCopy.createEl("p", { text: "Obsidian Mobile cannot run the local Codex CLI. Home, notes, tasks, Canvas Checkup, Notion sync, Google search, and focus tools remain available on this phone." });
    }
    if (!this.chat.messages.length) {
      const welcome = this.messages.createDiv({ cls: "cw-chat-welcome" });
      const welcomeIcon = welcome.createDiv({ cls: "cw-welcome-icon" });
      setIcon(welcomeIcon, "sparkles");
      welcome.createEl("h2", { text: "What should we work on?" });
      welcome.createEl("p", { text: "Ask about any file in this vault, run a workflow like /today, or ask Codex to research the web when current information is needed." });
      const suggestions = welcome.createDiv({ cls: "cw-suggestions" });
      [
        "What should I focus on today?",
        "Summarize my active projects",
        "Find unfinished tasks across the vault",
        "Research a topic and connect it to my notes"
      ].forEach((text) => {
        const button = suggestions.createEl("button", { text });
        button.addEventListener("click", () => { this.promptInput.value = text; this.promptInput.focus(); });
      });
    } else {
      this.chat.messages.forEach((message) => this.renderMessage(message.role, message.text, message.attachments));
    }

    const composerWrap = root.createDiv({ cls: "cw-composer-wrap" });
    this.attachmentTray = composerWrap.createDiv({ cls: "cw-attachment-tray" });
    this.renderAttachmentTray();
    const composer = composerWrap.createDiv({ cls: "cw-composer" });
    this.promptInput = composer.createEl("textarea", {
      attr: { rows: "2", placeholder: "Message Codex…  (Enter to send, Shift+Enter for a new line)", "aria-label": "Message Codex" }
    });
    this.promptInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        this.submit();
      }
    });
    const composerFooter = composer.createDiv({ cls: "cw-composer-footer" });
    const composerTools = composerFooter.createDiv({ cls: "cw-composer-tools" });
    iconButton(composerTools, "paperclip", "Attach a vault file", () => this.openVaultFilePicker());
    iconButton(composerTools, "folder-open", "Attach a file from your computer", () => this.fileInput.click());
    const activeModel = MODEL_OPTIONS.find((item) => item.value === (this.chat.model || this.plugin.settings.model));
    this.composerModel = composerTools.createSpan({ cls: "cw-composer-model", text: Platform.isMobile ? "Desktop Codex CLI required" : (activeModel?.label || this.chat.model || this.plugin.settings.model) });

    this.fileInput = composer.createEl("input", { attr: { type: "file", multiple: "true", "aria-label": "Attach files" } });
    this.fileInput.addClass("cw-hidden-file-input");
    this.fileInput.addEventListener("change", () => {
      this.addExternalFiles(Array.from(this.fileInput.files || []));
      this.fileInput.value = "";
    });
    composer.addEventListener("dragover", (event) => {
      event.preventDefault();
      composer.addClass("is-dragging");
    });
    composer.addEventListener("dragleave", () => composer.removeClass("is-dragging"));
    composer.addEventListener("drop", (event) => {
      event.preventDefault();
      composer.removeClass("is-dragging");
      this.addExternalFiles(Array.from(event.dataTransfer?.files || []));
    });

    this.sendButton = iconButton(composerFooter, "arrow-up", "Send", () => this.submit());
    this.sendButton.addClass("cw-send-button");
    this.stopButton = iconButton(composerFooter, "square", "Stop", () => this.stopRun());
    this.stopButton.addClass("cw-stop-button");
    this.stopButton.hide();
    this.statusEl = composerWrap.createDiv({ cls: "cw-chat-status", text: Platform.isMobile ? "Browse and manage your vault from Home; continue Codex chats on desktop." : (this.chat.threadId ? "Conversation ready" : "Ready to start a new conversation") });
    if (Platform.isMobile) {
      modelSelect.disabled = true;
      effortSelect.disabled = true;
      permission.disabled = true;
      this.promptInput.disabled = true;
      this.promptInput.placeholder = "Codex CLI conversations are available on desktop";
      this.sendButton.disabled = true;
      this.fileInput.disabled = true;
      composer.addClass("is-mobile-disabled");
    }
  }

  showGoogleSearch() {
    this.googleBar.toggle(!this.googleBar.isShown());
    if (this.googleBar.isShown()) this.googleBar.querySelector("input")?.focus();
  }

  openVaultFilePicker() {
    new VaultFilePicker(this.app, (file) => {
      const fullPath = this.app.vault.adapter.getFullPath(file.path);
      this.addAttachment({ name: file.name, path: fullPath, vaultPath: file.path });
    }).open();
  }

  addExternalFiles(files) {
    let webUtils = null;
    try { webUtils = require("electron").webUtils; } catch (_) {}
    for (const file of files) {
      let fullPath = file.path || "";
      if (!fullPath && webUtils?.getPathForFile) {
        try { fullPath = webUtils.getPathForFile(file); } catch (_) {}
      }
      if (!fullPath) {
        new Notice(`Could not access ${file.name}. Try attaching it from the vault picker.`);
        continue;
      }
      this.addAttachment({ name: file.name || baseName(fullPath), path: fullPath, vaultPath: null });
    }
  }

  addAttachment(attachment) {
    const key = attachment.path.toLowerCase();
    if (this.pendingAttachments.some((item) => item.path.toLowerCase() === key)) return;
    this.pendingAttachments.push(attachment);
    this.renderAttachmentTray();
  }

  renderAttachmentTray() {
    if (!this.attachmentTray) return;
    this.attachmentTray.empty();
    this.attachmentTray.toggle(this.pendingAttachments.length > 0);
    this.pendingAttachments.forEach((attachment, index) => {
      const chip = this.attachmentTray.createDiv({ cls: "cw-attachment-chip" });
      const icon = chip.createSpan();
      setIcon(icon, /\.(png|jpe?g|webp|gif)$/i.test(attachment.name) ? "image" : "file-text");
      chip.createSpan({ cls: "cw-attachment-name", text: attachment.name, attr: { title: attachment.path } });
      const remove = chip.createEl("button", { attr: { title: "Remove attachment", "aria-label": `Remove ${attachment.name}` } });
      setIcon(remove, "x");
      remove.addEventListener("click", () => {
        this.pendingAttachments.splice(index, 1);
        this.renderAttachmentTray();
      });
    });
  }

  renderMessage(role, text, attachments = []) {
    const message = this.messages.createDiv({ cls: `cw-message is-${role}` });
    const avatar = message.createDiv({ cls: "cw-message-avatar" });
    setIcon(avatar, role === "user" ? "user" : "sparkles");
    const body = message.createDiv({ cls: "cw-message-content" });
    body.createDiv({ cls: "cw-message-label", text: role === "user" ? "You" : "Codex" });
    const messageText = body.createDiv({ cls: "cw-message-text markdown-rendered" });
    const markdown = String(text || "");
    MarkdownRenderer.render(this.app, markdown, messageText, "", this).catch(() => {
      messageText.empty();
      messageText.setText(markdown);
    });
    if (attachments?.length) {
      const files = body.createDiv({ cls: "cw-message-attachments" });
      attachments.forEach((name) => {
        const chip = files.createDiv({ cls: "cw-message-file" });
        setIcon(chip.createSpan(), "paperclip");
        chip.createSpan({ text: name });
      });
    }
    this.messages.scrollTop = this.messages.scrollHeight;
  }

  setBusy(busy, text) {
    this.sendButton.toggle(!busy);
    this.stopButton.toggle(busy);
    this.promptInput.disabled = busy;
    this.statusEl.setText(text || (busy ? "Codex is working…" : "Conversation ready"));
    this.statusEl.toggleClass("is-busy", busy);
  }

  attachmentPrompt(attachments) {
    if (!attachments.length) return "";
    return `\n\nATTACHED FILES\n${attachments.map((item) => `- ${item.path}`).join("\n")}\nInspect these files as part of the request. Images are also attached through the Codex CLI image flag when supported.`;
  }

  buildFirstPrompt(question, attachments) {
    const history = this.chat.messages.slice(0, -1).slice(-12).map((message) => `${message.role.toUpperCase()}: ${message.text}`).join("\n\n");
    const permissionInstruction = this.chat.permission === "read-only"
      ? "This conversation is read-only: inspect and answer without changing files."
      : "This conversation has workspace-write access: make requested vault changes directly and verify them.";
    return `You are the assistant embedded in this Obsidian vault through Codex CLI. The vault root is your working directory. Read AGENTS.md and follow the vault workflows and Human/Machine/System boundaries. ${permissionInstruction} Use Obsidian-compatible Markdown in responses. Format mathematical notation as LaTeX with $...$ for inline equations and $$...$$ for display equations. Use your available web-search capability when the question needs current information. Your internal web search is not guaranteed to use Google, so do not claim that it does. When the user explicitly asks to see Google results in Obsidian, put [[GOOGLE_SEARCH:their search query]] on the final line; the plugin will open that Google search in a separate Obsidian tab.${history ? `\n\nVISIBLE CONVERSATION HISTORY\n${history}` : ""}${this.attachmentPrompt(attachments)}\n\nUSER REQUEST\n${question}`;
  }

  async submit() {
    if (Platform.isMobile || !spawn) {
      new Notice("Codex chat requires Obsidian Desktop because the Codex CLI cannot run on iOS or Android.");
      return;
    }
    const question = this.promptInput.value.trim();
    if (!question || this.runningProcess) return;
    const attachments = [...this.pendingAttachments];
    this.pendingAttachments = [];
    this.renderAttachmentTray();
    this.promptInput.value = "";
    this.chat.messages.push({ role: "user", text: question, attachments: attachments.map((item) => item.name), at: Date.now() });
    this.renderMessage("user", question, attachments.map((item) => item.name));
    if (this.chat.title === "New Codex Chat") {
      this.chat.title = question.replace(/\s+/g, " ").slice(0, 46) || "Codex Chat";
      this.leaf.updateHeader?.();
      this.app.workspace.requestSaveLayout();
    }
    await this.plugin.savePluginData();

    const isResume = Boolean(this.chat.threadId);
    const executable = this.plugin.settings.codexPath || "codex";
    const model = this.chat.model || this.plugin.settings.model;
    const effort = this.chat.reasoningEffort || this.plugin.settings.reasoningEffort;
    const imagePaths = attachments.filter((item) => /\.(png|jpe?g|webp|gif)$/i.test(item.path)).map((item) => item.path);
    const promptForCli = isResume ? `${question}${this.attachmentPrompt(attachments)}` : this.buildFirstPrompt(question, attachments);
    let args;
    if (isResume) {
      args = ["exec", "resume", "--json", "--skip-git-repo-check"];
      if (model) args.push("--model", model);
      if (effort) args.push("-c", `model_reasoning_effort=\"${effort}\"`);
      imagePaths.forEach((imagePath) => args.push("--image", imagePath));
      args.push(this.chat.threadId, "-");
    } else {
      args = ["exec", "--json", "--skip-git-repo-check", "--color", "never", "--cd", this.plugin.getVaultPath(), "--sandbox", this.chat.permission || "workspace-write"];
      if (model) args.push("--model", model);
      if (effort) args.push("-c", `model_reasoning_effort=\"${effort}\"`);
      imagePaths.forEach((imagePath) => args.push("--image", imagePath));
      args.push("-");
    }

    this.stdoutBuffer = "";
    this.finalAnswer = "";
    this.startedThreadId = null;
    this.setBusy(true, isResume ? "Continuing conversation…" : "Starting Codex conversation…");

    try {
      const child = spawn(executable, args, {
        cwd: this.plugin.getVaultPath(),
        windowsHide: true,
        shell: false,
        env: { ...process.env, NO_COLOR: "1" }
      });
      this.runningProcess = child;
      let stderr = "";
      child.stdout.setEncoding("utf8");
      child.stderr.setEncoding("utf8");
      child.stdout.on("data", (chunk) => this.consumeJson(chunk));
      child.stderr.on("data", (chunk) => { stderr += chunk; });
      child.on("error", (error) => this.finishRun(null, `${stderr}\n${error.message}`));
      child.on("close", (code) => this.finishRun(code, stderr));
      child.stdin.end(promptForCli, "utf8");
    } catch (error) {
      this.finishRun(null, error.message);
    }
  }

  consumeJson(chunk) {
    this.stdoutBuffer += chunk;
    const lines = this.stdoutBuffer.split(/\r?\n/);
    this.stdoutBuffer = lines.pop() || "";
    lines.forEach((line) => {
      if (!line.trim()) return;
      try {
        const event = JSON.parse(line);
        if (event.type === "thread.started" && event.thread_id) this.startedThreadId = event.thread_id;
        if (event.type === "item.completed") {
          const item = event.item || {};
          if (item.type === "agent_message" && item.text) this.finalAnswer = item.text;
          if (item.type === "command_execution") this.statusEl.setText("Codex is working with your vault…");
          if (item.type === "web_search") this.statusEl.setText("Codex is researching the web…");
        }
      } catch (_) {}
    });
  }

  async finishRun(code, stderr) {
    if (!this.runningProcess && code !== null) return;
    this.runningProcess = null;
    this.setBusy(false);
    if (code === 0 && this.finalAnswer) {
      if (this.startedThreadId && !this.chat.threadId) this.chat.threadId = this.startedThreadId;
      const searches = [...this.finalAnswer.matchAll(/\[\[GOOGLE_SEARCH:([^\]]+)\]\]/g)].map((match) => match[1].trim());
      const answer = this.finalAnswer.replace(/\n?\[\[GOOGLE_SEARCH:[^\]]+\]\]/g, "").trim();
      this.chat.messages.push({ role: "assistant", text: answer, at: Date.now() });
      this.renderMessage("assistant", answer);
      if (searches.length) this.plugin.openGoogleSearch(searches[searches.length - 1]);
      await this.plugin.savePluginData();
      this.statusEl.setText(this.chat.threadId ? "Conversation saved · persistent CLI thread" : "Conversation ready");
    } else {
      const detail = String(stderr || "Codex exited without returning an answer.").trim().split(/\r?\n/).slice(-6).join("\n");
      const text = `I couldn't complete that request.\n\n${detail}`;
      this.chat.messages.push({ role: "assistant", text, at: Date.now() });
      this.renderMessage("assistant", text);
      this.statusEl.setText("Codex run failed");
      this.statusEl.addClass("is-error");
      await this.plugin.savePluginData();
    }
    this.promptInput.focus();
  }

  stopRun() {
    if (!this.runningProcess) return;
    try { this.runningProcess.kill(); } catch (_) {}
    this.runningProcess = null;
    if (this.sendButton) this.setBusy(false, "Stopped");
  }
}

class CodexWorkspaceSettings extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "Codex Workspace" });
    containerEl.createEl("p", { text: "Each Obsidian chat tab maps to a persistent Codex CLI conversation. Google searches open through Obsidian’s core Web Viewer." });
    new Setting(containerEl).setName("Codex executable").addText((text) => text.setValue(this.plugin.settings.codexPath).onChange(async (value) => {
      this.plugin.settings.codexPath = value.trim();
      await this.plugin.savePluginData();
    }));
    new Setting(containerEl).setName("Default model").addDropdown((dropdown) => {
      MODEL_OPTIONS.forEach((model) => dropdown.addOption(model.value, `${model.label} · ${model.detail}`));
      dropdown.setValue(this.plugin.settings.model).onChange(async (value) => {
        this.plugin.settings.model = value;
        await this.plugin.savePluginData();
      });
    });
    new Setting(containerEl).setName("Reasoning effort").addDropdown((dropdown) => dropdown
      .addOption("low", "Low")
      .addOption("medium", "Medium")
      .addOption("high", "High")
      .setValue(this.plugin.settings.reasoningEffort)
      .onChange(async (value) => {
        this.plugin.settings.reasoningEffort = value;
        await this.plugin.savePluginData();
      }));
    new Setting(containerEl).setName("Open Home on startup").addToggle((toggle) => toggle.setValue(this.plugin.settings.openHomeOnStartup).onChange(async (value) => {
      this.plugin.settings.openHomeOnStartup = value;
      await this.plugin.savePluginData();
    }));
    new Setting(containerEl).setName("Default file access").setDesc("New conversations start with this sandbox. Vault edits is now the default.").addDropdown((dropdown) => dropdown
      .addOption("workspace-write", "Allow vault edits")
      .addOption("read-only", "Read only")
      .setValue(this.plugin.settings.defaultPermission)
      .onChange(async (value) => {
        this.plugin.settings.defaultPermission = value;
        await this.plugin.savePluginData();
      }));
    containerEl.createEl("h2", { text: "Notion task bridge" });
    containerEl.createEl("p", { text: "Connect a Notion integration token and a task database. The bridge uses the database properties Name, Status, Due, Priority, and Obsidian Path when available." });
    new Setting(containerEl).setName("Enable Notion task sync").setDesc("Adds manual Notion sync controls to Home.").addToggle((toggle) => toggle.setValue(this.plugin.settings.notionSyncEnabled).onChange(async (value) => {
      this.plugin.settings.notionSyncEnabled = value;
      await this.plugin.savePluginData();
    }));
    new Setting(containerEl).setName("Notion integration token").setDesc("Stored in this vault's plugin data. Create a restricted internal integration in Notion.").addText((text) => {
      text.inputEl.type = "password";
      text.setValue(this.plugin.settings.notionToken).onChange(async (value) => {
        this.plugin.settings.notionToken = value.trim();
        await this.plugin.savePluginData();
      });
    });
    new Setting(containerEl).setName("Task database ID or URL").setDesc("Paste the ID or full Notion database URL.").addText((text) => text.setValue(this.plugin.settings.notionDatabaseId).onChange(async (value) => {
      this.plugin.settings.notionDatabaseId = this.plugin.extractNotionId(value);
      await this.plugin.savePluginData();
    }));
    new Setting(containerEl).setName("Embedded Notion page URL").setDesc("The shared Notion URL displayed in the Home panel.").addText((text) => text.setValue(this.plugin.settings.notionEmbedUrl).onChange(async (value) => {
      this.plugin.settings.notionEmbedUrl = value.trim();
      await this.plugin.savePluginData();
    }));
    new Setting(containerEl).setName("Automatic sync on Home open").addToggle((toggle) => toggle.setValue(this.plugin.settings.notionAutoSync).onChange(async (value) => {
      this.plugin.settings.notionAutoSync = value;
      await this.plugin.savePluginData();
    }));
    new Setting(containerEl).setName("Sync now").setDesc(this.plugin.settings.notionLastSync ? `Last sync: ${this.plugin.settings.notionLastSync}` : "No sync completed yet.").addButton((button) => button.setButtonText("Sync Notion").onClick(() => this.plugin.syncNotionTasks()));
    containerEl.createEl("h2", { text: "Canvas Checkup" });
    containerEl.createEl("p", { text: "Canvas Checkup runs entirely inside Obsidian through Canvas's official API. It makes no Codex requests or model calls. Use a revocable Canvas access token here; never enter your IUSD password into Obsidian." });
    new Setting(containerEl).setName("Enable Canvas checks").setDesc("Runs quietly every hour from 8 AM through 11 PM, with one local reset at 6 AM, while Obsidian is running.").addToggle((toggle) => toggle.setValue(this.plugin.settings.canvasSyncEnabled).onChange(async (value) => {
      this.plugin.settings.canvasSyncEnabled = value; await this.plugin.savePluginData(); this.plugin.scheduleCanvasSync();
    }));
    new Setting(containerEl).setName("Canvas access token").setDesc("Create a revocable token in Canvas Account → Settings → Approved Integrations. Stored in this vault's local plugin data.").addText((text) => {
      text.inputEl.type = "password"; text.setPlaceholder("Paste a Canvas access token");
      text.setValue(this.plugin.settings.canvasToken).onChange(async (value) => { this.plugin.settings.canvasToken = value.trim(); await this.plugin.savePluginData(); });
    });
    new Setting(containerEl).setName("Canvas site").addText((text) => text.setValue(this.plugin.settings.canvasBaseUrl).onChange(async (value) => {
      this.plugin.settings.canvasBaseUrl = value.trim().replace(/\/$/, "") || DEFAULT_SETTINGS.canvasBaseUrl; await this.plugin.savePluginData();
    }));
    new Setting(containerEl).setName("Check now").setDesc(this.plugin.settings.canvasLastSync ? `Last check: ${this.plugin.settings.canvasLastSync}` : "No Canvas check completed yet.").addButton((button) => button.setButtonText("Run Canvas Checkup").onClick(() => this.plugin.syncCanvasAssignments()));
  }
}

module.exports = class CodexWorkspacePlugin extends Plugin {
  async onload() {
    const raw = await this.loadData() || {};
    if (raw.settings || raw.chats) {
      this.settings = Object.assign({}, DEFAULT_SETTINGS, raw.settings || {});
      this.chats = raw.chats || {};
    } else {
      this.settings = Object.assign({}, DEFAULT_SETTINGS, raw);
      this.chats = {};
    }
    if (this.settings.homeRequestModel === "o4-mini") {
      this.settings.homeRequestModel = "gpt-5.6-luna";
      await this.savePluginData();
    }
    if ((this.settings.permissionMigrationVersion || 0) < 1) {
      this.settings.defaultPermission = "workspace-write";
      Object.values(this.chats).forEach((chat) => {
        chat.permission = "workspace-write";
        if (chat.threadId) {
          chat.threadId = null;
          chat.recreatedForWorkspaceWrite = true;
        }
      });
      this.settings.permissionMigrationVersion = 1;
      await this.savePluginData();
    }
    this.registerView(HOME_VIEW, (leaf) => new WorkspaceHomeView(leaf, this));
    this.registerView(CHAT_VIEW, (leaf) => new CodexChatView(leaf, this));
    this.registerView(CANVAS_VIEW, (leaf) => new CanvasCheckupView(leaf, this));
    this.timerState = {
      timerDuration: 300, timerRemaining: 300, timerRunning: false, timerStartedAt: 0,
      stopwatchElapsed: 0, stopwatchRunning: false, stopwatchStartedAt: 0,
      alarmTime: "", alarmEnabled: false, alarmTriggered: ""
    };
    this.timerWidgets = new Set();
    this.timerInterval = window.setInterval(() => this.tickTimers(), 250);
    this.canvasScheduleTimeout = null;
    this.scheduleCanvasSync();
    this.addRibbonIcon("home", "Open Home", () => this.openHome());
    this.addRibbonIcon("message-square-plus", "New Codex chat", () => this.openNewChat());
    this.addRibbonIcon("graduation-cap", "Open Canvas Checkup", () => this.openCanvasCheckup());
    this.addCommand({ id: "open-home", name: "Open Home", callback: () => this.openHome() });
    this.addCommand({ id: "new-codex-chat", name: "New Codex chat tab", callback: () => this.openNewChat() });
    this.addCommand({ id: "google-search", name: "Search Google", callback: () => this.openGooglePrompt() });
    this.addCommand({ id: "sync-notion-tasks", name: "Sync Notion tasks", callback: () => this.syncNotionTasks() });
    this.addCommand({ id: "push-notion-task-status", name: "Push Notion task status", callback: () => this.pushNotionTaskStatus() });
    this.addCommand({ id: "open-canvas-checkup", name: "Open Canvas Checkup", callback: () => this.openCanvasCheckup() });
    this.addCommand({ id: "sync-canvas-checkup", name: "Check Canvas assignments now", callback: () => this.syncCanvasAssignments() });
    this.addSettingTab(new CodexWorkspaceSettings(this.app, this));
    this.app.workspace.onLayoutReady(() => {
      if (this.settings.openHomeOnStartup) this.openHome();
    });
  }

  onunload() {
    if (this.timerInterval) window.clearInterval(this.timerInterval);
    if (this.canvasScheduleTimeout) window.clearTimeout(this.canvasScheduleTimeout);
    this.app.workspace.detachLeavesOfType(HOME_VIEW);
    this.app.workspace.detachLeavesOfType(CHAT_VIEW);
    this.app.workspace.detachLeavesOfType(CANVAS_VIEW);
  }

  ensureChat(chatId) {
    if (!this.chats[chatId]) {
      this.chats[chatId] = {
        id: chatId,
        title: "New Codex Chat",
        threadId: null,
        permission: this.settings.defaultPermission || "workspace-write",
        model: this.settings.model || "gpt-5.6-luna",
        reasoningEffort: this.settings.reasoningEffort || "low",
        messages: [],
        createdAt: Date.now()
      };
      this.savePluginData();
    }
    return this.chats[chatId];
  }

  async savePluginData() {
    await this.saveData({ settings: this.settings, chats: this.chats });
  }

  registerTimerWidget(element, render) {
    const entry = { element, render };
    this.timerWidgets.add(entry);
    return () => this.timerWidgets.delete(entry);
  }

  refreshTimerWidgets() {
    for (const entry of this.timerWidgets) {
      if (!entry.element.isConnected) this.timerWidgets.delete(entry);
      else entry.render();
    }
  }

  getTimerRemaining() {
    const state = this.timerState;
    return state.timerRunning ? Math.max(0, state.timerDuration - ((Date.now() - state.timerStartedAt) / 1000)) : state.timerRemaining;
  }

  getStopwatchElapsed() {
    const state = this.timerState;
    return state.stopwatchRunning ? state.stopwatchElapsed + ((Date.now() - state.stopwatchStartedAt) / 1000) : state.stopwatchElapsed;
  }

  tickTimers() {
    const state = this.timerState;
    if (state.timerRunning && this.getTimerRemaining() <= 0) {
      state.timerRemaining = 0;
      state.timerRunning = false;
      this.playAlarm("Timer finished");
    } else if (state.timerRunning) {
      state.timerRemaining = this.getTimerRemaining();
    }
    if (state.alarmEnabled && state.alarmTime) {
      const now = new Date();
      const key = `${todayKey()} ${state.alarmTime}`;
      if (`${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}` === state.alarmTime && state.alarmTriggered !== key) {
        state.alarmTriggered = key;
        this.playAlarm("Alarm");
      }
    }
    this.refreshTimerWidgets();
  }

  startTimer(duration) {
    const state = this.timerState;
    state.timerDuration = duration;
    state.timerRemaining = duration;
    state.timerStartedAt = Date.now();
    state.timerRunning = true;
    this.refreshTimerWidgets();
  }

  pauseTimer() {
    const state = this.timerState;
    if (!state.timerRunning) return;
    state.timerRemaining = this.getTimerRemaining();
    state.timerRunning = false;
    this.refreshTimerWidgets();
  }

  resetTimer(duration) {
    const state = this.timerState;
    state.timerRunning = false;
    state.timerDuration = duration || state.timerDuration || 300;
    state.timerRemaining = state.timerDuration;
    this.refreshTimerWidgets();
  }

  startStopwatch() {
    const state = this.timerState;
    if (!state.stopwatchRunning) { state.stopwatchStartedAt = Date.now(); state.stopwatchRunning = true; }
    this.refreshTimerWidgets();
  }

  pauseStopwatch() {
    const state = this.timerState;
    if (state.stopwatchRunning) { state.stopwatchElapsed = this.getStopwatchElapsed(); state.stopwatchRunning = false; }
    this.refreshTimerWidgets();
  }

  resetStopwatch() {
    this.timerState.stopwatchElapsed = 0;
    this.timerState.stopwatchRunning = false;
    this.refreshTimerWidgets();
  }

  setAlarm(time, enabled) {
    this.timerState.alarmTime = time || "";
    this.timerState.alarmEnabled = Boolean(enabled && time);
    this.timerState.alarmTriggered = "";
    this.refreshTimerWidgets();
  }

  playAlarm(label) {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const context = new AudioContext();
      [0, 0.24, 0.48].forEach((offset, index) => {
        const oscillator = context.createOscillator();
        const gain = context.createGain();
        oscillator.type = "sine";
        oscillator.frequency.value = index % 2 ? 880 : 660;
        gain.gain.setValueAtTime(0.0001, context.currentTime + offset);
        gain.gain.exponentialRampToValueAtTime(0.22, context.currentTime + offset + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + offset + 0.18);
        oscillator.connect(gain).connect(context.destination);
        oscillator.start(context.currentTime + offset);
        oscillator.stop(context.currentTime + offset + 0.2);
      });
      window.setTimeout(() => context.close(), 1200);
    } catch (_) {}
    if ("Notification" in window) {
      if (window.Notification.permission === "granted") new window.Notification(label, { body: "Your focus tool has finished." });
      else if (window.Notification.permission === "default") window.Notification.requestPermission();
    }
    new Notice(`${label} — time is up`);
  }

  async openTimerPopout() {
    if (Platform.isMobile) {
      new Notice("The timer stays inside Obsidian on mobile because pop-out windows are not supported.");
      return;
    }
    try {
      const pip = window.documentPictureInPicture?.requestWindow
        ? await window.documentPictureInPicture.requestWindow({ width: 360, height: 300 })
        : window.open("about:blank", "codex-workspace-timer", "popup=yes,width=360,height=300,resizable=yes");
      if (!pip) throw new Error("The pop-out window was blocked.");
      const style = pip.document.createElement("style");
      style.textContent = `body{margin:0;padding:18px;background:#171719;color:#eee;font-family:system-ui,sans-serif}.cw-timer-widget{max-width:420px}.cw-timer-header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}.cw-timer-title h2{margin:4px 0 14px;font-size:18px}.cw-eyebrow{color:#a98cff;font-size:10px;font-weight:700;letter-spacing:.14em}.cw-timer-tabs{display:flex;gap:5px;margin-bottom:14px}.cw-timer-tabs button,.cw-timer-controls button,.cw-timer-secondary{border:1px solid #424247;border-radius:7px;background:#28282d;color:#ddd;padding:7px 10px;cursor:pointer}.cw-timer-tabs button.is-active,.cw-timer-controls .mod-cta{background:#8a6cff;color:white}.cw-timer-display{text-align:center;font:700 48px ui-monospace,monospace;letter-spacing:-.04em}.cw-timer-status{text-align:center;color:#aaa;font-size:12px;margin:5px 0 15px}.cw-timer-controls,.cw-timer-inputs,.cw-alarm-row{display:flex;gap:7px;justify-content:center}.cw-timer-inputs input,.cw-alarm-row input{width:64px;padding:7px;background:#222226;color:#eee;border:1px solid #424247;border-radius:6px}.cw-alarm-row{justify-content:space-between;align-items:center}.cw-alarm-label,.cw-alarm-enable{display:flex;gap:7px;align-items:center;font-size:12px}`;
      pip.document.head.appendChild(style);
      buildTimerWidget(pip.document.body, this, { popout: true, close: () => pip.close() });
      pip.addEventListener(window.documentPictureInPicture?.requestWindow ? "pagehide" : "beforeunload", () => this.refreshTimerWidgets(), { once: true });
      if (!window.documentPictureInPicture?.requestWindow) new Notice("Timer opened in a resizable window. Picture-in-picture pinning is unavailable in this build.");
    } catch (error) { new Notice(`Could not open the timer pop-out: ${error.message}`); }
  }

  getVaultPath() {
    const adapter = this.app.vault.adapter;
    return typeof adapter.getBasePath === "function" ? adapter.getBasePath() : "";
  }

  async openHome() {
    let leaf = this.app.workspace.getLeavesOfType(HOME_VIEW)[0];
    if (!leaf) {
      leaf = this.app.workspace.getLeaf("tab");
      await leaf.setViewState({ type: HOME_VIEW, active: true });
    }
    await this.app.workspace.revealLeaf(leaf);
    if (this.settings.notionAutoSync && this.settings.notionSyncEnabled) this.syncNotionTasks();
  }

  async openCanvasCheckup() {
    // Keep the action single-flight: rapid/re-entrant clicks can otherwise
    // create two tab leaves before Obsidian registers the first view.
    if (this.canvasOpenPromise) return this.canvasOpenPromise;
    this.canvasOpenPromise = (async () => {
      let leaves = this.app.workspace.getLeavesOfType(CANVAS_VIEW);
      let leaf = leaves[0];
      if (!leaf) {
        // Reuse the current workspace leaf. Asking for a "tab" leaf always
        // creates a new tab and is what caused redundant Canvas tabs.
        leaf = this.app.workspace.getLeaf(false);
        await leaf.setViewState({ type: CANVAS_VIEW, active: true });
      }
      // If an earlier race already left redundant views, retain the first
      // registered one and detach the extras before revealing it.
      leaves = this.app.workspace.getLeavesOfType(CANVAS_VIEW);
      for (const extra of leaves.slice(1)) this.app.workspace.detachLeaf(extra);
      await this.app.workspace.revealLeaf(leaf);
    })();
    try {
      await this.canvasOpenPromise;
    } finally {
      this.canvasOpenPromise = null;
    }
  }

  scheduleCanvasSync() {
    if (this.canvasScheduleTimeout) window.clearTimeout(this.canvasScheduleTimeout);
    this.canvasScheduleTimeout = null;
    if (!this.settings?.canvasSyncEnabled) return;
    const now = new Date();
    const hourKey = `${todayKey()}-${String(now.getHours()).padStart(2, "0")}`;
    const resetKey = todayKey();
    const at = new Date(now);
    let action = "reset";
    if (now.getHours() < 6) {
      at.setHours(6, 0, 0, 0);
    } else if (now.getHours() < 8) {
      if (this.settings.canvasLastReset !== resetKey) at.setTime(now.getTime());
      else { action = "sync"; at.setHours(8, 0, 0, 0); }
    } else if (now.getHours() <= 23) {
      action = "sync";
      const lastSync = this.settings.canvasLastSync ? new Date(this.settings.canvasLastSync) : null;
      const syncedThisHour = lastSync && !Number.isNaN(lastSync.getTime()) && lastSync.toDateString() === now.toDateString() && lastSync.getHours() === now.getHours();
      if (!syncedThisHour && this.canvasScheduleAttemptKey !== hourKey) at.setTime(now.getTime());
      else {
        at.setMinutes(0, 0, 0);
        at.setHours(now.getHours() + 1);
        if (at.getHours() === 0) { action = "reset"; at.setHours(6, 0, 0, 0); }
      }
    } else {
      at.setDate(at.getDate() + 1);
      at.setHours(6, 0, 0, 0);
    }
    this.canvasScheduleTimeout = window.setTimeout(async () => {
      if (action === "reset") await this.resetCanvasDailyChanges();
      else { this.canvasScheduleAttemptKey = hourKey; await this.syncCanvasAssignments({ quiet: true }); }
      this.scheduleCanvasSync();
    }, Math.max(250, at.getTime() - Date.now()));
  }

  async ensureVaultFolder(folderPath) {
    const parts = folderPath.split("/"); let current = "";
    for (const part of parts) { current = current ? `${current}/${part}` : part; if (!this.app.vault.getAbstractFileByPath(current)) await this.app.vault.createFolder(current); }
  }

  async readCanvasData() {
    const file = this.app.vault.getAbstractFileByPath(CANVAS_DATA_PATH);
    if (!file) return { assignments: [], changes: [] };
    try { return JSON.parse(await this.app.vault.read(file)); }
    catch (_) { return { assignments: [], changes: [], error: "The cached Canvas data could not be read." }; }
  }

  formatCanvasDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value || "");
    return date.toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  }

  canvasPlainText(html) {
    if (!html) return "";
    const doc = new DOMParser().parseFromString(String(html), "text/html");
    return (doc.body?.innerText || doc.body?.textContent || "").replace(/\s+/g, " ").trim();
  }

  async canvasRequest(endpoint) {
    if (!this.settings.canvasToken) throw new Error("Add a Canvas access token in Codex Workspace settings first.");
    const base = (this.settings.canvasBaseUrl || DEFAULT_SETTINGS.canvasBaseUrl).replace(/\/$/, "");
    const response = await requestUrl({ url: `${base}/api/v1/${endpoint}`, method: "GET", headers: { Authorization: `Bearer ${this.settings.canvasToken}` }, throw: false });
    if (response.status < 200 || response.status >= 300) {
      if (response.status === 401 || response.status === 403) throw new Error("Canvas sign-in or access token is no longer valid.");
      throw new Error(response.json?.message || `Canvas request failed (${response.status}).`);
    }
    return response.json;
  }

  canvasSummary(assignments, changes) {
    const now = Date.now();
    const pending = assignments.filter((item) => item.bucket === "pending");
    const overdue = pending.filter((item) => item.dueAt && new Date(item.dueAt).getTime() < now);
    const next = pending.filter((item) => item.dueAt && new Date(item.dueAt).getTime() >= now).sort((a, b) => new Date(a.dueAt).getTime() - new Date(b.dueAt).getTime())[0];
    const pieces = [];
    if (overdue.length) pieces.push(`${overdue.length} assignment${overdue.length === 1 ? " is" : "s are"} past due.`);
    if (next) pieces.push(`Next due: ${next.name} for ${next.course}${next.dueAt ? ` on ${this.formatCanvasDate(next.dueAt)}` : ""}.`);
    if (changes.length) pieces.push(`${changes.length} new or changed assignment${changes.length === 1 ? "" : "s"} in this check.`);
    if (!pieces.length) pieces.push(pending.length ? `${pending.length} pending assignment${pending.length === 1 ? "" : "s"}; nothing due immediately.` : "No pending assignments are currently cached.");
    return pieces.join(" ");
  }

  async writeCanvasNote(data) {
    const summaryText = data.summary || "";
    const all = Array.isArray(data.assignments) ? data.assignments : [];
    const buckets = { pending: all.filter((item) => item.bucket === "pending"), submitted: all.filter((item) => item.bucket === "submitted"), graded: all.filter((item) => item.bucket === "graded") };
    const lines = ["---", "cssclasses:", "  - canvas-checkup-note", "---", "", "# Canvas Checkup", "", `> [!info] Last checked ${data.updatedAt ? this.formatCanvasDate(data.updatedAt) : "not yet"}. Obsidian checks Canvas hourly from 8 AM through 11 PM and resets its change tracker at 6 AM.`, "", summaryText ? `## Check status\n\n${summaryText}\n` : ""];
    for (const [bucket, label] of [["pending", "Pending assignments"], ["submitted", "Submitted assignments"], ["graded", "Graded assignments"]]) {
      lines.push(`## ${label}`, "");
      if (!buckets[bucket].length) lines.push(`No ${bucket} assignments are currently cached.`, "");
      for (const item of buckets[bucket]) lines.push(`### ${item.name}`, "", `- **Class:** ${item.course || "Not listed"}`, `- **Due:** ${item.dueAt ? this.formatCanvasDate(item.dueAt) : "No due date"}`, `- **Points:** ${item.points == null ? "Not listed" : item.points}`, `- **Status:** ${item.status || "Not submitted"}`, `- **Canvas:** ${item.url || "Link not available"}`, "", "**Directions**", "", item.directions || "No written directions were included on Canvas.", "");
    }
    const content = lines.filter((line, index) => line !== "" || lines[index - 1] !== "").join("\n").trim() + "\n";
    const existing = this.app.vault.getAbstractFileByPath(CANVAS_NOTE_PATH);
    if (existing) await this.app.vault.modify(existing, content); else await this.app.vault.create(CANVAS_NOTE_PATH, content);
  }

  async syncCanvasAssignments(options = {}) {
    if (!this.settings.canvasSyncEnabled && !options.quiet) new Notice("Enable Canvas checks in Codex Workspace settings first.");
    if (!this.settings.canvasSyncEnabled) return;
    const previous = await this.readCanvasData();
    try {
      const courses = await this.canvasRequest("courses?enrollment_state=active&state[]=available&include[]=term&per_page=100");
      const now = Date.now(); const assignments = [];
      for (const course of courses) {
        if (!course?.id || course.access_restricted_by_date) continue;
        let items = [];
        try { items = await this.canvasRequest(`courses/${course.id}/assignments?include[]=submission&order_by=due_at&per_page=100`); } catch (_) { continue; }
        for (const item of items) {
          const due = item.due_at ? new Date(item.due_at).getTime() : null; const submission = item.submission || {};
          const workflow = submission.workflow_state || "unsubmitted";
          const isGraded = workflow === "graded" || submission.excused === true;
          const isSubmitted = !isGraded && (workflow === "submitted" || workflow === "pending_review" || Boolean(submission.submitted_at));
          if (!item.published) continue;
          const bucket = isGraded ? "graded" : isSubmitted ? "submitted" : "pending";
          const status = isGraded ? (submission.excused ? "Excused" : "Graded") : isSubmitted ? "Submitted; awaiting grade" : due && due < now ? "Past due" : "Not submitted";
          assignments.push({ id: String(item.id), courseId: String(course.id), name: item.name || "Untitled assignment", course: course.name || course.course_code || "Course not listed", dueAt: item.due_at || null, points: item.points_possible ?? null, bucket, status, submittedAt: submission.submitted_at || null, gradedAt: submission.graded_at || null, directions: this.canvasPlainText(item.description), url: item.html_url || "", updatedAt: item.updated_at || "" });
        }
      }
      assignments.sort((a, b) => {
        const order = { pending: 0, submitted: 1, graded: 2 };
        const bucketOrder = (order[a.bucket] ?? 3) - (order[b.bucket] ?? 3);
        if (bucketOrder) return bucketOrder;
        if (a.bucket === "pending") return (a.dueAt ? new Date(a.dueAt).getTime() : Number.MAX_SAFE_INTEGER) - (b.dueAt ? new Date(b.dueAt).getTime() : Number.MAX_SAFE_INTEGER);
        return String(b.submittedAt || b.gradedAt || b.dueAt || "").localeCompare(String(a.submittedAt || a.gradedAt || a.dueAt || ""));
      });
      const priorById = new Map((previous.assignments || []).map((item) => [String(item.id), item])); const changes = [];
      for (const item of assignments) { const old = priorById.get(String(item.id)); if (!old) changes.push({ type: "new", id: item.id, name: item.name, course: item.course }); else if (["name", "dueAt", "points", "directions", "status", "bucket", "gradedAt"].some((key) => JSON.stringify(old[key]) !== JSON.stringify(item[key]))) changes.push({ type: "changed", id: item.id, name: item.name, course: item.course }); }
      const data = { updatedAt: new Date().toISOString(), assignments, changes, summary: this.canvasSummary(assignments, changes), error: "" };
      await this.ensureVaultFolder("Machine/Canvas Checkup");
      const json = JSON.stringify(data, null, 2) + "\n"; const cache = this.app.vault.getAbstractFileByPath(CANVAS_DATA_PATH);
      if (cache) await this.app.vault.modify(cache, json); else await this.app.vault.create(CANVAS_DATA_PATH, json);
      await this.writeCanvasNote(data); this.settings.canvasLastSync = data.updatedAt; await this.savePluginData();
      if (changes.length) { new Notice(`Canvas Checkup found ${changes.length} new or changed assignment${changes.length === 1 ? "" : "s"}.`); if ("Notification" in window && window.Notification.permission === "granted") new window.Notification("Canvas Checkup", { body: `${changes.length} assignment${changes.length === 1 ? "" : "s"} changed.` }); }
      else if (!options.quiet) new Notice(`Canvas Checkup is current: ${assignments.length} ongoing assignment${assignments.length === 1 ? "" : "s"}.`);
      for (const leaf of this.app.workspace.getLeavesOfType(CANVAS_VIEW)) leaf.view.render();
    } catch (error) {
      await this.ensureVaultFolder("Machine/Canvas Checkup");
      const data = { ...previous, updatedAt: new Date().toISOString(), error: error.message, changes: [] }; const json = JSON.stringify(data, null, 2) + "\n"; const cache = this.app.vault.getAbstractFileByPath(CANVAS_DATA_PATH);
      if (cache) await this.app.vault.modify(cache, json); else await this.app.vault.create(CANVAS_DATA_PATH, json);
      if (!options.quiet) new Notice(`Canvas Checkup failed: ${error.message}`);
      for (const leaf of this.app.workspace.getLeavesOfType(CANVAS_VIEW)) leaf.view.render();
    }
  }

  async resetCanvasDailyChanges() {
    const resetKey = todayKey();
    if (this.settings.canvasLastReset === resetKey) return;
    const previous = await this.readCanvasData();
    const data = { ...previous, changes: [], dailyResetAt: new Date().toISOString(), summary: this.canvasSummary(previous.assignments || [], []), error: previous.error || "" };
    await this.ensureVaultFolder("Machine/Canvas Checkup");
    const json = JSON.stringify(data, null, 2) + "\n";
    const cache = this.app.vault.getAbstractFileByPath(CANVAS_DATA_PATH);
    if (cache) await this.app.vault.modify(cache, json); else await this.app.vault.create(CANVAS_DATA_PATH, json);
    await this.writeCanvasNote(data);
    this.settings.canvasLastReset = resetKey;
    await this.savePluginData();
    for (const leaf of this.app.workspace.getLeavesOfType(CANVAS_VIEW)) leaf.view.render();
  }

  runHomeCodexRequest(request) {
    return new Promise(async (resolve, reject) => {
      let pages;
      try {
        const query = await this.notionRequest("POST", `databases/${this.settings.notionDatabaseId}/query`, { page_size: 100 });
        pages = (query.results || []).map((page) => ({ id: page.id, name: this.notionText(page.properties, "Name") || this.notionText(page.properties, "Task"), status: this.notionSelect(page.properties, "Status"), due: this.notionDate(page.properties, "Due") }));
      } catch (error) { reject(error); return; }
      const directWorkingDate = request.match(/^\s*(?:move|set|change)\s+(.+?)\s+(?:working\s+date|work\s+date|date\s+(?:i am\s+)?working\s+on)\s+to\s+(today|tomorrow|\d{4}-\d{2}-\d{2})/i) || request.match(/^\s*move\s+(.+?)\s+to\s+(today|tomorrow|\d{4}-\d{2}-\d{2})/i);
      if (directWorkingDate) {
        const target = pages.find((page) => page.name?.toLowerCase() === directWorkingDate[1].trim().toLowerCase()) || pages.find((page) => page.name?.toLowerCase().includes(directWorkingDate[1].trim().toLowerCase()));
        if (!target) { resolve(`I could not find the task “${directWorkingDate[1].trim()}”.`); return; }
        const dateProperty = await this.notionPropertyName("date", ["Work Date", "Working Date", "Date"]);
        if (!dateProperty || /due|deadline/i.test(dateProperty)) { resolve("I could not find a separate working-date property in the Notion task database; I did not change the due date."); return; }
        const base = new Date();
        if (directWorkingDate[2].toLowerCase() === "tomorrow") base.setDate(base.getDate() + 1);
        const workingDate = directWorkingDate[2].match(/^\d{4}-\d{2}-\d{2}$/) ? directWorkingDate[2] : `${base.getFullYear()}-${String(base.getMonth() + 1).padStart(2, "0")}-${String(base.getDate()).padStart(2, "0")}`;
        await this.notionRequest("PATCH", `pages/${target.id}`, { properties: { [dateProperty]: { date: { start: workingDate } } } });
        const verified = await this.notionRequest("GET", `pages/${target.id}`);
        const verifiedDate = this.notionDate(verified.properties, dateProperty);
        if (verifiedDate !== workingDate) { resolve(`Notion did not confirm the working-date update. Property used: ${dateProperty}.`); return; }
        const mirror = this.app.vault.getMarkdownFiles().find((file) => file.path.startsWith("Tasks/Notion Tasks/") && file.path.includes(target.id.slice(0, 8)));
        if (mirror) {
          const mirrorContent = await this.app.vault.read(mirror);
          const updatedMirror = /^working_date:/m.test(mirrorContent) ? mirrorContent.replace(/^working_date:.*$/m, `working_date: ${workingDate}`) : mirrorContent.replace(/^due:.*$/m, `$&\nworking_date: ${workingDate}`);
          await this.app.vault.modify(mirror, updatedMirror);
        }
        this.refreshNotionEmbed();
        resolve(`Updated ${target.name} — working date: ${workingDate} (${dateProperty}).`);
        return;
      }
      if (Platform.isMobile || !spawn) {
        reject(new Error("This free-form schedule request needs the desktop Codex CLI. Direct requests such as “move Physics to tomorrow” still work on mobile."));
        return;
      }
      const executable = this.settings.codexPath || "codex";
      const prompt = `You are a schedule command parser. Today is ${todayKey()}. Do not use tools and do not modify files. Convert the user's request into exactly one JSON object and no other text. Resolve relative dates such as tomorrow using today's date. Permanent command rules: every request using “move” refers only to the date the user will work on, never the due date. Supported edits are task name, description, working_date, priority, and completion status. The task's working date and due date are separate; never infer or edit due from “move”. Allowed output shapes: {"action":"update","task":"exact task name","working_date":"YYYY-MM-DD"}, {"action":"update","task":"exact task name","name":"new name"}, {"action":"update","task":"exact task name","description":"new description"}, {"action":"update","task":"exact task name","priority":"High"}, {"action":"update","task":"exact task name","status":"Done"}, or {"action":"clarify","message":"short question"}. Only choose a task from this list: ${JSON.stringify(pages)}. User request: ${request}`;
      const child = spawn(executable, ["exec", "--json", "--skip-git-repo-check", "--color", "never", "--cd", this.getVaultPath(), "--sandbox", "workspace-write", "--model", this.settings.homeRequestModel || "gpt-5.6-luna", "-c", "model_reasoning_effort=low", "-"], { cwd: this.getVaultPath(), windowsHide: true, shell: false, env: { ...process.env, NO_COLOR: "1" } });
      let output = "", jsonBuffer = "", errorOutput = "", finalAnswer = "";
      child.stdout.setEncoding("utf8"); child.stderr.setEncoding("utf8");
      child.stdout.on("data", (chunk) => { output += chunk; jsonBuffer += chunk; const lines = jsonBuffer.split(/\r?\n/); jsonBuffer = lines.pop() || ""; for (const line of lines) { try { const event = JSON.parse(line); if (event.type === "item.completed" && event.item?.type === "agent_message") finalAnswer = event.item.text || finalAnswer; } catch (_) {} } });
      child.stderr.on("data", (chunk) => { errorOutput += chunk; });
      child.on("error", reject);
      child.on("close", async (code) => {
        if (code !== 0) { reject(new Error(errorOutput.trim() || output.trim().split(/\r?\n/).slice(-3).join("\n") || `Process exited with code ${code}`)); return; }
        try {
          const match = (finalAnswer || output).match(/\{[\s\S]*\}/);
          const command = match ? JSON.parse(match[0]) : null;
          if (!command || command.action === "clarify") { resolve(command?.message || "I could not determine which task to change."); return; }
          const target = pages.find((page) => page.name && page.name.toLowerCase() === String(command.task || "").toLowerCase()) || pages.find((page) => page.name && page.name.toLowerCase().includes(String(command.task || "").toLowerCase()));
          if (!target) { resolve(`I could not find the task “${command.task || ""}”.`); return; }
          const properties = {};
          if (command.status) properties.Status = { select: { name: command.status } };
          if (command.working_date || command.due) {
            const dateProperty = await this.notionPropertyName("date", command.working_date ? ["Work Date", "Working Date", "Date"] : ["Due", "Date"]);
            if (!dateProperty) { resolve("I could not find a date property in the Notion task database."); return; }
            properties[dateProperty] = { date: { start: command.working_date || command.due } };
          }
          await this.notionRequest("PATCH", `pages/${target.id}`, { properties });
          this.refreshNotionEmbed();
          resolve(`Updated ${target.name}${command.status ? ` — status: ${command.status}` : ""}${command.working_date ? ` — working date: ${command.working_date}` : ""}${command.due ? ` — due: ${command.due}` : ""}.`);
        } catch (error) { reject(error); }
      });
      child.stdin.end(prompt, "utf8");
    });
  }

  async openNewChat() {
    const chatId = makeId();
    this.ensureChat(chatId);
    const leaf = this.app.workspace.getLeaf("tab");
    await leaf.setViewState({ type: CHAT_VIEW, state: { chatId }, active: true });
    await this.app.workspace.revealLeaf(leaf);
  }

  refreshNotionEmbed() {
    const iframe = document.querySelector(".cw-notion-embed");
    if (!iframe) return;
    const base = this.settings.notionEmbedUrl || DEFAULT_SETTINGS.notionEmbedUrl;
    iframe.src = `${base}${base.includes("?") ? "&" : "?"}refresh=${Date.now()}`;
  }

  openGoogleSearch(query) {
    const url = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
    window.open(url, "_blank");
  }

  openGooglePrompt() {
    this.openHome();
    new Notice("Use the Google search bar on Home or inside a Codex chat tab.");
  }

  openFileSearch() {
    const command = this.app.commands?.executeCommandById;
    if (command) {
      command.call(this.app.commands, "file-search:open");
      return;
    }
    new Notice("File search is unavailable. Use Obsidian's file search command.");
  }

  async openVaultFile(filePath) {
    const file = this.app.vault.getAbstractFileByPath(filePath);
    if (file) return this.openFile(file);
    new Notice(`File not found: ${filePath}`);
  }

  async openFile(file) {
    const leaf = this.app.workspace.getLeaf("tab");
    await leaf.openFile(file);
    await this.app.workspace.revealLeaf(leaf);
  }

  async openTodayNote() {
    const date = todayKey();
    const path = `Daily Notes/${date}.md`;
    let file = this.app.vault.getAbstractFileByPath(path);
    if (!file) {
      const template = this.app.vault.getAbstractFileByPath("Templates/Daily Note.md");
      let content = template ? await this.app.vault.read(template) : `# ${date}\n\n## Focus\n\n## Tasks\n- [ ] \n\n## Notes\n`;
      content = content.replaceAll("{{date}}", date).replaceAll("{{long-date}}", new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric", year: "numeric" }));
      file = await this.app.vault.create(path, content);
    }
    await this.openFile(file);
  }

  async collectTasks(limit = 12) {
    const results = [];
    const files = this.app.vault.getMarkdownFiles().filter((file) => !/^(Templates|Machine|System|Sample Obsidian Vault)\//.test(file.path));
    for (const file of files) {
      if (results.length >= limit) break;
      const content = await this.app.vault.cachedRead(file);
      const lines = content.split(/\r?\n/);
      for (const line of lines) {
        const match = line.match(/^\s*[-*]\s+\[ \]\s+(.+)/);
        if (match) {
          const visibleText = match[1].replace(/\s*<!--\s*notion:[^>]+-->\s*/i, "").trim();
          results.push({ text: visibleText, file });
        }
        if (results.length >= limit) break;
      }
    }
    return results;
  }

  extractNotionId(value) {
    const input = String(value || "").trim();
    const hyphenated = input.match(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/i);
    if (hyphenated) return hyphenated[0];
    const compact = input.match(/[a-f0-9]{32}/i);
    return compact ? compact[0] : input;
  }

  async notionRequest(method, endpoint, body) {
    if (!this.settings.notionToken || !this.settings.notionDatabaseId) throw new Error("Set the Notion token and task database ID in Codex Workspace settings first.");
    const response = await requestUrl({
      url: `https://api.notion.com/v1/${endpoint}`,
      method,
      headers: { "Authorization": `Bearer ${this.settings.notionToken}`, "Notion-Version": "2022-06-28", "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      throw: false
    });
    const payload = response.json;
    if (response.status < 200 || response.status >= 300) throw new Error(payload.message || `Notion request failed (${response.status})`);
    return payload;
  }

  notionText(properties, name) {
    const property = properties?.[name];
    return property?.title?.[0]?.plain_text || property?.rich_text?.[0]?.plain_text || "";
  }

  notionDate(properties, name) {
    if (properties?.[name]?.date) return properties[name].date.start || "";
    const fallback = Object.values(properties || {}).find((property) => property?.type === "date" && property.date);
    return fallback?.date?.start || "";
  }

  async notionPropertyName(type, preferred = []) {
    const database = await this.notionRequest("GET", `databases/${this.settings.notionDatabaseId}`);
    const properties = database.properties || {};
    for (const name of preferred) {
      const match = Object.keys(properties).find((propertyName) => propertyName.toLowerCase() === name.toLowerCase() && properties[propertyName]?.type === type);
      if (match) return match;
    }
    if (type === "date") {
      const planningDate = Object.keys(properties).find((name) => properties[name]?.type === "date" && !/due|deadline/i.test(name));
      if (planningDate) return planningDate;
    }
    return Object.keys(properties).find((name) => properties[name]?.type === type) || null;
  }

  notionSelect(properties, name) {
    return properties?.[name]?.select?.name || "";
  }

  async syncNotionTasks() {
    if (!this.settings.notionSyncEnabled) { new Notice("Enable Notion task sync in Codex Workspace settings first."); return; }
    try {
      const query = await this.notionRequest("POST", `databases/${this.settings.notionDatabaseId}/query`, { page_size: 100 });
      const pages = (query.results || []).filter((page) => this.notionSelect(page.properties, "Status").toLowerCase() !== "done");
      const folderPath = "Tasks/Notion Tasks";
      if (!this.app.vault.getAbstractFileByPath(folderPath)) await this.app.vault.createFolder(folderPath);
      for (const page of pages) {
        const text = this.notionText(page.properties, "Name") || this.notionText(page.properties, "Task") || "Untitled task";
        const due = this.notionDate(page.properties, "Due");
        const priority = this.notionSelect(page.properties, "Priority");
        const safeName = text.replace(/[\\/:*?"<>|]/g, "-").replace(/\s+/g, " ").trim().slice(0, 90) || "Untitled task";
        const filePath = `${folderPath}/${safeName} - ${page.id.slice(0, 8)}.md`;
        const status = this.notionSelect(page.properties, "Status") || "Not started";
        const checked = status.toLowerCase() === "done" ? "x" : " ";
        const content = [
          "---",
          `notion_id: ${page.id}`,
          `status: ${status}`,
          `due: ${due || ""}`,
          `priority: ${priority || ""}`,
          "---",
          "",
          `# ${text}`,
          "",
          `- [${checked}] ${text}${priority ? ` - ${priority}` : ""} <!-- notion:${page.id} -->`,
          "",
          "## Notes",
          "",
          "## Reminders",
          ""
        ].join("\n");
        // Match by the stable Notion ID first so renaming a task renames its
        // existing Markdown file instead of leaving the old title orphaned.
        const existingByPath = this.app.vault.getAbstractFileByPath(filePath);
        let existingById = null;
        for (const file of this.app.vault.getMarkdownFiles()) {
          if (!file.path.startsWith(`${folderPath}/`) || file.path === filePath) continue;
          const fileText = await this.app.vault.cachedRead(file);
          if (new RegExp(`^notion_id:\\s*${page.id.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\$&")}\\s*$`, "mi").test(fileText)) {
            existingById = file;
            break;
          }
        }
        let existing = existingByPath || existingById;
        if (existing && existing.path !== filePath) {
          const target = this.app.vault.getAbstractFileByPath(filePath);
          if (!target) {
            await this.app.vault.rename(existing, filePath);
            existing = this.app.vault.getAbstractFileByPath(filePath);
          }
        }
        if (existing) await this.app.vault.modify(existing, content);
        else await this.app.vault.create(filePath, content);
      }
      this.settings.notionLastSync = new Date().toISOString();
      await this.savePluginData();
      this.refreshNotionEmbed();
      new Notice(`Synced ${pages.length} open Notion task${pages.length === 1 ? "" : "s"}.`);
    } catch (error) {
      new Notice(`Notion sync failed: ${error.message}`);
    }
  }

  async pushNotionTaskStatus() {
    if (!this.settings.notionSyncEnabled) { new Notice("Enable Notion task sync in Codex Workspace settings first."); return; }
    try {
      const files = this.app.vault.getMarkdownFiles().filter((file) => file.path.startsWith("Tasks/Notion Tasks/"));
      if (!files.length) { new Notice("Sync Notion tasks first."); return; }
      let changed = 0;
      for (const file of files) {
        const content = await this.app.vault.read(file);
        const match = content.match(/^\s*-\s+\[([ xX])\]\s+.*<!--\s*notion:([^ >]+)\s*-->/m);
        if (!match) continue;
        const status = match[1].toLowerCase() === "x" ? "Done" : "Not started";
        try {
          await this.notionRequest("PATCH", `pages/${match[2]}`, { properties: { Status: { select: { name: status } } } });
          changed++;
        } catch (error) {
          if (!/property|status/i.test(error.message)) throw error;
        }
      }
      new Notice(`Updated ${changed} Notion task status${changed === 1 ? "" : "es"}.`);
      await this.syncNotionTasks();
    } catch (error) {
      new Notice(`Notion status push failed: ${error.message}`);
    }
  }

  getRecentNotes(limit = 10) {
    return this.app.vault.getMarkdownFiles()
      .filter((file) => !/^(Templates|Machine|System|Sample Obsidian Vault)\//.test(file.path))
      .sort((a, b) => b.stat.mtime - a.stat.mtime)
      .slice(0, limit);
  }
};
