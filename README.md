# dss-azul-indexer

This is the indexer that consumes events from the blue box and indexes them into Elasticsearch.

## Getting Started

### Blue Box 

It is required to know the blue box endpoint. See here for instructions: https://github.com/HumanCellAtlas/data-store/tree/master

### Elasticsearch (ES)

Create an Elasticsearch box on AWS. 
On the AWS console click "Services," then click "Elasticsearch Service." Then click "Create a new domain." Assign a domain name to the ES instance (eg: "dss-sapphire"). Choose your configuration for your requirements.
For the Access Policy, copy the contents of policies/elasticsearch-policy.json and edit the places with `<>`
To find your `<AWS-account-ID>`, click "Select a Template" and click "Allow or deny access to one or more AWS accounts or IAM users". Then a pop-up will appear with your "AWS account ID".
Take note of the Elasticsearch endpoint.

### Configure AWS and create a Virtual Environment
Install python3.

Create a virtual environment with `virtualenv -p python3 <envname>` and activate with `source <envname>/bin/activate`.

Install and configure the AWS CLI with your credentials
```
pip install awscli --upgrade
aws configure
```

### Chalice

Chalice is similar to Flask but is serverless and uses AWS Lambda.
```
pip install chalice
chalice new-project
```
When prompted for project name, input `<your-indexer-lambda-application-name>`, (e.g., dss-indigo).

Change the working directory to the newly created folder `<your-indexer-lambda-application-name>` (e.g., dss-indigo) and execute `chalice deploy`. Record the URL returned in the last line of stdout returned by this command - henceforth referred to as `<callback_url>`. This will create an AWS Lambda function called `dss-indigo` which will be updated using `chalice deploy`. Chalice automatically generated a folder `chalicelib/` and the files `rm app.py` and `rm requirements.txt`. Overwrite those by copying `app.py`, `requirements.txt` and `chalicelib/` from this repo and to the dss-indigo folder. Then execute

`pip install -r requirements.txt`

### Config File

`chalicelib/config.json` should contain the keys that you wish to add to the index documents. The structure of the config.json should mimic the metadata json file being looked at.

For example, the following metadata for assay.json:
```
{
  "rna": {
    "primer": "random"
  },
  "seq": {
    "machine": "Illumina HiSeq 2000",
    "molecule": "total RNA",
    "paired_ends": "no",
    "prep": "TruSeq"
  },
  "single_cell": {
    "method": "mouth pipette"
  },
  "sra_experiment": "SRX129997",
  "sra_run": [
    "SRR445718"
  ],
  "files": [
    {
      "name": "SRR445718_1.fastq.gz",
      "format": ".fastq.gz",
      "type": "reads",
      "lane": 1
    }
  ]
}
```
and this cell.json
```
{
  "type": "oocyte",
  "ontology": "CL_0000023",
  "id": "oocyte #1"
}
```
Could have a config like such:
```
{
  "assay.json": [
    {
      "rna": [
        "primer"
      ]
    },
    {
      "single_cell": [
        "method"
      ]
    },
    "sra_experiment",
    {
      "files":[
        "format"
      ]
    }
  ],
  "cell.json":[
    "type",
    "ontology",
    "id"
  ]
 }
```
***NOTE***: The config should be rooted under a version of the metadata being received.

In Elasticsearch, the fields for the File Indexer will be
```
assay,json|rna|primer
assay,json|single_cell|method
assay,json|sra_experiment
assay,json|files|format
cell,json|type
cell,json|ontology
cell,json|id
```
Notice the commas(,) where there were previously periods(.). Also, the pipe (|) is used as the separator between levels in the config.

#### Adding Mappings
Given a config:
```
{
  "cell.json":[
    "type",
    "ontology",
    "id"
  ]
 }
```

### Environment Variables
In order to add environmental variables to Chalice, the variables must be added to three locations.
Do not add protocols to any of the Endpoints. Make sure the ES_ENDPOINT does not have any trailing slashes.

1) Edit Chalice  
open `.chalice/config.json`  
Replace the current file with the following, making sure to replace the <> with your information.  
```
{
  "version": "2.0",
  "app_name": "<your-indexer-lambda-application-name>",
  "stages": {
    "dev": {
      "api_gateway_stage": "api",
      "manage_iam_role":false,
      "iam_role_arn":"arn:aws:iam::<AWS-account-ID>:role/<your-indexer-lambda-application-name>-dev",
      "environment_variables": {
         "ES_ENDPOINT":"<your elasticsearch endpoint>",
         "BLUE_BOX_ENDPOINT":"<your blue box>",
         "ES_INDEX":"<elasticsearch index to use>",
         "INDEXER_NAME":"<your-indexer-lambda-application-name>",
         "HOME":"/tmp"
      }
    }
  }
}
```   

2) Edit .profile
open `~/.profile` and add the following items.

```
export ES_ENDPOINT=<your elasticsearch endpoint>
export BLUE_BOX_ENDPOINT=<your blue box>
export ES_INDEX=<elasticsearch index to use>
export INDEXER_NAME=<your-indexer-lambda-application-name>
export HOME=/tmp
```

