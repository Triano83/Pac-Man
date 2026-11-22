PY = python3

install:
	$(PY) -m pip install -r requirements.txt

run:
	$(PY) pac-man.py config.json

debug:
	$(PY) -m pdb pac-man.py config.json

clean:
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache build dist

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

test:
	$(PY) -m pytest -q

package:
	$(PY) -m pip install pyinstaller
	$(PY) build.py

.PHONY: install run debug clean lint lint-strict test package
