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

### Build the AWS Lambda to handle Blue Box notifications
Clone this repository and `cd dss-azul-indexer`. Run `ls -ls /usr/bin/python*` to check whether Python 3.6 is installed. If not install it. Next, create a virtual environment with `virtualenv --python=python3.6 <envname>` and activate it with `source <envname>/bin/activate`. Use your favorite editor to update the values for the Blue Box and Elasticsearch endpoints in the file `.env`. Do _not_ add protocols (e.g., `http://`) to any of the endpoints. Make sure the ES_ENDPOINT does not have any trailing slashes. Now run `make deploy`. This will ask for your AWS credentials, and a name for the AWS Lambda. It should finish by reporting the call-back URL of the newly created Lambda function, for instance `https://<someCode>.execute-api.us-west-2.amazonaws.com/api/`. 

To delete the Lambda run `make teardown`. When prompted enter the name of the Lambda that you want to delete. That should delete the API, the Lambda function, and the cloud watch events.

### Config File for the indexer

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
