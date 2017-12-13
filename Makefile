# Copyright 2017 Insurance Australia Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
PROJECT=watchmen_base

define HELP_TEXT
Usage: make [TARGET]...
!!IMPORTANT!! before running make [TARGET], please make sure you are running suitable role in correct AWS account...
Available targets:
endef
export HELP_TEXT

help: ## Help target
		@echo "$$HELP_TEXT"
		@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / \
			{printf "\033[36m%-30s\033[0m  %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build-docker-base-image:
	@echo "$(INFO) Preparing Docker build env image"
	@git rev-parse --short HEAD > .git-tag
	@docker build -f docker/Dockerfile -t $(PROJECT) .

### Watchmen Deployment ###

clean:
	./shell_lib/cleanup.sh

create-zips: clean
	./shell_lib/zip_build_deploy.sh

# Make sure 'make create-zips' is run before 'make create-watchmen-cf'
create-watchmen-cf:
	python ./python_lib/create_roles_cf.py
	python ./python_lib/create_es_cluster_cf.py
	python ./python_lib/create_es_subscriptions_cf.py
	python ./python_lib/create_reporting_cf.py
	python ./python_lib/create_citizen_update_cf.py
	python ./python_lib/create_verification_rule_cf.py
	python ./python_lib/create_watchmen_cf.py

deploy-watchmen:
	ansible-playbook watchmen_cloudformation/deploy_to_watchmen_account.yml -vvv \
		-e 'PROFILE=default' \
		-e 'REGION=$(AWS_DEFAULT_REGION)' \
		-e 'BUCKET_NAME_CF=$(BUCKET_NAME_CF)' \
		-e 'BUCKET_NAME_DISTRIBUTION=$(BUCKET_NAME_DISTRIBUTION)' \
		-e 'BUCKET_NAME_LAMBDA=$(BUCKET_NAME_LAMBDA)' \
		-e 'BUCKET_NAME_REPORT=$(BUCKET_NAME_REPORT)' \
		-e 'DEPLOY_CITIZEN_UPDATE=$(DEPLOY_CITIZEN_UPDATE)' \
	    -e 'DEPLOY_ELASTIC_SEARCH=$(DEPLOY_ELASTIC_SEARCH)' \
		-e 'DEPLOY_MONITORING=$(DEPLOY_MONITORING)' \
		-e 'DEPLOY_REPORTING=$(DEPLOY_REPORTING)' \
	    -e 'ELASTIC_SEARCH_INSTANCE_COUNT=$(ELASTIC_SEARCH_INSTANCE_COUNT)' \
		-e 'ENV=$(ENV)' \
		-e 'prefix=$(prefix)'

deploy-watchmen-in-docker: build-docker-base-image ## Deploy watchmen using docker. If development, set prefix using "make prefix=%%- deploy..."
	@docker run -i \
		-e 'AWS_ACCESS_KEY_ID' \
		-e 'AWS_DEFAULT_REGION' \
		-e 'AWS_SECRET_ACCESS_KEY' \
		-e 'AWS_SESSION_TOKEN' \
		-e 'PROFILE=default' \
		-e 'REGION=$(AWS_DEFAULT_REGION)' \
		-e 'BUCKET_NAME_CF=$(BUCKET_NAME_CF)' \
		-e 'BUCKET_NAME_DISTRIBUTION=$(BUCKET_NAME_DISTRIBUTION)' \
		-e 'BUCKET_NAME_LAMBDA=$(BUCKET_NAME_LAMBDA)' \
		-e 'BUCKET_NAME_REPORT=$(BUCKET_NAME_REPORT)' \
		-e 'DEPLOY_CITIZEN_UPDATE=$(DEPLOY_CITIZEN_UPDATE)' \
		-e 'DEPLOY_ELASTIC_SEARCH=$(DEPLOY_ELASTIC_SEARCH)' \
		-e 'DEPLOY_MONITORING=$(DEPLOY_MONITORING)' \
		-e 'DEPLOY_REPORTING=$(DEPLOY_REPORTING)' \
		-e 'ELASTIC_SEARCH_INSTANCE_COUNT=$(ELASTIC_SEARCH_INSTANCE_COUNT)' \
		-e 'ENV=$(ENV)' \
		-e 'prefix=$(prefix)' \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "make create-zips; make create-watchmen-cf; make deploy-watchmen"

### Create and Upload Citizen template  ###
### Set environment variables for AWS credentials, AWS_DEFAULT_REGION, CITIZEN_S3_BUCKET, CITIZEN_VERSION_MAJOR and CITIZEN_VERSION_MINOR (CITIZEN_VERSION=CITIZEN_VERSION_MAJOR.CITIZEN_VERSION_MINOR)

# Make sure 'make create-zips' is run before 'make create-citizen-cf'
create-citizen-cf: clean
	python ./python_lib/create_citizen_cf.py

upload-citizen:
	./citizen_lib/upload_citizen_cfn.sh

upload-citizen-in-docker: build-docker-base-image ## Create and upload citizen template using docker.
	@docker run -i \
		-e 'AWS_ACCESS_KEY_ID' \
		-e 'AWS_DEFAULT_REGION' \
		-e 'AWS_SECRET_ACCESS_KEY' \
		-e 'AWS_SESSION_TOKEN' \
		-e 'CITIZEN_VERSION_MAJOR' \
		-e 'CITIZEN_VERSION_MINOR' \
		-e 'CITIZEN_S3_BUCKET' \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "make create-citizen-cf; make upload-citizen"

### Trigger Citizen Stack Update via SNS Topic in Watchmen ###
### Set environment variables for AWS credentials, AWS_DEFAULT_REGION, CITIZEN_S3_BUCKET, Citizen Update SNS Topic ARN (arn:aws:sns:<aws region>:<watchmen_account_number>:watchmen-citizen-updates) and prefix (if applicable)

sns-staging:
	`which aws` sns publish --topic-arn "${SNS_ARN}" --message "${SNS_MESSAGE}" --no-verify-ssl

sns-staging-in-docker: ## Sends SNS message to trigger Citizen Update for staging Citizen account using docker.
	@docker run -i \
		-e 'AWS_ACCESS_KEY_ID' \
		-e 'AWS_DEFAULT_REGION' \
		-e 'AWS_SECRET_ACCESS_KEY' \
		-e 'AWS_SESSION_TOKEN' \
		-e 'SNS_ARN' \
		-e 'SNS_MESSAGE' \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "make sns-staging"

sns-canary-in-docker: build-docker-base-image ## Sends SNS message to trigger Citizen Update for Canary Accounts defined in 'configuration/config.yml' using docker.
	@docker run -i \
		-e 'AWS_ACCESS_KEY_ID' \
		-e 'AWS_DEFAULT_REGION' \
		-e 'AWS_SECRET_ACCESS_KEY' \
		-e 'AWS_SESSION_TOKEN' \
		-e 'SNS_ARN=$(SNS_ARN)' \
		-e 'prefix=$(prefix)' \
		-e 'CITIZEN_S3_BUCKET' \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "python ./citizen_lib/trigger_citizen_stack_update.py CanaryAccounts"

sns-prod-in-docker: build-docker-base-image ## Sends SNS message to trigger Citizen Update for production Citizen accounts (excluding Canary Accounts) using docker.
	@docker run -i \
		-e 'AWS_ACCESS_KEY_ID' \
		-e 'AWS_DEFAULT_REGION' \
		-e 'AWS_SECRET_ACCESS_KEY' \
		-e 'AWS_SESSION_TOKEN' \
		-e 'SNS_ARN=$(SNS_ARN)' \
		-e 'prefix=$(prefix)' \
		-e 'CITIZEN_S3_BUCKET' \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "python ./citizen_lib/trigger_citizen_stack_update.py ProductionAccounts"

canary-tests-in-docker: build-docker-base-image ## Run canary tests to check canary Citizen accounts using docker.
	@docker run -i \
		-e 'AWS_ACCESS_KEY_ID' \
		-e 'AWS_DEFAULT_REGION' \
		-e 'AWS_SECRET_ACCESS_KEY' \
		-e 'AWS_SESSION_TOKEN' \
		-e 'prefix=$(prefix)' \
		-e 'CITIZEN_S3_BUCKET' \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "pytest citizen_lib/test_canary_accounts.py --verbose -s --junitxml htmlcov/junit.xml --html htmlcov/canary_test_report.html --self-contained-html"

### Watchmen Pre Merge Tests ###

git-secrets: clean
	git secrets --install -f
	git secrets --register-aws
	git secrets --add -a '123456789012'  # Added allowed pattern for unit test account number "123456789012"
	git secrets --scan

git-secrets-in-docker: build-docker-base-image ## Run git-secrets using docker.
	# Want to copy the files into the container as git secrets modifies git config.
	# Don't want the local copy of git config to be modified.
	@test -f $@.cid && { docker rm -f $$(cat $@.cid); rm $@.cid; } || true;
	@docker run -d -t --cidfile="$@.cid" \
		-e TERM \
		$(PROJECT) \
		/bin/sh
	@docker cp $(PWD)/. $$(cat $@.cid):/data
	@docker exec -i $$(cat $@.cid) make git-secrets
	@docker stop $$(cat $@.cid)
	@docker rm $$(cat $@.cid)
	@rm $@.cid

pylint: clean
	pip install -e .
	mkdir pylint
	pylint --output-format=json citizen_updates elasticsearch python_lib reports verification_rules > ./pylint/pylint_report.json; exit 0 # forcing a clean exit so as not to break the build

pylint-in-docker: build-docker-base-image  ## Run pylint using docker.
	@docker run -i \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "make pylint"

unit-tests: clean
	pip install -e .
	pytest --verbose -s \
		--cov=verification_rules \
		--cov=reports
	@echo "Test all unit tests via pytest"

unit-tests-in-docker: build-docker-base-image  ## Run unit tests using docker.
	@docker run -i \
		-e 'AWS_DEFAULT_REGION' \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "make unit-tests"

## Watchmen Integration Tests ###

int-tests-watchmen: clean
	pytest --verbose -s integration_tests/test_lambda_functions_exists.py
	pytest --verbose -s integration_tests/test_lambda_functions_executes.py

int-tests-watchmen-in-docker: build-docker-base-image ## Run Watchmen integration tests using docker.
	@docker run -i \
		-e 'AWS_ACCESS_KEY_ID' \
		-e 'AWS_DEFAULT_REGION' \
		-e 'AWS_SECRET_ACCESS_KEY' \
		-e 'AWS_SESSION_TOKEN' \
		-e 'prefix=$(prefix)' \
		-e 'CITIZEN_ARN=$(CITIZEN_ARN)' \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "make int-tests-watchmen"

## Citizen Integration Tests ###

int-tests-citizen: clean
	pytest --verbose -s integration_tests/test_config_rules_exists.py
	pytest --verbose -s integration_tests/test_config_citizen_version.py

int-tests-citizen-in-docker: build-docker-base-image ## Run Citizen integration tests using docker.
	@docker run -i \
		-e 'AWS_ACCESS_KEY_ID' \
		-e 'AWS_DEFAULT_REGION' \
		-e 'AWS_SECRET_ACCESS_KEY' \
		-e 'AWS_SESSION_TOKEN' \
		-e 'prefix=$(prefix)' \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "make int-tests-citizen"
