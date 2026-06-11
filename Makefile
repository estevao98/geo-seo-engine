setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -e .

test:
	. .venv/bin/activate && python -m pytest

check:
	git status --short
	git diff --stat
	git diff --check

mcp:
	opencode mcp list
