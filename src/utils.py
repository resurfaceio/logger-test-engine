import yaml

import logging
import requests


def yaml_loader(yaml_path):
    with open(yaml_path, "r") as d:
        try:
            return yaml.safe_load(d)
        except yaml.YAMLError as exc:
            logging.error(f"There was an error {exc}")
            return None


def run_gql_query(url, query, headers=None):
    response = requests.post(url, json={"query": query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            "Query failed to run by returning code of {}. {}".format(
                response.status_code, query
            )
        )


def parse_args(request):

    if isinstance(request, dict):
        pass
    elif request.headers["content-type"] == "application/json":
        request = dict(request.get_json(silent=True))
    elif request.headers["content-type"] == "application/octet-stream":
        request = dict(json.loads(request.data))
    else:
        request = dict(json.loads(json.dumps(request)))
    return request
