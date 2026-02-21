# Desktop Claude Code — Session Handoff Prompt

**INSTRUCTIONS**: Copy the entire prompt block below and paste it into your desktop Claude Code (VS Code terminal or CLI) at the END of your working session. This generates the session log, commits it, and pushes it so the web session can pick up where you left off.

---

## THE PROMPT — COPY EVERYTHING BELOW THIS LINE

```
Read the file CLAUDE.md in this repo for the session continuity protocol. Then execute the following:

1. Generate a complete session log for TODAY's work in this environment. Use the exact format specified in CLAUDE.md. Include:

   - Every file you created, modified, or deleted this session
   - Every git operation performed
   - Every external action taken via MCP servers (Wix, Teams, SharePoint, Azure, etc.)
   - Every MCP server that was connected and what was done through it
   - Every Teams channel created, message sent, or protocol established
   - Every Wix page, automation, or site change made
   - All pending/incomplete work and explicit next steps
   - Key decisions, blockers, or context the next session needs

2. Write the session log to: docs/session-logs/{TODAY's DATE in YYYY-MM-DD}-{CURRENT TIME in HHmm}-vscode.md

3. Copy that same content to: docs/session-logs/LATEST.md (overwrite it)

4. Stage, commit, and push:
   git add docs/session-logs/
   git commit -m "session-log: {date} {time} vscode — {one-line summary of today's work}"
   git push -u origin {current branch}

Be thorough. Include EVERYTHING. The next session in a different environment depends entirely on this log to understand what happened and continue the work.
```

---

## QUICK-START VERSION (for fast handoffs)

```
Read CLAUDE.md. Generate a full session log per the protocol. Write it to docs/session-logs/ with today's date-time and environment. Also overwrite docs/session-logs/LATEST.md. Commit and push. Be thorough — capture all work done including MCP actions, Teams, Wix, files changed, and next steps.
```

---

## TO PICK UP IN A NEW SESSION (paste this at session start)

```
Read docs/session-logs/LATEST.md and any session logs from today in docs/session-logs/. Summarize what was accomplished, what is pending, and what I should focus on next. Then proceed with the pending work.
```
