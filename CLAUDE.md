# CLAUDE.md — RS&Co. Enterprise Project Configuration

## Project Overview
RS&Co. Centralized Enterprise Operations Hub. This repository contains enterprise architecture documentation, AI agent configurations, CI/CD pipeline definitions, and automation workflows for RS&Company's real estate investment and development platform.

## Repository Structure
```
RSCoEnterprise/
├── CLAUDE.md                              # This file — Claude Code project config
├── CLAUDE-AGENT-DIRECTIVES.md             # Operational directives for all AI agents
├── ENTERPRISE-IMPLEMENTATION-ROADMAP.md   # WBS with phases, tasks, RACI, status
├── README.md                              # Project overview and infrastructure
├── docs/
│   ├── REQUIREMENTS-SPECIFICATION.md      # Formal requirements (Task 1.1.8)
│   ├── RS-Enterprise-Architecture.html    # Main architecture document
│   └── architecture-pages/
│       ├── 00-index.html                  # Architecture site home
│       ├── 01-system-architecture.html    # 7-layer technology stack
│       ├── 02-agentic-staff.html          # 10 AI agent roles
│       ├── 03-data-flows.html             # 6 primary data flows
│       ├── 04-executive-dashboard.html    # 9-panel Power BI dashboard
│       ├── 05-operating-model.html        # Governance and operations
│       └── 06-decommission-plan.html      # Legacy system retirement
└── .github/
    ├── pull_request_template.md           # PR template
    └── ISSUE_TEMPLATE/
        ├── feature-request.md             # Feature request template
        ├── bug-report.md                  # Bug report template
        └── task.md                        # Task/WBS item template
```

## Key Conventions

### Agent Deconfliction Protocol
Each AI agent has a non-overlapping domain. Claude Code (this agent) owns:
- Codebase development and deployment
- Azure DevOps pipeline configuration
- SharePoint/M365 administration scripts
- GitHub repo management and CI/CD
- Wix Velo backend module deployment

Do NOT perform tasks owned by other agents (marketing content, CRM configuration, investor communications) unless explicitly directed.

### Systems of Record
- **Deal Data:** Wix CMS (DealRoomDeals collection)
- **Documents:** SharePoint (RS Enterprise hub)
- **Contacts/Pipeline:** Dynamics 365 CRM
- **Financials:** Business Central
- **Source Code:** GitHub (this repo)

### File Naming Convention
All files follow: `[Entity]-[Category]-[Description]-[Version].[ext]`

### Branch Strategy
- `main` — production-ready documentation and configurations
- `claude/*` — Claude Code working branches
- Feature branches follow: `feature/{description}`
- Hotfix branches follow: `hotfix/{description}`

### Commit Message Format
```
[Phase X.Y.Z] Brief description of change

- Detail 1
- Detail 2

WBS Ref: Task X.Y.Z
```

### Current Project Phase
Phase 1: Planning and Analysis (Feb 20 - Mar 12, 2026)
- Task 1.1 (Requirement Gathering): IN PROGRESS
- See ENTERPRISE-IMPLEMENTATION-ROADMAP.md for full WBS

## Technology Stack
- **CMS:** Wix (Velo backend, CMS collections, Members Portal)
- **Enterprise:** Microsoft 365 (SharePoint, D365, Business Central, Power BI, Power Automate, Teams)
- **AI:** Claude (Anthropic), OpenAI GPT-4, Copilot Studio, Azure OpenAI
- **DevOps:** GitHub, Azure DevOps, VS Code
- **Integration:** MCP Servers (Wix + Tools)

## Team
- Brandon Riddick-Seals (brandon@riddickseals.com) — Project Owner
- Bryson Riddick-Seals (bryson@riddickseals.com)
- Chana Austin (chana@riddickseals.com)
- LeRonne Riddick-Seals (leronne@riddickseals.com)

## External Resources
- SharePoint Hub: https://rslg.sharepoint.com/sites/RSEnterprise
- Azure DevOps: https://dev.azure.com/riddickseals/
- Tenant: RS&Company (riddickseals.com)
