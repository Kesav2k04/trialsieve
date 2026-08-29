# A thin wrapper. `python run.py <target>` is the real entry point and works
# on a machine with no make, which includes a stock Windows box.

PY ?= python

.PHONY: help check reproduce verify diff live live-smoke panel clean \n        contamination environment links publish

help:
	@$(PY) run.py help

check:
	@$(PY) run.py check

reproduce:
	@$(PY) run.py reproduce

verify:
	@$(PY) run.py verify

diff:
	@$(PY) run.py diff

live-smoke:
	@$(PY) run.py live-smoke

live:
	@$(PY) run.py live

panel:
	@$(PY) run.py panel

clean:
	@$(PY) run.py clean

contamination:
	@$(PY) run.py contamination

environment:
	@$(PY) run.py environment

links:
	@$(PY) run.py links

publish:
	@$(PY) run.py publish
