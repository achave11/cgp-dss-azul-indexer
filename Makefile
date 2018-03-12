SHELL := /bin/bash

deploy:
	@echo "installing dependencies"
	pip install -r requirements.txt
	source .env
	@echo "configuring AWS with your credentials"
	pip install awscli --upgrade
	aws configure
	export ACC_NUM="$(aws sts get-caller-identity --query 'Account')"
	@read -p "Enter AWS-lambda name: " lambda_name; \
	chalice new-project $$lambda_name; \
	cp app.py $$lambda_name/app.py; \
	cp requirements.txt $$lambda_name/requirements.txt; \
	python subst_config_vars.py $$lambda_name; \
	cp -r chalicelib $$lambda_name/chalicelib; \
	cd $$lambda_name && \
	chalice deploy --no-autogen-policy

teardown:
	@echo "deleting AWS Lambda"
	@read -p "Enter AWS-lambda name: " lambda_name; \
	cd $$lambda_name && \
	chalice delete --stage dev

deploy-local:
	@echo "deploying AWS local"
	cd dss-blau && \
	chalice local

