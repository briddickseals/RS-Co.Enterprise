# RS&Co. Enterprise

**RS&Co. Centralized Enterprise Operations Hub**

This repository serves as the central codebase for RS&Co.'s enterprise infrastructure, AI agents, and automation workflows.

## Enterprise Architecture

### Azure / Microsoft 365

| Resource | Details |
|---|---|
| **Tenant** | RS&Company (`riddickseals.com`) |
| **Azure Subscription** | Azure subscription 1 |
| **SharePoint Hub** | [RS Enterprise](https://rslg.sharepoint.com/sites/RSEnterprise) |
| **Azure DevOps** | [riddickseals](https://dev.azure.com/riddickseals/) |

### SharePoint Structure

```
RS Enterprise (Centralized Hub)
├── Executive/           # Executive management, admin, strategy
├── Corporate/           # Legal, Finance, Business Solutions, Innovation
├── Development/         # Development PMO, Planning, Construction Mgmt
├── Projects/            # Active real estate projects
├── Brands/              # ASSET, ADVISORS, ACUMEN, AREAops, PROPEL, etc.
├── Marketing/           # Marketing PMO, Creative Media
├── Ventures/            # Crypto, Imhotep Academy, REIT Fund
├── People/              # DAIP Intern Programs, Team Resources
└── Archive/             # Legacy content
```

### Wix Sites

| Site | Purpose |
|---|---|
| **RS&Co.** | Corporate website |
| **AREAops** | PropTech platform |

### AI Infrastructure

| Service | Status |
|---|---|
| OpenAI API | Configured |
| Anthropic (Claude) | Configured |
| Claude Code | Active |
| Azure OpenAI | Pending deployment |
| Copilot Studio | 2 bots (Real Estate Analyst Pro, AcumenCRE) |

## Team

- Brandon Riddick-Seals (`brandon@riddickseals.com`)
- Bryson Riddick-Seals (`bryson@riddickseals.com`)
- Chana Austin (`chana@riddickseals.com`)
- LeRonne Riddick-Seals (`leronne@riddickseals.com`)

## Getting Started

```bash
# Clone the repository
git clone https://github.com/briddickseals/RS-Co.Enterprise.git
cd RS-Co.Enterprise

# Azure CLI login
az login
az devops configure --defaults organization=https://dev.azure.com/riddickseals/ project="RS Enterprise DevOps"
```

## License

Proprietary - RS&Company
