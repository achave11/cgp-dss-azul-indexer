#!/usr/bin/env python

import os
import json
import click


@click.command()
@click.argument('lambda_name')
def subst_config_vars(lambda_name):
    """Obtain user values for AWS from environment variables. Then
    sustitute the value by updating config.json and write back
    to .chalice directory."""

    fname = lambda_name + '/.chalice/config.json'
    with open(fname, 'r') as fp:
        config = json.load(fp)
    # Get user-specific values.
    config['stages']['dev']['manage_iam_role'] = False  # encoded by json pack.
    config['stages']['dev']['iam_role_arn'] = os.environ["IAM_ROLE_ARN"]
    es_endpoint = os.environ["ES_ENDPOINT"]
    blue_box_endpoint = os.environ["BLUE_BOX_ENDPOINT"]
    es_index = os.environ["ES_INDEX"]
    indexer_name = os.environ["INDEXER_NAME"]
    home = os.environ["HOME"]
    # Create dict from those.
    config_keys = ['ES_ENDPOINT', 'BLUE_BOX_ENDPOINT',
                   'ES_INDEX', 'INDEXER_NAME', 'HOME']
    config_vars = [es_endpoint, blue_box_endpoint,
                   es_index, indexer_name, home]
    config_params = dict(zip(config_keys, config_vars))
    config['stages']['dev'].update(config_params)
    with open(fname, 'w') as fp:
        json.dump(config, fp)


if __name__ == '__main__':
    subst_config_vars()
