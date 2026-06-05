.PHONY: install test eval run lint

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

eval:
	python -m eval.ragas_eval --dataset eval/datasets/qa_pairs.jsonl

run:
	streamlit run app/main.py

lint:
	ruff check .
