.PHONY: help setup run transform dashboard test ci clean

help:
	@echo ""
	@echo "  modern-data-pipeline — Makefile"
	@echo "  ================================"
	@echo ""
	@echo "  make setup       → Create venv + install dependencies"
	@echo "  make run         → Run full pipeline (extract + load + transform)"
	@echo "  make extract     → Extract + load only (no dbt)"
	@echo "  make transform   → Run dbt build only"
	@echo "  make dashboard   → Start Evidence.dev dev server"
	@echo "  make test        → Run pytest"
	@echo "  make ci          → Full pipeline (used by GitHub Actions)"
	@echo "  make clean       → Remove venv, duckdb, dbt artifacts"
	@echo ""

# ── Setup ──────────────────────────────────────────────────────────────────────

setup:
	@echo "📦 Creating virtual environment..."
	python -m venv .venv
	.venv/bin/pip install --upgrade pip --quiet
	.venv/bin/pip install -r requirements.txt
	.venv/bin/dbt deps --project-dir transform/dbt_pipeline --profiles-dir transform/dbt_pipeline
	@echo ""
	@echo "✅ Python setup complete"
	@echo ""
	@echo "📦 Installing Evidence.dev dashboard..."
	cd dashboard && npm install
	@echo ""
	@echo "✅ All dependencies installed!"
	@echo "👉 Activate venv: source .venv/bin/activate"
	@echo "👉 Copy env file: cp .env.example .env  (then fill GITHUB_TOKEN)"

# ── Pipeline ───────────────────────────────────────────────────────────────────

run:
	@echo "🚀 Running full pipeline..."
	.venv/bin/python -m pipeline.flows

extract:
	@echo "📥 Extract + Load only..."
	.venv/bin/python scripts/run_extract.py

transform:
	@echo "🔨 Running dbt build..."
	.venv/bin/dbt build \
		--project-dir transform/dbt_pipeline \
		--profiles-dir transform/dbt_pipeline

# ── Dashboard ──────────────────────────────────────────────────────────────────

dashboard:
	@echo "📊 Starting Evidence.dev dashboard..."
	cd dashboard && npm run dev

dashboard-build:
	cd dashboard && npm run build

# ── Tests ──────────────────────────────────────────────────────────────────────

test:
	.venv/bin/pytest tests/ -v

# ── CI (used by GitHub Actions) ────────────────────────────────────────────────

ci: extract transform
	@echo "✅ CI pipeline complete"

# ── Cleanup ────────────────────────────────────────────────────────────────────

clean:
	rm -rf .venv
	rm -f pipeline.duckdb
	rm -rf transform/dbt_pipeline/target
	rm -rf transform/dbt_pipeline/dbt_packages
	rm -rf dashboard/node_modules
	rm -rf dashboard/.evidence
	@echo "🧹 Clean complete"
