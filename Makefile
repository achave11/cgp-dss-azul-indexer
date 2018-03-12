SHELL := /bin/bash

deploy:
	@echo "installing dependencies"
	pip install -r requirements.txt
	@echo "configuring AWS with your credentials"
	pip install awscli --upgrade
	aws configure 
	@read -p "Enter AWS-lambda name: " lambda_name; \
	chalice new-project $$lambda_name; \
	cp app.py $$lambda_name; \
	cp requirements.txt $$lambda_name/requirements.txt; \
	source .env && python subst_config_vars.py $$lambda_name; \
	cp -r chalicelib $$lambda_name; \
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

