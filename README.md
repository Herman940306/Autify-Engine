# Autify Engine V1

**Zero-Cloud | Draft-Only | Human-Supervised AI Workflow Assistant for SMBs**

---

## Overview

Autify Engine V1 is a fully local, human-supervised AI workflow assistant designed for small and medium businesses. It processes multiple data sources securely on-premise, generates automated drafts for human approval, and runs deterministic data analysis -- all while enforcing strict auditability via append-only logs.

**No data ever leaves your machine.** Every output is a draft until a human clicks Approve.

---

## Quick Start (Desktop App)

**Double-click the "Autify Engine" shortcut on your Desktop.** That's it.

The launcher automatically starts the backend, dashboard, and opens the app in a browser window without a URL bar (Edge/Chrome app mode).

**Default login:** `admin` / `admin123` (you will be prompted to change the password on first login).

### Manual Start (Alternative)

```powershell
# PowerShell (run from project root)
powershell -ExecutionPolicy Bypass -File launcher\launch.ps1

# With options:
launcher\launch.ps1 -NoBrowser     # Start services only, no browser
launcher\launch.ps1 -Restart       # Kill stale processes and restart
```

### Stop Services

```powershell
powershell -ExecutionPolicy Bypass -File launcher\stop.ps1
```

---

## Prerequisites

| Dependency  | Version   | Install Command                        |
|-------------|-----------|----------------------------------------|
| Python      | 3.11+     | `winget install Python.Python.3.11`    |
| Node.js     | 18+       | `winget install OpenJS.NodeJS.LTS`     |
| Docker      | (optional)| `winget install Docker.DockerDesktop`  |

### First-time Setup

```powershell
# Install Python dependencies
pip install -r requirements.txt

# Install dashboard dependencies
cd dashboard
npm install
cd ..
```

---

## Architecture

```
Autify Engine V1
|
|-- api/                  FastAPI backend (REST API on port 18080)
|   +-- main.py           All endpoints, CORS, Pydantic schemas
|   +-- auth.py           User authentication, login/logout, token management
|   +-- chat.py           Chat bot backend (local LLM only, true data enforcement)
|
|-- analysis/             Deterministic KPI engine
|   +-- engine.py         Sum, mean, min, max, Z-score anomaly detection
|
|-- core/                 Central configuration
|   +-- config.py         Ports, DB path, LLM settings, 10 LLM Laws
|   +-- security.py       Role-based permissions (admin/user), LLM safety rules
|
|-- dashboard/            React 18 + Vite + Tailwind frontend (port 18300)
|   +-- src/App.jsx       Auth-protected router with all page routes
|   +-- src/api.js        API client with bearer token auth
|   +-- src/auth/         Login page, auth context, password change modal
|   +-- src/pages/        Dashboard, Clients, Inputs, Drafts, Chat, Reports, Users, Settings
|   +-- vite.config.js    Dev server + proxy config
|
|-- database/             SQLAlchemy + SQLite (Zero-Cloud)
|   +-- models.py         User, Client (name/surname/address), Input, AnalysisResult, DraftOutput (rejected flag), Log, ChatMessage
|   +-- database.py       Engine + session factory + auto-migration
|
|-- launcher/             Desktop app launcher
|   +-- launch.ps1        Start services + open kiosk browser
|   +-- stop.ps1          Graceful shutdown
|   +-- create-shortcut.ps1  Creates Desktop shortcut
|
|-- license/              Hardware-bound licensing
|   +-- manager.py        SHA-256 fingerprint, activation, reactivation (max 2/yr)
|
|-- llm/                  Template-driven draft generator
|   +-- orchestrator.py   Loads templates, builds drafts, optional LLM enrichment
|
|-- parsers/              Multi-format file ingestor
|   +-- parser.py         CSV, Excel, JSON, TXT, PDF, SQLite -> structured data
|
|-- templates/            6 industry prompt templates (JSON)
|   +-- retail_pos_reporting.json
|   +-- retail_inventory_alert.json
|   +-- workshop_job_scheduling.json
|   +-- workshop_client_notification.json
|   +-- profservices_invoice.json
|   +-- profservices_billing_workflow.json
|
|-- tests/                156 tests (unit, integration, security)
|   +-- unit/             Parser, analysis, schema, auth, clients, chatbot
|   +-- integration/      Full workflow pipeline (incl. rejected drafts)
|   +-- security/         License, Zero-Cloud, draft-only enforcement
|
|-- scripts/              Deployment scripts
|   +-- start.ps1         Interactive PowerShell launcher
|   +-- start.bat         CMD launcher
|
|-- Docker files          Containerized deployment
|   +-- Dockerfile.backend
|   +-- Dockerfile.dashboard
|   +-- docker-compose.yml
|
+-- .env                  Environment variables
+-- requirements.txt      Python dependencies
+-- conftest.py           Pytest path configuration
```

---

## Ports

| Service     | Default Port | Environment Variable |
|-------------|-------------|---------------------|
| Backend API | 18080       | `BACKEND_PORT`      |
| Dashboard   | 18300       | `DASHBOARD_PORT`    |
| Local LLM   | 18434       | `LLM_PORT`          |

All ports are configurable via `.env` or environment variables.

---

## API Endpoints

### Authentication
| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| POST   | `/auth/login`               | Login, returns bearer token    |
| POST   | `/auth/logout`              | Invalidate session token       |
| GET    | `/auth/me`                  | Current user + permissions     |
| POST   | `/auth/register`            | Admin creates new user         |
| POST   | `/auth/change-password`     | User changes own password      |
| GET    | `/auth/users`               | Admin lists all users          |
| DELETE | `/auth/users/{id}`          | Admin deactivates a user       |

