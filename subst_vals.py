#!/usr/bin/env python

import os
import json
import click
import boto3
import requests
import sys


# Get AWS account details.
iam = boto3.resource('iam')
account_id = iam.CurrentUser().arn.split(":")[4]


@click.command()
@click.argument('lambda_name')
def subst_config_vals(lambda_name):
    """Obtain user values for AWS from environment variables. Then
    sustitute the value by updating config.json and write back
    to .chalice directory."""
    global lambda_name
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
        json.dump(config, fp, ensure_ascii=False)


def subst_policy_vals():
    """Let user substitute variables of the IAM policy and attaches the
    policy to the lambda."""
    policy_fname = 'policies/lambda-policy.json'
    with open(policy_fname, 'r') as fp:
        policy = json.load(fp)

    # First item in list: Principal.
    val = policy['Statement'][0]['Principal']['AWS']
    val = val.replace("<AWS-account-ID>", account_id)
    policy['Statement'][0]['Principal']['AWS'] = val

    # First item in list: Resource.
    val = policy['Statement'][0]['Resource']
    es_domain_name = lambda_name + '-elasticsearch'
    val = val.replace('<your-es-domain-name>', es_domain_name)
    policy['Statement'][0]['Resource'] = val

    # Second item in list: Resource (first item).
    val = policy['Statement'][1]['Resource'][0]
    val = val.replace("<AWS-account-ID>", account_id)
    val = val.replace('<your-es-domain-name>', es_domain_name)
    policy['Statement'][1]['Resource'][0] = val

    # Second item in list: Resource (second item).
    val = policy['Statement'][1]['Resource'][1]
    val = val.replace("<AWS-account-ID>", account_id)
    val = val.replace("<your-indexer-lambda-domain-name>", account_id)
    policy['Statement'][1]['Resource'][1] = val

    # Include public IP address.
    policy['Statement'][1] \
        ['Condition']['IpAddress'] \
        ['aws:SourceIp'][0] = get_ip()

    return policy


def get_ip():
    """Returns public IP address of host.
    :return ip:
    """
    try:
        response = requests.get('http://jsonip.com')
        response.raise_for_status()
        ip = response.json()['ip']
    except requests.exceptions.HTTPError as err:
        print(err)
        sys.exit(1)
    return ip


def main():
    subst_config_vals()
    subst_policy_vals()


if __name__ == '__main__':
    main()
