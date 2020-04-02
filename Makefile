REQUIREMENTS=requirements.txt
FREEZE=requirements-freeze.txt
CREDENTIALS=credentials.json
CREDENTIALS_EXAMPLE=credentials.json.example
CONFIG=config.json
CONFIG_EXAMPLE=config.json.example
DATADIR=data

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
install: $(FREEZE)

$(FREEZE): $(REQUIREMENTS)
	pip install -r $(REQUIREMENTS)
	pip freeze -r $(REQUIREMENTS) > $(FREEZE)

.PHONY: fetch
fetch: ## Fetch job console logs from Jenkins.
fetch: $(FREEZE) | $(DATADIR)
	python fetch.py

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

$(DATADIR):
	mkdir -p $(DATADIR)

