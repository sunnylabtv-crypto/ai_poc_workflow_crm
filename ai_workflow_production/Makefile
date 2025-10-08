.PHONY: install health run monitor logs

install:
	pip install -r requirements.txt

health:
	python main.py --mode health

run:
	python main.py --mode single --env development

monitor:
	python main.py --mode monitor --env development

monitor-prod:
	python main.py --mode monitor --env production

logs:
	python scripts/monitor_logs.py tail 50

watch:
	python scripts/monitor_logs.py watch

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
