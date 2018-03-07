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
# Location of the opensource watchmen_core repository
export LOCATION_CORE=.
export PYTHONPATH := .:./verification_rules

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
	@docker build -f docker/Dockerfile -t $(PROJECT) .

### Watchmen Deployment ###

clean:
	$(LOCATION_CORE)/shell_lib/cleanup.sh

create-zips: clean
	$(LOCATION_CORE)/shell_lib/zip_build_deploy.sh

# Make sure 'make create-zips' is run before 'make create-watchmen-cf'
create-watchmen-cf:
	python $(LOCATION_CORE)/python_lib/create_roles_cf.py
	python $(LOCATION_CORE)/python_lib/create_elastic_search_cf.py
	python $(LOCATION_CORE)/python_lib/create_reporting_cf.py
	python $(LOCATION_CORE)/python_lib/create_citizen_update_cf.py
	python $(LOCATION_CORE)/python_lib/create_proxy_lambda_cf.py
	python $(LOCATION_CORE)/python_lib/create_proxy_rules_cf.py
	python $(LOCATION_CORE)/python_lib/create_monitoring_cf.py
	python $(LOCATION_CORE)/python_lib/create_watchmen_cf.py

upload-watchmen-cf:
	aws s3 cp $(LOCATION_CORE)/watchmen_cloudformation/files/citizen-update.yml s3://$(BUCKET_NAME_CF) --no-verify-ssl
	aws s3 cp $(LOCATION_CORE)/watchmen_cloudformation/files/elastic-search.yml s3://$(BUCKET_NAME_CF) --no-verify-ssl
	aws s3 cp $(LOCATION_CORE)/watchmen_cloudformation/files/monitoring.yml s3://$(BUCKET_NAME_CF) --no-verify-ssl
	aws s3 cp $(LOCATION_CORE)/watchmen_cloudformation/files/proxy-lambda.yml s3://$(BUCKET_NAME_CF) --no-verify-ssl
	aws s3 cp $(LOCATION_CORE)/watchmen_cloudformation/files/proxy-rules.yml s3://$(BUCKET_NAME_CF) --no-verify-ssl
	aws s3 cp $(LOCATION_CORE)/watchmen_cloudformation/files/reporting.yml s3://$(BUCKET_NAME_CF) --no-verify-ssl
	aws s3 cp $(LOCATION_CORE)/watchmen_cloudformation/files/roles.yml s3://$(BUCKET_NAME_CF) --no-verify-ssl

deploy-watchmen-core:
	ansible-playbook $(LOCATION_CORE)/watchmen_cloudformation/deploy_watchmen_core.yml -vvv \
		-e 'PROFILE=default' \
		-e 'REGION=$(AWS_DEFAULT_REGION)' \
		-e 'prefix=$(prefix)' \
		-e 'BUCKET_NAME_CF=$(BUCKET_NAME_CF)' \
		-e 'BUCKET_NAME_LAMBDA=$(BUCKET_NAME_LAMBDA)' \
		-e 'ENV=$(ENV)'

deploy-watchmen-core-combined: create-zips create-watchmen-cf upload-watchmen-cf deploy-watchmen-core

deploy-watchmen-core-in-docker: build-docker-base-image ## Deploy watchmen core using docker. If development, set prefix using "make prefix=%%- deploy..."
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e PROFILE=default \
		-e REGION=$(AWS_DEFAULT_REGION) \
		-e prefix=$(prefix) \
		-e BUCKET_NAME_CF=$(BUCKET_NAME_CF) \
		-e BUCKET_NAME_LAMBDA=$(BUCKET_NAME_LAMBDA) \
		-e BUCKET_NAME_DISTRIBUTION=$(BUCKET_NAME_DISTRIBUTION) \
		-e ENV=$(ENV) \
		$(PROJECT) \
		/bin/sh -c "make deploy-watchmen-core-combined"

deploy-watchmen-citizen-update:
	ansible-playbook $(LOCATION_CORE)/watchmen_cloudformation/deploy_watchmen_citizen_update.yml -vvv \
		-e 'PROFILE=default' \
		-e 'REGION=$(AWS_DEFAULT_REGION)' \
		-e 'prefix=$(prefix)' \
		-e 'BUCKET_NAME_CF=$(BUCKET_NAME_CF)' \
		-e 'BUCKET_NAME_DISTRIBUTION=$(BUCKET_NAME_DISTRIBUTION)' \
		-e 'BUCKET_NAME_LAMBDA=$(BUCKET_NAME_LAMBDA)' \
		-e 'ENV=$(ENV)'

# Has a dependency on watchmen core
deploy-watchmen-citizen-update-in-docker: build-docker-base-image ## Deploy watchmen citizen update using docker. If development, set prefix using "make prefix=%%- deploy..." Has a dependency on watchmen core.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e PROFILE=default \
		-e REGION=$(AWS_DEFAULT_REGION) \
		-e BUCKET_NAME_CF=$(BUCKET_NAME_CF) \
		-e BUCKET_NAME_DISTRIBUTION=$(BUCKET_NAME_DISTRIBUTION) \
		-e BUCKET_NAME_LAMBDA=$(BUCKET_NAME_LAMBDA) \
		-e ENV=$(ENV) \
		-e prefix=$(prefix) \
		$(PROJECT) \
		/bin/sh -c "make deploy-watchmen-citizen-update"

