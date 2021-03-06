#SET NEW_ELASTICSEARCH='N' if passing in an existing service or NEW_ELASTICSEARCH='Y' if you want it to be setup as well
SHELL=/bin/bash
include config/config.env
export $(shell sed 's/=.*//' config/config.env)

PYTHON := $(shell command -v python3 2> /dev/null)
STAGE ?= development

all: setup_elasticsearch

setup_virtual_env:
	#create the virtualenv - NOTE: source cannot be activated within a makefile
	@if [$(PYTHON) == '']; then	sudo apt-get update && sudo apt-get install python3.6; fi
	virtualenv -p python3 $(VIRTUALENV_NAME)

configure_aws: setup_virtual_env
	#install AWS CLI within the virtualenv
	$(VIRTUALENV_NAME)/bin/pip install awscli --upgrade
	#aws configure cli does not support passing in access key ID and secret access key as parameters
	export AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID)
	export AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY)

setup_chalice: configure_aws
	#install chalice
	$(VIRTUALENV_NAME)/bin/pip install chalice
	#create a chalice project
	$(VIRTUALENV_NAME)/bin/chalice new-project $(CHALICE_PROJECT)
	#inital deploy of chalice project
	cd $(CHALICE_PROJECT) && ../$(VIRTUALENV_NAME)/bin/chalice deploy --profile $(AWS_PROFILE) --stage $(STAGE) >output_log.txt
	#obtain the url of the newly deployed chalice lambda
	$(eval CHALICE_URL=$(shell grep -o 'https://[0-9a-zA-Z.-]*/api/' ${CHALICE_PROJECT}/output_log.txt))

update_chalice_with_default_files: 
	@if [ ! -d "${VIRTUALENV_NAME}" && -f "${CHALICE_PROJECT}/output_log.txt" ]; then $(MAKE) setup_chalice; fi
	#copy files from the repo and update chalice
	cd $(CHALICE_PROJECT) && rm app.py && rm requirements.txt
	cp -a chalicelib/. $(CHALICE_PROJECT)/
	cp app.py $(CHALICE_PROJECT)/
	cp requirements.txt $(CHALICE_PROJECT)/
	#install requirements
	cd $(CHALICE_PROJECT) && ../$(VIRTUALENV_NAME)/bin/pip install -r requirements.txt

edit_env_variables: update_chalice_with_default_files
	#change the config file of chalice and replace with right values
	$(eval ES_ENDPOINT = $(shell ${VIRTUALENV_NAME}/bin/aws es --profile ${AWS_PROFILE} describe-elasticsearch-domain --domain-name \
	$(ES_DOMAIN_NAME) | jq ".DomainStatus.Endpoint"))
	cd $(CHALICE_PROJECT) && rm .chalice/config.json && cp ../config/chalice/config.json .chalice/ && cd .chalice &&\
	rpl '<INDEXER_LAMBDA_APPLICATION_NAME>' '${CHALICE_PROJECT}' config.json && rpl '<INDEX_TO_USE>' '${ES_INDEX}' config.json &&\
	rpl '<AWS_ACCOUNT_ID>' '${AWS_ACCOUNT_ID}' config.json && rpl '<ELASTICSEARCH_ENDPOINT>' '${ES_ENDPOINT}' config.json &&\
	rpl '<BB_ENDPOINT>' '${BB_ENDPOINT}' config.json
	#update lambda's environment variables
	$(VIRTUALENV_NAME)/bin/aws lambda --profile $(AWS_PROFILE) update-function-configuration \
	--function-name "$(CHALICE_PROJECT)-$(STAGE)" --environment "Variables={ES_ENDPOINT=$(ES_ENDPOINT),BLUE_BOX_ENDPOINT=$(BB_ENDPOINT),\
	ES_INDEX=$(ES_INDEX),INDEXER_NAME=$(CHALICE_PROJECT),HOME=/tmp}"

