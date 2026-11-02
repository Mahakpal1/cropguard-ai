.PHONY: setup run test get-model docker-up
setup:            ## create venv and install everything
	python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt
run:              ## API + web page on http://localhost:8000 (simulated mode if no model is installed)
	uvicorn backend.app.main:app --reload --port 8000
test:             ## all tests (cv, knowledge base, API, contract)
	python -m pytest
get-model:        ## download the community pretrained model (read ml/README.md first)
	python ml/download_pretrained.py
docker-up:
	docker compose up --build