deploy-watchmen-monitoring:
	ansible-playbook $(LOCATION_CORE)/watchmen_cloudformation/deploy_watchmen_monitoring.yml -vvv \
		-e 'PROFILE=default' \
		-e 'REGION=$(AWS_DEFAULT_REGION)' \
		-e 'prefix=$(prefix)' \
		-e 'BUCKET_NAME_CF=$(BUCKET_NAME_CF)' \
		-e 'ENV=$(ENV)'

# Has a dependency on watchmen core
deploy-watchmen-monitoring-in-docker: build-docker-base-image ## Deploy watchmen monitoring using docker. If development, set prefix using "make prefix=%%- deploy..." Has a dependency on watchmen core.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e PROFILE=default \
		-e REGION=$(AWS_DEFAULT_REGION) \
		-e BUCKET_NAME_CF=$(BUCKET_NAME_CF) \
		-e ENV=$(ENV) \
		-e prefix=$(prefix) \
		$(PROJECT) \
		/bin/sh -c "make deploy-watchmen-monitoring"

deploy-watchmen-reporting:
	ansible-playbook $(LOCATION_CORE)/watchmen_cloudformation/deploy_watchmen_reporting.yml -vvv \
		-e 'PROFILE=default' \
		-e 'REGION=$(AWS_DEFAULT_REGION)' \
		-e 'prefix=$(prefix)' \
		-e 'BUCKET_NAME_CF=$(BUCKET_NAME_CF)' \
		-e 'BUCKET_NAME_LAMBDA=$(BUCKET_NAME_LAMBDA)' \
		-e 'BUCKET_NAME_REPORT=$(BUCKET_NAME_REPORT)' \
		-e 'ENV=$(ENV)'

populate-citizen-account:
	python $(LOCATION_CORE)/python_lib/populate_citizen_account.py

deploy-watchmen-reporting-combined: deploy-watchmen-reporting populate-citizen-account

# Has a dependency on watchmen core
deploy-watchmen-reporting-in-docker: build-docker-base-image ## Deploy watchmen reporting using docker. If development, set prefix using "make prefix=%%- deploy..." Has a dependency on watchmen core.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e PROFILE=default \
		-e REGION=$(AWS_DEFAULT_REGION) \
		-e BUCKET_NAME_CF=$(BUCKET_NAME_CF) \
		-e BUCKET_NAME_LAMBDA=$(BUCKET_NAME_LAMBDA) \
		-e BUCKET_NAME_REPORT=$(BUCKET_NAME_REPORT) \
		-e ENV=$(ENV) \
		-e prefix=$(prefix) \
		$(PROJECT) \
		/bin/sh -c "make deploy-watchmen-reporting-combined"

deploy-watchmen-elastic-search:
	ansible-playbook $(LOCATION_CORE)/watchmen_cloudformation/deploy_watchmen_elastic_search.yml -vvv \
		-e 'PROFILE=default' \
		-e 'REGION=$(AWS_DEFAULT_REGION)' \
		-e 'prefix=$(prefix)' \
		-e 'BUCKET_NAME_CF=$(BUCKET_NAME_CF)' \
		-e 'BUCKET_NAME_LAMBDA=$(BUCKET_NAME_LAMBDA)' \
		-e 'ELASTIC_SEARCH_INSTANCE_COUNT=$(ELASTIC_SEARCH_INSTANCE_COUNT)' \
		-e 'DEPLOY_REPORTING=$(DEPLOY_REPORTING)' \
		-e 'DEPLOY_CITIZEN_UPDATE=$(DEPLOY_CITIZEN_UPDATE)' \
		-e 'CREATE_SUBSCRIPTION=$(CREATE_SUBSCRIPTION)' \
		-e 'ENV=$(ENV)'

# Has a dependency on watchmen core
deploy-watchmen-elastic-search-in-docker: build-docker-base-image ## Deploy watchmen elastic search using docker. If development, set prefix using "make prefix=%%- deploy..." Has a dependency on watchmen core.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e PROFILE=default \
		-e REGION=$(AWS_DEFAULT_REGION) \
		-e prefix=$(prefix) \
		-e BUCKET_NAME_CF=$(BUCKET_NAME_CF) \
		-e BUCKET_NAME_LAMBDA=$(BUCKET_NAME_LAMBDA) \
		-e ELASTIC_SEARCH_INSTANCE_COUNT=$(ELASTIC_SEARCH_INSTANCE_COUNT) \
		-e DEPLOY_REPORTING=$(DEPLOY_REPORTING) \
		-e DEPLOY_CITIZEN_UPDATE=$(DEPLOY_CITIZEN_UPDATE) \
		-e CREATE_SUBSCRIPTION=$(CREATE_SUBSCRIPTION) \
		-e ENV=$(ENV) \
		$(PROJECT) \
		/bin/sh -c "make deploy-watchmen-elastic-search"

