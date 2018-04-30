from future import standard_library
standard_library.install_aliases()
import json, argparse
from urllib.request import urlopen, Request
from hca.dss import DSSClient

parser = argparse.ArgumentParser(description='Process options the finder of golden bundles.')
parser.add_argument('--dss-host', dest='dss_host', action='store',
                    default='https://commons-dss.ucsc-cgp-dev.org/v1',
                    help='The url for the storage system.')
parser.add_argument('--indexer-url', dest='indexer_url', action='store',
                    default='https://3kymd03wdj.execute-api.us-west-2.amazonaws.com/api/',
                    help='The indexer URL')
parser.add_argument('--replica', dest='replica', action='store', default='aws', required=False,
                    help='The replica to use (aws, gcp)')
parser.add_argument('--bundle-uuid-prefix', dest='bundle_uuid_prefix', action='store', required=True,
                    help='Prefix of bundle UUIDs to be loaded')
args = parser.parse_args()


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
    bundle_id = result_entry['bundle_fqid']
    bundle_uuid = bundle_id[:36]
    bundle_version = bundle_id[37:]
    return bundle_uuid, bundle_version


def main():
    dss_client = DSSClient()
    dss_client.host = args.dss_host
    # bundle_query = {"query": {"wildcard": {"uuid": args.bundle_uuid_prefix}}}
    bundle_query = {
        "query": {
            "bool": {
                "must": [{
                    "regexp": {
                        "files.metadata_json.core.schema_url": ".*/1.2.1/.*"
                    }
                },
                    {
                        "wildcard": {
                            "uuid": args.bundle_uuid_prefix
                        }
                    }
                ]
            }
        }
    }
    bundles_found = 0
    bundles_loaded = 0
    bundle_load_failed = []
    for result in dss_client.post_search.iterate(es_query=bundle_query, replica=args.replica, output_format="summary"):
        bundles_found += 1
        bundle_uuid, bundle_version = parseResultEntry(result)
        print(f"Loading bundle: {bundle_uuid}.{bundle_version}")
        headers = {"content-type": "application/json"}
        post_payload = json.dumps({ "query": { "query": { "match_all":{}} }, "subscription_id": "ba50df7b-5a97-4e87-b9ce-c0935a817f0b", "transaction_id": "ff6b7fa3-dc79-4a79-a313-296801de76b9", "match": { "bundle_version": bundle_version, "bundle_uuid": bundle_uuid } })
        req = requestConstructor(args.indexer_url, headers, post_payload)
        try:
            # response = executeRequest(req)
            bundles_loaded += 1
        except Exception as e:
            bundle_load_failed.append(f"{bundle_uuid}.{bundle_version}")
            print (e)
    print(f"Total bundles with UUID prefix {args.bundle_uuid_prefix} found: {bundles_found}, loaded: {bundles_loaded}, failed: {len(bundle_load_failed)}")
    if bundle_load_failed:
        print(f"Bundles that failed to load: {bundle_load_failed}")


if __name__ == "__main__":
    main()
