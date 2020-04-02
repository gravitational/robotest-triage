REQUIREMENTS=requirements.txt
FREEZE=requirements-freeze.txt
REQUIREMENTS_INSTALLED=.requirements-installed.txt
DEV_REQUIREMENTS=dev-requirements.txt
DEV_FREEZE=dev-requirements-freeze.txt
TOOLCHAIN_INSTALLED=.dev-requirements-installed.txt
CREDENTIALS=credentials.json
CREDENTIALS_EXAMPLE=credentials.json.example
CONFIG=config.json
CONFIG_EXAMPLE=config.json.example
DATADIR=data
SRCS=fetch.py analyze.py

.PHONY: help
# kudos to https://gist.github.com/prwhite/8168133 for inspiration
help: ## Show this message.
	@echo 'Usage: make [options] [target] ...'
	@echo
	@echo 'Options: run `make --help` for options'
	@echo
	@echo 'Targets:'
	@egrep '^(.+)\:\ ##\ (.+)' ${MAKEFILE_LIST} | column -t -c 2 -s ':#' | sort | sed 's/^/  /'

.PHONY: install
install: ## Install necessary dependencies.
install: $(REQUIREMENTS_INSTALLED)

.PHONY: toolchain
toolchain:  ## Install development tools.
toolchain: $(TOOLCHAIN_INSTALLED)

.PHONY: clean
clean: ## Remove intermediate build artifacts.
	rm -rf $(REQUIREMENTS_INSTALLED) $(TOOLCHAIN_INSTALLED)

$(REQUIREMENTS_INSTALLED): $(FREEZE)
	pip install -r $(FREEZE)
	pip freeze > $(REQUIREMENTS_INSTALLED)

$(FREEZE): $(REQUIREMENTS)
	pip install -r $(REQUIREMENTS)
	pip freeze -r $(REQUIREMENTS) > $(FREEZE)

$(TOOLCHAIN_INSTALLED): $(DEV_FREEZE)
	pip install -r $(DEV_FREEZE)
	pip freeze > $(TOOLCHAIN_INSTALLED)

$(DEV_FREEZE): $(DEV_REQUIREMENTS)
	pip install -r $(DEV_REQUIREMENTS)
	pip freeze --all -r $(DEV_REQUIREMENTS) > $(DEV_FREEZE)

.PHONY: lint
lint:  ## Run source code through static analysis.
lint: $(TOOLCHAIN_INSTALLED)
	flake8 $(SRCS)

$(DATADIR):
	mkdir -p $(DATADIR)

.PHONY: fetch
fetch: ## Fetch job console logs from Jenkins.
fetch: $(REQUIREMENTS_INSTALLED) | $(DATADIR)
	python fetch.py

# TODO: use a better dependency than the .PHONY fetch
.PHONY: analyze
analyze: ## Run analytics on fetched data.
analyze: fetch $(REQUIREMENTS_INSTALLED)
	python analyze.py $(DATADIR)/*

.PHONY: configure
configure: $(CONFIG) $(CREDENTIALS)

$(CONFIG):
	cp $(CONFIG_EXAMPLE) $(CONFIG)
	@echo "Default configuration copied to $(CONFIG). Please edit this file to change config."

$(CREDENTIALS):
	cp $(CREDENTIALS_EXAMPLE) $(CREDENTIALS)
	@echo "Please update $(CREDENTIALS) with your Jenkins user and token."
	@echo "Aborting to allow you to edit $(CREDENTIALS)..."
	@exit 1

.PHONY: auth
auth: ## Test authentication.
auth: url=$(shell python -c "import json; print(json.load(open('$(CONFIG)', 'r'))['url'])")
auth: credentials=$(shell python -c "import json; print(json.load(open('$(CONFIG)', 'r'))['credentials'])")

auth: user=$(shell python -c "import json; print(json.load(open('$(credentials)', 'r'))['user'])")
auth: token=$(shell python -c "import json; print(json.load(open('$(credentials)', 'r'))['token'])")
auth: $(CONFIG) $(credentials)
	curl --silent --fail --user $(user):$(token) $(url) > /dev/null
	@echo "Sucessfully authenticated."

