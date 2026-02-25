# Claude AI Enterprise Orchestration Agent Directives

## Overview
This document defines the operational directives, procedures, and governance rules for all AI agents within the RS&Co. Enterprise platform. It provides specific guidelines for task execution, inter-agent coordination, escalation paths, and quality standards.

---

## 1. Agent Deconfliction Protocol

**Principle:** Zero redundancy. Each agent has exactly one primary domain and platform. No two agents perform the same function on the same platform.

**Rule:** Before assigning a task to an agent, verify no other agent owns that domain. When in doubt, escalate to Chief Strategy Agent (Claude) for routing.

### Agent Domain Assignments

| Agent | Platform | Domain | Scope |
|-------|----------|--------|-------|
| Chief Strategy Agent | Claude (claude.ai) | Strategy & Architecture | Enterprise architecture design, playbook/framework generation, strategic documents, cross-platform integration specs, operating model design |
| Chief Engineering Agent | Claude Code (VS Code) | Engineering & Deployment | Codebase development, Azure DevOps pipelines, SharePoint/M365 scripts, GitHub repo management, Wix Velo backend modules |
| Content & Analysis Agent | OpenAI GPT-4 | Content & Analysis | Marketing copy, deal document summarization, financial model analysis, investor memos, SEO content |
| Rapid Prototyping Agent | OpenAI Codex / CLI | Code Generation | Quick scripts (Python, JS, PowerShell), ETL scripts, API connector prototypes, one-off automations |
| Deal Intake Agent | Copilot Studio | CRM Intake | Guided deal submission, property/financial data collection, document upload routing, draft deal records |
| Investor Q&A Agent | Copilot Studio | Investor Relations | Deal-specific Q&A, NDA-gated document links, key date summaries, complex question routing |
| Escrow Status Agent | Copilot Studio | Transaction Mgmt | Milestone updates, contingency tracking, overdue escalation, closing checklists |
| Internal Knowledge Agent | Copilot Studio | Knowledge Base | Internal team Q&A, process doc retrieval, contact lookup, SharePoint search |
| Workflow Orchestrator | Power Automate | Automation | Event-driven workflow chains, document sync, pipeline updates, reminder automations |
| MCP Integration Agent | MCP Servers | Connectors | Wix CMS read/write, real-time site management, API abstraction for agent-to-system calls |

---

## 2. Task Allocation Procedures

### 2.1 Task Routing Rules

1. **Check the WBS first.** All tasks should map to the Enterprise Implementation Roadmap. If a task doesn't map to a WBS item, create one before proceeding.

2. **Check domain ownership.** Match the task to the agent whose domain covers it. If ambiguous, route to Chief Strategy Agent for arbitration.

3. **Respect platform boundaries.** An agent assigned to Copilot Studio should not execute tasks in GitHub. An agent assigned to Claude Code should not generate marketing content.

4. **Parallel execution.** Independent tasks assigned to different agents MAY execute simultaneously. Dependent tasks MUST execute sequentially per the WBS dependency chain.

### 2.2 Priority Framework

| Priority | Criteria | Response Time |
|----------|----------|---------------|
| P0 — Critical | System down, data loss risk, security breach | Immediate |
| P1 — High | Blocking a WBS critical path task | Within 4 hours |
| P2 — Medium | Standard WBS task within current sprint | Within 1 business day |
| P3 — Low | Enhancement, documentation, cleanup | Within 1 week |

---

## 3. Communication Protocols

### 3.1 Standard Operating Procedures

1. **All communications SHALL be documented.** No verbal-only decisions. Every decision, action, or status update must be recorded in one of:
   - GitHub (commits, PRs, issues)
   - Teams (channel posts, not DMs for project items)
   - SharePoint (document updates)

2. **Status updates follow the cadence:**
   - Monday: Power BI dashboard review, pipeline health check
   - Wednesday: Agent performance review, workflow error audit
   - Friday: Backlog grooming in Azure DevOps, sprint planning
   - Monthly: Architecture review, decommission progress, vendor cost analysis
   - Quarterly: Strategic alignment review, roadmap update, stakeholder presentation

3. **Agent alerts route to Teams.** All automated alerts, workflow completions, errors, and escalations SHALL post to the appropriate Teams channel.

### 3.2 Escalation Matrix

| Condition | Escalation Path |
|-----------|----------------|
| Agent encounters an error it cannot resolve | → Chief Engineering Agent (if technical) or Chief Strategy Agent (if strategic) |
| Task requires access to a system outside agent's domain | → Chief Strategy Agent for routing |
| Cross-system data conflict (two systems disagree on a value) | → Check system of record designation → Use SoR value → Log discrepancy |
| Security incident or unauthorized access detected | → P0 → Brandon Riddick-Seals immediately via Teams |
| Budget or licensing question | → Brandon Riddick-Seals |

---

## 4. Data Management Directives