change_es_lambda_policy: edit_env_variables
	#edit elasticsearch and lambda policy
	$(eval ES_ARN = $(shell ${VIRTUALENV_NAME}/bin/aws es --profile ${AWS_PROFILE} describe-elasticsearch-domain --domain-name \
	$(ES_DOMAIN_NAME) | jq ".DomainStatus.ARN"))
	rpl '<ELASTICSEARCH_ARN>' '${ES_ARN}' config/lambda-policy.json
	$(VIRTUALENV_NAME)/bin/aws iam --profile $(AWS_PROFILE) update-assume-role-policy --role-name "$(CHALICE_PROJECT)-$(STAGE)" --policy-document file://"config/lambda-policy.json"

redeploy_chalice: change_es_lambda_policy
	#redeploy chalice
	cd $(CHALICE_PROJECT) && ../$(VIRTUALENV_NAME)/bin/chalice deploy --no-autogen-policy --stage $(STAGE)
	#write generated URLs and config values to a file for easy reference
	$(eval ES_ENDPOINT = $(shell ${VIRTUALENV_NAME}/bin/aws es --profile ${AWS_PROFILE} describe-elasticsearch-domain --domain-name \
	$(ES_DOMAIN_NAME) | jq ".DomainStatus.Endpoint"))
	$(eval ES_ARN = $(shell ${VIRTUALENV_NAME}/bin/aws es --profile ${AWS_PROFILE} describe-elasticsearch-domain --domain-name \
	$(ES_DOMAIN_NAME) | jq ".DomainStatus.ARN"))
	$(eval CHALICE_URL=$(shell grep -o 'https://[0-9a-zA-Z.-]*/api/' ${CHALICE_PROJECT}/output_log.txt))
	echo "CALLBACK_URL="$(CHALICE_URL) "\n" "ES_ENDPOINT="$(ES_ENDPOINT) "\n" "BLUE_BOX_ENDPOINT="$(BB_ENDPOINT) "\n" \
	"ES_INDEX="$(ES_INDEX) "\n" "INDEXER_NAME="$(CHALICE_PROJECT) "\n" "HOME=/tmp" > values_generated.txt

setup_elasticsearch:
	#if Elasticsearch endpoint supplied, use it. If not, setup a new elasticsearch service instance
	@if [ -z "$(ES_ENDPOINT)" ]; then \
		$(MAKE) new_elasticsearch; \
	else $(MAKE) redeploy_chalice; fi;\

new_elasticsearch: setup_chalice
	#create new elasticsearch service domain
	$(VIRTUALENV_NAME)/bin/aws es --profile $(AWS_PROFILE) create-elasticsearch-domain --domain-name "$(ES_DOMAIN_NAME)" \
	--elasticsearch-cluster-config  file://"config/elasticsearch-config.json" \
	--access-policies file://"config/elasticsearch-policy.json" \
	--ebs-options file://"config/ebs-config.json" 
	
	#pause to give AWS extra seconds to get it configured
	sleep 60
	#obtain elasticsearch end-point - takes 10 minutes to setup on AWS. Check every 2 minutes
	./poll_elasticsearch.sh "$(VIRTUALENV_NAME)" "$(AWS_PROFILE)" "$(ES_DOMAIN_NAME)"
	$(eval ES_ENDPOINT = $(shell ${VIRTUALENV_NAME}/bin/aws es --profile ${AWS_PROFILE} describe-elasticsearch-domain --domain-name \
	$(ES_DOMAIN_NAME) | jq ".DomainStatus.Endpoint"))
	$(eval ES_ARN = $(shell ${VIRTUALENV_NAME}/bin/aws es --profile ${AWS_PROFILE} describe-elasticsearch-domain --domain-name \
	$(ES_DOMAIN_NAME) | jq ".DomainStatus.ARN"))
	$(MAKE) redeploy_chalice

clean:
	#delete elasticsearch domain
	$(VIRTUALENV_NAME)/bin/aws es --profile $(AWS_PROFILE) delete-elasticsearch-domain --domain-name $(ES_DOMAIN_NAME)
	#delete chalice lambda
	cd $(CHALICE_PROJECT) && ../$(VIRTUALENV_NAME)/bin/chalice delete --stage $(STAGE)
	#clean all local files
	rm -r $(CHALICE_PROJECT)
	rm -r $(VIRTUALENV_NAME)
	rm eq_endpoint.txt
	rm values_generated.txt