PYTHON ?= python3

.PHONY: check clean compile doctor live-smoke marketplace-update-smoke package package-repro-check release-contract test validate

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

release-contract:
	$(PYTHON) scripts/validate_release.py --tag "$(TAG)"

marketplace-update-smoke:
	$(PYTHON) scripts/marketplace_update_smoke.py

doctor:
	$(PYTHON) plugins/amanerp-second-opinion/scripts/second_opinion.py doctor --require-gh

live-smoke: doctor
	@echo "Doctor passed. Run the documented advisory and supplied-diff smoke with approved synthetic input."

clean:
	rm -rf dist plugins/amanerp-second-opinion/scripts/__pycache__ scripts/__pycache__ tests/__pycache__