### Core Workflow
| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| GET    | `/health`                   | System health + version        |
| GET    | `/clients`                  | List all clients               |
| POST   | `/clients`                  | Create new client              |
| PUT    | `/clients/{id}`             | Update client                  |
| DELETE | `/clients/{id}`             | Archive (soft-delete) client   |
| POST   | `/upload/{client_id}`       | Upload file for processing     |
| GET    | `/analytics`                | All analysis results           |
| GET    | `/analytics/summary`        | Aggregated KPI summary         |
| GET    | `/drafts`                   | List all drafts                |
| POST   | `/drafts/{id}/approve`      | Human-approve a draft          |
| POST   | `/drafts/{id}/reject`       | Human-reject a draft           |
| GET    | `/notifications`            | System notifications           |
| GET    | `/inputs`                   | List uploaded inputs           |
| GET    | `/logs`                     | Append-only audit logs         |

### Chat Bot
| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| POST   | `/chat`                     | Send message to AI assistant   |
| GET    | `/chat/history`             | Retrieve chat history          |
| GET    | `/chat/export`              | Export chat history as JSON    |

### Export & Intelligence
| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| GET    | `/export/analytics/csv`     | Download analytics as CSV      |
| GET    | `/export/drafts/csv`        | Download drafts as CSV         |
| GET    | `/clients/{id}/suggestions` | AI-powered client suggestions  |
| GET    | `/calendar/events`          | Calendar events from drafts    |

### LLM & License
| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| GET    | `/llm/status`               | LLM connection status          |
| GET    | `/llm/templates`            | Available prompt templates     |
| GET    | `/llm/laws`                 | The 10 LLM Laws               |
| POST   | `/activate`                 | Activate license key           |

Interactive API docs: `http://127.0.0.1:18080/docs`

---

## The 10 LLM Laws

1. All outputs are DRAFTS -- never auto-executed.
2. Human approval required before any action.
3. No data leaves the local machine (Zero-Cloud).
4. All inputs are validated and sanitized.
5. Deterministic analysis -- no randomness in KPIs.
6. Append-only audit logs -- immutable history.
7. Hardware-bound licensing -- one device per key.
8. No PII in LLM prompts -- template variables only.
9. True Data Only -- all chat responses from local LLM; failures return errors, never templates.
10. All drafts carry draft_flag=True until human approval.

---

## User Roles & Permissions

| Permission            | Admin | User |
|-----------------------|:-----:|:----:|
| Approve/Reject Drafts |  Yes  |  No  |
| Manage Users          |  Yes  |  No  |
| Delete/Archive Clients|  Yes  |  No  |
| View Audit Logs       |  Yes  |  No  |
| Manage License        |  Yes  |  No  |
| Upload Files          |  Yes  | Yes  |
| View Analytics        |  Yes  | Yes  |
| Chat with AI          |  Yes  | Yes  |
| Manage Clients (CRUD) |  Yes  | Yes  |
| Export Data            |  Yes  | Yes  |

Default admin account: `admin` / `admin123` (force-changed on first login).

---

## Chat Bot

The built-in AI chat assistant connects to a local LLM (Ollama). All chat responses are generated exclusively by the local LLM -- template fallback is **not** used for user-facing output. If the LLM is unavailable, a clear error message is returned.

- **True Data Only**: Every response comes from the local LLM; no mock/placeholder/template content
- **Schema Validation**: Structured outputs (emails, KPIs, drafts) are validated against required schemas
- **Zero-Cloud**: All conversations stay on your machine
- **Draft-Only**: Action requests get safety warnings -- no auto-execution
- **LLM Laws Enforced**: System prompt enforces all 10 laws
- **Topics**: Data analysis, workflow guidance, client management, report interpretation
- **History**: Chat sessions are saved and can be exported as JSON

---

## Testing

```powershell
# Run all 156 tests
python -m pytest tests/ -v

# Run by category
python -m pytest tests/unit/ -v           # 136 unit tests (parser, analysis, schema, auth, clients, chatbot)
python -m pytest tests/integration/ -v    # 10 integration tests (incl. rejected draft filter)
python -m pytest tests/security/ -v       # 10 security tests
```

---

## Docker Deployment

```powershell
# Build and start all services
docker-compose up --build

# Services:
#   backend:   http://localhost:18080
#   dashboard: http://localhost:18300
#   llm:       Ollama on port 18434 (auto-pulls model)
```

---

## Industry Modules

| Module               | Templates                                  |
|----------------------|--------------------------------------------|
| Retail POS           | POS Reporting, Inventory Alerts            |
| Workshop Management  | Job Scheduling, Client Notifications       |
| Professional Services| Invoice Generation, Billing Workflows      |

Each module uses JSON prompt templates in `templates/` that the orchestrator loads and fills with real data from the analysis engine.

---

## License & Legal

- **SLA**: Hardware-bound licensing, draft-only constraints, guaranteed uptime terms
- **MSA/SOW**: Modular architecture supports additional industry modules
- **NDA/DPA**: Zero-Cloud design fulfills local-only data processing requirements
- **Reactivation**: Maximum 2 reactivations per 365-day license period

---

## Hardware Requirements

| Component | Minimum          | Recommended        |
|-----------|------------------|--------------------|
| CPU       | 4 cores          | 8+ cores           |
| RAM       | 8 GB             | 16 GB              |
| Storage   | 10 GB free       | 50 GB (with LLM)   |
| OS        | Windows 10/11    | Windows 11         |
| GPU       | Not required     | NVIDIA (for LLM)   |

---

## Version

**Autify Engine V1.0.0** | Built March 2026
