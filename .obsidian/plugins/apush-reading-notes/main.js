const { Plugin, Notice } = require("obsidian");
const { spawn } = require("child_process");
const path = require("path");

const ASSIGNMENTS_PATH = "Machine/Canvas Checkup/assignments.json";
const NOTES_FOLDER = "Anish's Second Brain/Notes/APUSH";
const SKILL_PATH = "Machine/Skills/apush-reading-notes/SKILL.md";
const HISTORY_COURSE = "U.S. History A (AP) - Harrington, J";

module.exports = class ApushReadingNotesPlugin extends Plugin {
  async onload() {
    this.startupTimer = null;
    this.app.workspace.onLayoutReady(() => {
      // Canvas Checkup has its own sync process. Give it a short chance to
      // refresh assignments, then perform exactly one APUSH-reading check for
      // this Obsidian launch. There is intentionally no recurring timer here.
      this.startupTimer = window.setTimeout(() => this.checkOnceAtStartup(), 20000);
    });
  }

  onunload() {
    if (this.startupTimer) window.clearTimeout(this.startupTimer);
  }

  extractPageRange(text) {
    const match = String(text || "").match(/\bp{1,2}\. ?\s*(\d+)\s*[-–—]\s*(\d+)/i)
      || String(text || "").match(/\bread\s+(\d+)\s*[-–—]\s*(\d+)/i);
    if (!match) return null;
    const start = Number(match[1]);
    const end = Number(match[2]);
    return Number.isFinite(start) && Number.isFinite(end) && end >= start ? { start, end } : null;
  }

  async checkOnceAtStartup() {
    try {
      const assignmentsFile = this.app.vault.getAbstractFileByPath(ASSIGNMENTS_PATH);
      if (!assignmentsFile) return;

      const payload = JSON.parse(await this.app.vault.read(assignmentsFile));
      const readings = (payload.assignments || [])
        .filter((assignment) => assignment.course === HISTORY_COURSE)
        .map((assignment) => {
          const combined = `${assignment.name || ""}\n${assignment.directions || ""}`;
          return { ...assignment, range: this.extractPageRange(combined) };
        })
        .filter((assignment) => assignment.range)
        .sort((a, b) => {
          const aDue = a.dueAt ? Date.parse(a.dueAt) : 0;
          const bDue = b.dueAt ? Date.parse(b.dueAt) : 0;
          if (aDue !== bDue) return bDue - aDue;
          return Date.parse(b.updatedAt || 0) - Date.parse(a.updatedAt || 0);
        });

      if (!readings.length) return;
      const latest = readings[0];
      const { start, end } = latest.range;

      const existing = this.app.vault.getMarkdownFiles().some((file) => {
        if (!file.path.startsWith(`${NOTES_FOLDER}/`)) return false;
        const normalized = file.name.replace(/[–—]/g, "-");
        return new RegExp(`(^|\\D)${start}\\s*-\\s*${end}(\\D|$)`).test(normalized);
      });
      if (existing) return;

      await this.runReadingSkill(latest);
    } catch (error) {
      console.error("APUSH startup reading check failed", error);
      new Notice(`APUSH reading check failed: ${error.message}`);
    }
  }

  getVaultPath() {
    if (typeof this.app.vault.adapter.getBasePath === "function") {
      return this.app.vault.adapter.getBasePath();
    }
    return path.dirname(this.app.vault.adapter.getFullPath("AGENTS.md"));
  }

  async runReadingSkill(assignment) {
    const vaultPath = this.getVaultPath();
    const executable = "codex";
    const args = [
      "exec",
      "--json",
      "--skip-git-repo-check",
      "--color", "never",
      "--cd", vaultPath,
      "--sandbox", "workspace-write",
      "-"
    ];

    const prompt = [
      "You are running automatically at Obsidian startup inside this vault.",
      "Read AGENTS.md and then read Machine/Skills/apush-reading-notes/SKILL.md.",
      `Execute that skill for Canvas assignment ID ${assignment.id}.`,
      `The detected assigned page range is pp. ${assignment.range.start}-${assignment.range.end}.`,
      "First verify that matching APUSH notes still do not exist. If they now exist, make no changes and exit.",
      "If notes are missing, use the assignment's current PDF/link and the previous APUSH reading directions, follow the black-text-on-white-only rule, and create the note in the prescribed APUSH Unit + page-range naming scheme.",
      "Do not modify unrelated files."
    ].join("\n");

    await new Promise((resolve, reject) => {
      const child = spawn(executable, args, {
        cwd: vaultPath,
        windowsHide: true,
        shell: false,
        env: { ...process.env }
      });

      let stderr = "";
      child.stderr.on("data", (chunk) => { stderr += String(chunk); });
      child.on("error", reject);
      child.on("close", (code) => {
        if (code === 0) resolve();
        else reject(new Error(stderr.trim() || `Codex exited with code ${code}`));
      });
      child.stdin.write(prompt);
      child.stdin.end();
    });
  }
};
