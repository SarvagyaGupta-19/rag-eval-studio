.PHONY: install test eval run lint ci pipeline

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

eval:
	python -m eval.ragas_eval --dataset eval/datasets/qa_pairs.jsonl

run:
	streamlit run app/main.py

pipeline:
	python scripts/run_pipeline.py

lint:
	ruff check .

ci: test
	@echo "CI checks passed."
