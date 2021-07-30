import json
import logging

import yaml


def yaml_loader(yaml_path):
    with open(yaml_path, "r") as d:
        try:
            return yaml.safe_load(d)
        except yaml.YAMLError as exc:
            logging.error(f"There was an error {exc}")
            return None


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