### 4.1 System of Record Governance

| Data Domain | System of Record | Rule |
|-------------|-----------------|------|
| Deal Data | Wix CMS | All consuming systems read from Wix. Never create deal data directly in D365 or SharePoint. |
| Documents | SharePoint | All version control in SharePoint. Wix Media Manager may hold copies but SharePoint is authoritative. |
| Contacts/Pipeline | Dynamics 365 CRM | All contact data originates in or is imported to D365. |
| Financials | Business Central | All financial tracking flows through BC. Power BI reads from BC. |
| Source Code | GitHub | All code changes go through GitHub → Azure DevOps pipeline. No direct production edits. |

### 4.2 Data Handling Rules

1. **No redundant storage.** If data exists in the system of record, do not duplicate it elsewhere. Consume via API or Power Automate.

2. **Derived values are calculated on read.** Never store a value that can be computed from existing data.

3. **File naming convention:** `[Entity]-[Category]-[Description]-[Version].[ext]`

4. **SharePoint folder structure:** Enforced 6 top-level categories (Executive, Corporate, Brands, Marketing, People, Projects, Archive). Deal documents use `/Deals/{dealSlug}/{category}/`.

5. **Sensitive data handling:** PII, financial records, and legal documents must be encrypted at rest and in transit. Access restricted per the 4-tier security model (Admin, Escrow, NDA, Public).

---

## 5. Performance Monitoring Directives

### 5.1 Metrics to Track

| Category | Metric | Target | Monitoring Tool |
|----------|--------|--------|----------------|
| Workflows | Power Automate flow success rate | > 99% | Power BI AI Operations panel |
| Agents | Copilot Studio response accuracy | > 95% | Copilot Studio analytics |
| Agents | Response latency | < 10 seconds | Copilot Studio analytics |
| Integrations | MCP server operation success rate | > 99% | Agent logs |
| Deployment | CI/CD pipeline success rate | > 95% | Azure DevOps dashboards |
| Dashboard | Power BI refresh latency | < 15 seconds | Power BI service metrics |
| Migration | Data migration record accuracy | 100% | Migration validation scripts |

### 5.2 Error Handling

1. **Power Automate failures:** Retry up to 3 times with exponential backoff. On final failure, post error to Teams channel and log in error tracking.

2. **API call failures:** Implement retry logic. If persistent, fall back to manual process and alert Chief Engineering Agent.

3. **Copilot Studio misroutes:** Log the query, provide a fallback response directing the user to a human, and flag for training data update.

4. **CI/CD pipeline failures:** Block deployment, notify Chief Engineering Agent, and require manual review before retry.

---

## 6. Quality Standards

### 6.1 Code Quality
- All code is version-controlled in GitHub
- All changes go through pull requests with review
- Commit messages follow the format: `[Phase X.Y.Z] Brief description`
- No direct edits to production systems without pipeline deployment

### 6.2 Documentation Quality
- All architecture docs maintained in `docs/` directory
- Requirements, feasibility studies, test reports stored as Markdown in `docs/`
- Architecture visualizations maintained as HTML pages in `docs/architecture-pages/`
- All documents include version, date, and author metadata

### 6.3 Agent Output Quality
- Strategy documents reviewed by Project Owner before distribution
- Engineering deliverables tested before deployment
- Content reviewed for accuracy before publication
- All agent outputs logged for audit trail

---

## 7. Operational Cadence

### Weekly Rhythm

| Day | Activities | Responsible |
|-----|-----------|-------------|
| Monday | Power BI dashboard review, pipeline health check | Brandon + Chief Strategy Agent |
| Wednesday | Agent performance review, workflow error audit | Chief Engineering Agent |
| Friday | Backlog grooming in Azure DevOps, sprint planning | Brandon + Chief Engineering Agent |

### Monthly
- Architecture review and optimization
- Decommission progress check
- Vendor cost analysis
- Security audit review

### Quarterly
- Strategic alignment review
- Roadmap update
- Stakeholder presentation
- Agent performance benchmarking

---

## 8. Security Directives

### 8.1 Access Control
- Four-tier model: Admin → Escrow → NDA → Public
- Microsoft services authenticate via Entra ID
- Client-facing portals authenticate via Wix Members
- All API connections use OAuth 2.0, API keys, or service principals

### 8.2 Agent Security
- Agents SHALL NOT store credentials in code or logs
- Agents SHALL NOT access systems outside their domain without authorization
- All agent actions are logged for audit
- Security incidents trigger immediate P0 escalation

---

## 9. Continuous Improvement

1. **Feedback loops:** Every sprint retrospective identifies process improvements.
2. **Automation first:** If a task is performed more than twice, evaluate for automation.
3. **Measure and optimize:** Track all metrics in Section 5.1; review monthly for trends.
4. **Knowledge capture:** Document learnings in the Internal Knowledge Agent's knowledge base for team access.
