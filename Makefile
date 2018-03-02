SHELL := /bin/bash
deploy:
	@echo "installing dependencies\n"
	pip install -r requirements.txt
	source .env
	@echo "configuring AWS with your credentials\n"
	pip install awscli --upgrade && \
	aws configure && \
	chalice new-project dss-blau && \
	cp app.py dss-blau/app.py
	cp -r chalicelib dss-blau/chalicelib
	@echo "deploying lambda on AWS\n"
	cd dss-blau && \
	chalice deploy --no-autogen-policy

deploy-local:
	@echo "deploying AWS local\n"
	cd dss-blau && \
	chalice local

