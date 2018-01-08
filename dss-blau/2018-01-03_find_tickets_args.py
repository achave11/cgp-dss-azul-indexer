# coding: utf-8

def requestConstructor(url, headers, data):
    '''
    Helper function to make requests to use on with urlopen()
    '''
    req = Request(url, data.encode('utf-8'))
    for key, value in list(headers.items()):
        req.add_header(key, value)

    return req


def executeRequest(req):
    '''
    Helper function to make the post request to the indexer
    '''
    f = urlopen(req)
    response = f.read()
    f.close()
    return response


def parseResultEntry(result_entry):
    '''
    Helper function to parse the results from a single results entry
    '''
    bundle_id = result_entry['bundle_id']
    bundle_uuid = bundle_id[:36]
    bundle_version = bundle_id[37:]
    return (bundle_uuid, bundle_version)
headers = {"accept": "application/json",
               "content-type": "application/json"}
    data = json.dumps({"es_query":
                       {"query":
                        {"match":
                         {"files.project_json.content.core.schema_version": "4.6.1"}}}})
    req = requestConstructor(args.dss_url, headers, data)
    response = executeRequest(req)
    response = json.loads(response)
headers = {"accept": "application/json",
           "content-type": "application/json"}
data = json.dumps({"es_query":
                   {"query":
                    {"match":
                     {"files.project_json.content.core.schema_version": "4.6.1"}}}})
req = requestConstructor(args.dss_url, headers, data)
response = executeRequest(req)
response = json.loads(response)
                 
import json
headers = {"accept": "application/json",
           "content-type": "application/json"}
data = json.dumps({"es_query":
                   {"query":
                    {"match":
                     {"files.project_json.content.core.schema_version": "4.6.1"}}}})
req = requestConstructor(args.dss_url, headers, data)
response = executeRequest(req)
response = json.loads(response)
                 
headers = {"accept": "application/json",
           "content-type": "application/json"}
data = json.dumps({"es_query":
                   {"query":
                    {"match":
                     {"files.project_json.content.core.schema_version": "4.6.1"}}}})
req = requestConstructor(args.dss_url, headers, data)
response = executeRequest(req)
response = json.loads(response)
                 
import argparse
parser = argparse.ArgumentParser(description='Process options the finder of golden bundles.')
#parser.add_argument('--assay-id', dest='assay_id', action='store',
#                    default='Q3_DEMO-assay1', help='assay id')
parser.add_argument('--dss-url', dest='dss_url', action='store',
                    default='https://dss.staging.data.humancellatlas.org/v1/search?replica=aws',
                    help='The url for the storage system.')
                    
parser.add_argument('--indexer-url', dest='repoCode', action='store',
                    default='https://1hkr6s0hsf.execute-api.us-west-2.amazonaws.com/api/',
                    help='none')
                    
args = parser.parse_args()
args
get_ipython().run_line_magic('save', '2018-01-03_find_tickets_args')
