# Balcony QC & Approval Platform (monorepo)

Local setup (Windows / Powershell)

1) Install Node (>=18) and Python (>=3.10)

2) Install frontend dependencies (pnpm workspace)

```powershell
# install pnpm if you don't already have it
npm install -g pnpm

pnpm -w install
```

3) Create and activate Python venv with Python 3.11, install backend deps

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r services\api\requirements.txt
```

4) Run Docker Compose (Postgres + MinIO)

```powershell
docker compose -f infra\docker-compose.yml up -d
```

5) Run backend (development)

```powershell
cd services\api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6) Run frontend

```powershell
pnpm --filter ./apps/web run dev
```

Makefile targets are available for common developer tasks; see `Makefile`.
# Balcony
A quality-control and approval layer for AI-generated business work that verifies accuracy, evidence, and risk, fixes simple issues, and routes exceptions to the right reviewer before approved work reaches customers or systems like Salesforce, ERP, email, or finance tools.
