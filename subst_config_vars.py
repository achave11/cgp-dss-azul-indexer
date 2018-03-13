#!/usr/bin/env python

import os
import json
import click
import boto3


@click.command()
@click.argument('lambda_name')
def subst_config_vars(lambda_name):
    """Obtain user values for AWS from environment variables. Then
    sustitute the value by updating config.json and write back
    to .chalice directory."""
    # Get AWS account number.
    iam = boto3.resource('iam')
    account_id = iam.CurrentUser().arn.split(":")[4]
    fname = lambda_name + '/.chalice/config.json'
    with open(fname, 'r') as fp:
        config = json.load(fp)
    # Get user-specific values.
    config['stages']['dev']['manage_iam_role'] = False  # encoded by json pack.
    config['stages']['dev']['iam_role_arn'] = ('arn:aws:iam::' + account_id +
                                               ':role/' + lambda_name + '-dev')
    es_endpoint = os.environ["ES_ENDPOINT"]
    blue_box_endpoint = os.environ["BLUE_BOX_ENDPOINT"]
    es_index = os.environ["ES_INDEX"]
    indexer_name = lambda_name
    home = '/tmp'
    # Create dict from those.
    config_keys = ['ES_ENDPOINT', 'BLUE_BOX_ENDPOINT',
                   'ES_INDEX', 'INDEXER_NAME', 'HOME']
    config_vars = [es_endpoint, blue_box_endpoint,
                   es_index, indexer_name, home]
    config_params = dict(zip(config_keys, config_vars))
    config['stages']['dev']['environment_variables'] = config_params
    with open(fname, 'w') as fp:
        json.dump(config, fp)


if __name__ == '__main__':
    subst_config_vars()
