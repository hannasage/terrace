# Terrace. The six targets named in CLAUDE.md, plus help as the default.
#
# These are the canonical entry points. CI and the data-refresh workflow call
# the same underlying commands, so a green local run means a green pipeline.

DBT_DIR := pipeline/dbt

.DEFAULT_GOAL := help

.PHONY: help ingest build check publish dev

help: ## List the available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

ingest: ## Fetch raw source data into pipeline/data/raw
	uv run python -m pipeline.ingest --sources all

build: ## Run dbt build, which runs every model and test
	uv run dbt build --project-dir $(DBT_DIR) --profiles-dir $(DBT_DIR)

check: ## Quality gates: guardrails over the diff, registry consistency, house style
	uv run python scripts/guardrails_ci.py "$${BASE_SHA:-HEAD~1}"
	uv run python scripts/check_registry.py
	uv run python scripts/house_style.py

publish: ## Write Parquet artefacts to web/public/data
	uv run python scripts/publish.py

dev: ## Run the web application locally
	cd web && npm run dev