### Create and Upload Citizen template  ###
### Set environment variables for AWS credentials, AWS_DEFAULT_REGION, CITIZEN_S3_BUCKET.
### Note: CITIZEN_VERSION will be set as Current Australian time (YYMMDD.HMS)

create-citizen-cf: clean
	python $(LOCATION_CORE)/python_lib/create_citizen_cf.py

upload-citizen:
	$(LOCATION_CORE)/citizen_lib/upload_citizen_cfn.sh

upload-citizen-combined: create-citizen-cf upload-citizen

upload-citizen-in-docker: build-docker-base-image ## Create and upload citizen template using docker.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e CITIZEN_S3_BUCKET \
		$(PROJECT) \
		/bin/sh -c "make upload-citizen-combined"

### Trigger Citizen Stack Update via SNS Topic in Watchmen ###
### Set environment variables for AWS credentials, AWS_DEFAULT_REGION, CITIZEN_S3_BUCKET, Citizen Update SNS Topic ARN (arn:aws:sns:<aws region>:<watchmen_account_number>:watchmen-citizen-updates) and prefix (if applicable)

sns-staging:
	aws sns publish --topic-arn "${SNS_ARN}" --message "${SNS_MESSAGE}" --no-verify-ssl

sns-staging-in-docker: ## Sends SNS message to trigger Citizen Update for staging Citizen account using docker.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e SNS_ARN \
		-e SNS_MESSAGE \
		$(PROJECT) \
		/bin/sh -c "make sns-staging"

sns-canary:
	python $(LOCATION_CORE)/citizen_lib/trigger_citizen_stack_update.py CanaryAccounts

sns-canary-in-docker: build-docker-base-image ## Sends SNS message to trigger Citizen Update for Canary Accounts defined in 'configuration/config.yml' using docker.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e SNS_ARN=$(SNS_ARN) \
		-e prefix=$(prefix) \
		-e CITIZEN_S3_BUCKET \
		$(PROJECT) \
		/bin/sh -c "make sns-canary"

sns-prod:
	python $(LOCATION_CORE)/citizen_lib/trigger_citizen_stack_update.py ProductionAccounts

sns-prod-in-docker: build-docker-base-image ## Sends SNS message to trigger Citizen Update for production Citizen accounts (excluding Canary Accounts) using docker.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e SNS_ARN=$(SNS_ARN) \
		-e prefix=$(prefix) \
		-e CITIZEN_S3_BUCKET \
		$(PROJECT) \
		/bin/sh -c "make sns-prod"

canary-tests:
	pytest --verbose -s $(LOCATION_CORE)/citizen_lib/test_canary_accounts.py

canary-tests-in-docker: build-docker-base-image ## Run canary tests to check canary Citizen accounts using docker.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
	    -e prefix=$(prefix) \
		-e CITIZEN_S3_BUCKET \
		$(PROJECT) \
		/bin/sh -c "make canary-tests"

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
	pylint $(LOCATION_CORE)/citizen_updates \
		$(LOCATION_CORE)/elasticsearch \
		$(LOCATION_CORE)/python_lib \
		$(LOCATION_CORE)/reports \
		$(LOCATION_CORE)/verification_rules; exit 0 # forcing a clean exit so as not to break the build

pylint-in-docker: build-docker-base-image  ## Run pylint using docker.
	@docker run -i \
		-v $(PWD):/data \
		$(PROJECT) \
		/bin/sh -c "make pylint"

unit-tests: clean
	pytest --verbose -s \
		--cov=$(LOCATION_CORE)/verification_rules \
		--cov=$(LOCATION_CORE)/reports \
		--cov=$(LOCATION_CORE)/proxy_lambda \
		--cov=$(LOCATION_CORE)/python_lib \
		--cov-report html

	@echo "Test all unit tests via pytest"

unit-tests-in-docker: build-docker-base-image  ## Run unit tests using docker.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_DEFAULT_REGION \
		$(PROJECT) \
		/bin/sh -c "make unit-tests"

## Watchmen Integration Tests ###

int-tests-watchmen: clean
	pytest --verbose -s $(LOCATION_CORE)/integration_tests/test_lambda_functions_exists.py
	pytest --verbose -s $(LOCATION_CORE)/integration_tests/test_lambda_functions_executes.py

int-tests-watchmen-in-docker: build-docker-base-image ## Run Watchmen integration tests using docker.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e prefix=$(prefix) \
		-e CITIZEN_ARN=$(CITIZEN_ARN) \
		$(PROJECT) \
		/bin/sh -c "make int-tests-watchmen"

## Citizen Integration Tests ###

int-tests-citizen: clean
	pytest --verbose -s $(LOCATION_CORE)/integration_tests/test_config_rules_exists.py
	pytest --verbose -s $(LOCATION_CORE)/integration_tests/test_config_citizen_version.py

int-tests-citizen-in-docker: build-docker-base-image ## Run Citizen integration tests using docker.
	@docker run -i \
		-v $(PWD):/data \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e AWS_SESSION_TOKEN \
		-e AWS_DEFAULT_REGION \
		-e prefix=$(prefix) \
		$(PROJECT) \
		/bin/sh -c "make int-tests-citizen"
