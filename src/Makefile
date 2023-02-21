.PHONY: all
all: help

.PHONY: lint
lint: check-isort check-black ## Run all linters and formatters

.PHONY: black
black: ## Update Python source code formatting with black
	@black .

.PHONY: check-black
check-black: ## Check Python source code formatting with black
	@black --check --diff .

.PHONY: isort
isort: ## Update Python import organization with isort
	@isort .

.PHONY: check-isort
check-isort: ## Check Python import organization with isort
	@isort --check-only --diff .

# Explanation of the below shell command should it ever break.
# 1. Set the field separator to ": ##" and any make targets that might appear between : and ##
# 2. Use sed-like syntax to remove the make targets
# 3. Format the split fields into $$1) the target name (in blue) and $$2) the target descrption
# 4. Pass this file as an arg to awk
# 5. Sort it alphabetically
# 6. Format columns with colon as delimiter.
.PHONY: help
help: ## Print this message and exit.
	@printf "Makefile for developing and testing the SecureDrop proxy.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
