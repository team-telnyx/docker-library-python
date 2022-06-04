# SHELL := bash
# .ONESHELL:
# .SHELLFLAGS := -o errexit -o nounset -o pipefail -c
# MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules
MAKEFLAGS += --always-make

# .PHONY: build
# build:
# 	echo TODO

# venv_dir := .venv

# venv: requirements.txt
# 	python3 -m venv ${venv_dir}
# 	${venv_dir}/bin/python3 -m pip install -r $<
# 	${venv_dir}/bin/python3 -m pip freeze > $@

# %: venv
# 	${venv_dir}/bin/python3 -m doit $@

.PHONY: list
	bash scripts/make-delegator.sh list

.PHONY: %
%:
	bash scripts/make-delegator.sh $@
