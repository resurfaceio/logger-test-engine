import asyncio
import json
import logging
from ast import literal_eval

import httpx
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


def safe_json(data):

    if isinstance(data, dict):
        return data
    elif isinstance(data, str):
        try:
            data = literal_eval(data)
            if isinstance(data, list):
                return {k: v for k, v in data}
            return data
        except ValueError:

            return data
    else:
        return None


async def wake_apps(urls):
    async with httpx.AsyncClient() as client:
        tasks = (client.get(url, timeout=None) for url in urls)
        reqs = await asyncio.gather(*tasks)
    return [req.text for req in reqs]
