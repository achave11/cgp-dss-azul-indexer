#!/usr/bin/env python

import os
import json


def subst_config_vars():
    """Obtain user values for AWS from environment variables. Then
    sustitute the value by updating config.json and write back
    to .chalice directory."""

    fname = 'dss-blau/.chalice/config.json'
    # Get user-specific values.
    iam_role_arn = os.environ["IAM_ROLE_ARN"]
    es_endpoint = os.environ["ES_ENDPOINT"]
    blue_box_endpoint = os.environ["BLUE_BOX_ENDPOINT"]
    es_index = os.environ["ES_INDEX"]
    indexer_name = os.environ["INDEXER_NAME"]
    home = os.environ["HOME"]
    # Create dict from those.
    config_vars = [iam_role_arn, es_endpoint, blue_box_endpoint,
                   es_index, indexer_name, home]
    config_keys = ['IAM_ROLE_ARN', 'ES_ENDPOINT', 'BLUE_BOX_ENDPOINT',
                   'ES_INDEX', 'INDEXER_NAME', 'HOME']
    config_params = dict(zip(config_keys, config_vars))
    with open(fname, 'r') as fp:
        config = json.load(fp)
    config['stages']['dev'].update(config_params)
    with open(fname, 'w') as fp:
        json.dump(config, fp)


def main():
    subst_config_vars()


if __name__ == '__main__':
    main()