run `. ~/.profile` to load the variables

3) Edit Lambda

Go to the AWS console, and then to your Lambda function and add the following environment variables:

```
ES_ENDPOINT  -->   <your elasticsearch endpoint>
BLUE_BOX_ENDPOINT   -->   <your blue box>
ES_INDEX  -->  <elasticsearch index to use>
INDEXER_NAME  -->  <your-indexer-lambda-application-name>
HOME --> /tmp
```

### Elasticsearch & Lambda

Given the current configuration, a deployment will result in errors when attempting to reach Elasticsearch. This is because Lambda is not configured to allow ES actions.

Open the AWS console and go to IAM. On the side menu bar, chose roles, then choose your lambda function, `<your-indexer-lambda-application-name>` and under "Policy name" click the drop down, then click on "Edit Policy". Add the policy found in lambda-policy.json under the `policies` folder, making sure to change the `Resource` value to the ARN of your elasticsearch box.

### Deploy Chalice

Enter your directory of your chalice function and `chalice deploy --no-autogen-policy`. Since we have created a policy in AWS we do not want chalice to automatically create a policy for us.

Your `<callback_url>` should be able to take post requests from the Blue Box and index the resulting files 
This is untested, but can take in a simulated curl request of the following format.
```
curl -H "Content-Type: application/json" -X POST -d '{ "query": { "query": { "bool": { "must": [ { "match": { "files.sample_json.donor.species": "Homo sapiens" } }, { "match": { "files.assay_json.single_cell.method": "Fluidigm C1" } }, { "match": { "files.sample_json.ncbi_biosample": "SAMN04303778" } } ] } } }, "subscription_id": "ba50df7b-5a97-4e87-b9ce-c0935a817f0b", "transaction_id": "ff6b7fa3-dc79-4a79-a313-296801de76b9", "match": { "bundle_version": "2017-08-03T041453.170646Z", "bundle_uuid": "4ce8a36d-51d6-4a3c-bae7-41a63699f877" } }' <callback_url> 
```

### Methods and Endpoints

|  Methods/Endpoints | Notes |
| ------------- | ------------- |
| `<callback_url>`/  | takes in a post request and indexes the bundle found in the request   |
| es_check() |  returns the ES info, good check to make sure Chalice can talk to ES  |

### Manual Loading

Download and expand import.tgz from Data-Bundle-Examples: https://github.com/HumanCellAtlas/data-bundle-examples/blob/master/import/import.tgz
Download the test/local-import.py file from this repo. Create an environmental variable `BUNDLE_PATH` that points to the import.tgz files. (Note: There are thousands of files in import.tgz, can specify parts of bundles to download: `import/geo/GSE67835` or `import/geo` or `import`)
Add environmental variable `ES_ENDPOINT` which points to your ES box or have a localhost running. Optionally, create the name of the ES index to add the files to with the environmental variable `ES_INDEX` (default index is `test-import`)
Required to have a config.json (like the one in `chalicelib/config.json`)

Run `local-import.py`. Open Kibana to see your files appear. The

Note: Manual loading creates mappings for ES, has some list parsing capability, and if `key` in config.json does not exist, returns a value of "no `key`". (This functionality is not present in the Chalice function yet)

### Todo List

* how to setup Kibana for security group reasons
* how to run find-golden-tickets.py
* improve mappings to Chalice
* list handling in json files
* cron deduplication
* capibility to download files that are not json
* multiple version handling (per file version or per file?)
* Unit testing: Flask mock up of the Blue Box endpoints
    * We need something that will generate POSTS to the lambda, such as a shell script.
    * Flask has endpoints for looking up bundles, and get a particular manifest.
    * Assume  bundles uuid always exist. generate a request to download anything indexable ? 
* Improve debugging (config for turning on/off debug)

## Automated Deployment
You can use `make` to create a ElasticSearch service, chalice lambda and set everything up. The `Makefile` can take in `STAGE=<STAGE_VALUE>` as an input for different stages when deploying `chalice`. 

Before you run `make`, you will need to setup the prerequisites. 

### Prerequisities to run `make`
You will need to update the `config/elasticsearch-policy.json` file to enter your desired domain name, lambda name and the IP address. 
Next, you will need to update the `config/config.env` file and apply all the values. The ```
BB_ENDPOINT=dss.staging.data.humancellatlas.org/v1
ES_INDEX=test-import
```
values are pre-filled by default. 

If you've an existing ElasticSearch service instance, you should fill in the following values:
```
ES_DOMAIN_NAME=
ES_ENDPOINT=
ES_ARN=
```

If you don't supply the `ES_ENDPOINT` value, the `make` file will automatically create a new ElasticSearch instance. 

The `config/elasticsearch-config.json` and `config/ebs-config.json` files can be modified to change the shape of the ElasticSearch service instance and ElasticSearch Beanstalk. 

Once `make` finishes successfully, you can find all the required environment variables' values in `values_generated.txt`

You will need to export these values to your `~/.profile`
