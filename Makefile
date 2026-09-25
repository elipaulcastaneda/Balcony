PYTHON_VENV=.venv

.PHONY: bootstrap install-backend install-frontend install-node lint test pnpm-install

bootstrap:
	pnpm -w install

pnpm-install:
	pnpm -w install

install-backend:
	py -3.11 -m venv $(PYTHON_VENV)
	$(PYTHON_VENV)\Scripts\python.exe -m pip install --upgrade pip
	$(PYTHON_VENV)\Scripts\python.exe -m pip install -r services\api\requirements.txt

install-frontend:
	pnpm --filter ./apps/web install

lint:
	pnpm --filter ./apps/web run lint || true

test:
	pytest -q
