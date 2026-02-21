# Claude Code Session Continuity Protocol

## Session Handoff System

This repo uses `docs/session-logs/` as the **central bridge** between all Claude Code environments (desktop VS Code, web, CLI). Every session must read and write to this location.

## On Session Start — READ First

1. Read `docs/session-logs/LATEST.md` to get the most recent session state
2. Read any file in `docs/session-logs/` dated today (`YYYY-MM-DD-*.md`)
3. Acknowledge what was accomplished and what is pending before doing new work

## On Session End — WRITE Before Closing

Before ending any session, generate and commit a session log to `docs/session-logs/` using the format below.

### File Naming Convention

```
docs/session-logs/YYYY-MM-DD-HHmm-{environment}.md
```

Examples:
- `2026-02-21-1430-vscode.md`
- `2026-02-21-1630-web.md`
- `2026-02-21-1800-cli.md`

### Required Session Log Format

```markdown
# Session Log — {YYYY-MM-DD HH:mm} — {environment}

## Environment
- **Platform**: {VS Code / Web / CLI}
- **Branch**: {current branch}
- **Session ID**: {if available}

## Work Completed
- [ item 1 ]
- [ item 2 ]

## External Actions (Outside This Repo)
### Microsoft Teams
- Channels created/modified: {list}
- Protocols established: {list}
- Key decisions: {list}

### Wix (MCP Server)
- Site changes: {list}
- Pages created/modified: {list}
- Automations configured: {list}

### Azure / SharePoint
- Resources provisioned: {list}
- Sites/lists modified: {list}

### Other Integrations
- {service}: {actions taken}

## Files Modified
- {path}: {description of change}

## Active Configuration
### MCP Servers Connected
- {server name}: {purpose}

### Tools/Extensions Used
- {tool}: {how it was used}

## Pending / Next Steps
- [ ] {next action 1}
- [ ] {next action 2}

## Decisions & Context
- {key decision or context the next session needs to know}
```

## Also Update LATEST.md

After writing the dated log, **always overwrite** `docs/session-logs/LATEST.md` with the same content. This ensures any new session can instantly find the current state without searching.

## Git Workflow for Session Logs

```bash
git add docs/session-logs/
git commit -m "session-log: {YYYY-MM-DD HH:mm} {environment} — {brief summary}"
git push -u origin {current-branch}
```

## STANDING DIRECTIVES — ALWAYS Execute

### 1. Teams Operations Channel — Mandatory Post

**ALWAYS** send session logs and significant work summaries to the **Operations Channel** in Microsoft Teams. This is non-negotiable and applies to every session, every environment.

**When to post:**
- At the end of every session (alongside writing the session log file)
- When any significant milestone, decision, or deliverable is completed
- When any external integration action is taken (Wix, Azure, SharePoint, etc.)

**What to post:**
- The full session log content (same content written to `docs/session-logs/`)
- Use formatted markdown for readability in Teams
- Tag it with the environment and branch for traceability

**How to post (by environment):**
- **VS Code (with Teams MCP):** Use the Microsoft Teams MCP server to post directly to the Operations Channel
- **Web / CLI (no MCP):** Generate the Teams message content and instruct the user to post it, OR queue it in `docs/session-logs/PENDING-TEAMS-POST.md` for the next MCP-enabled session to send

**Format for Teams post:**
```
📋 Session Log — {YYYY-MM-DD HH:mm} — {environment}
🔀 Branch: {branch}

✅ Work Completed:
{bulleted list}

🔧 External Actions:
{bulleted list of Teams/Wix/Azure/SharePoint actions}

📁 Files Modified:
{bulleted list}

⏭️ Next Steps:
{bulleted list}

📌 Key Decisions:
{bulleted list}
```

### 2. Record Keeping

All session logs serve as the permanent operational record. Nothing gets lost between sessions. The Operations Channel in Teams is the team-visible mirror of `docs/session-logs/`.

---

## Repo Structure Reference

```
RS-Co.Enterprise/
├── CLAUDE.md                              ← YOU ARE HERE (session protocol)
├── CLAUDE-AGENT-DIRECTIVES.md             ← Agent operational directives
├── ENTERPRISE-IMPLEMENTATION-ROADMAP.md   ← Project phases & timeline
├── README.md                              ← Enterprise architecture reference
├── docs/
│   ├── RS-Enterprise-Architecture.html
│   ├── architecture-pages/
│   └── session-logs/                      ← CENTRAL SESSION BRIDGE
│       ├── LATEST.md                      ← Always current state
│       └── YYYY-MM-DD-HHmm-{env}.md      ← Dated logs
└── .gitignore
```
