PYTHON ?= python3

.PHONY: check clean compile doctor live-smoke package package-repro-check test validate

check: compile validate test

compile:
	$(PYTHON) -m compileall -q plugins scripts tests

validate:
	$(PYTHON) scripts/validate_project.py

test:
	$(PYTHON) -m unittest discover -v

package:
	$(PYTHON) scripts/package_plugin.py

package-repro-check:
	$(PYTHON) -m unittest -v tests.test_packaging.PackagingTests.test_package_is_deterministic_and_contains_only_plugin_files

doctor:
	$(PYTHON) plugins/claude-advisor/scripts/claude_advisor.py doctor --require-gh

live-smoke: doctor
	@echo "Doctor passed. Run the documented advisory and supplied-diff smoke with approved synthetic input."

clean:
	rm -rf dist plugins/claude-advisor/scripts/__pycache__ scripts/__pycache__ tests/__pycache__
