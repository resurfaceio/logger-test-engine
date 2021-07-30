import asyncio
import json
from pprint import pformat

import httpx

from .settings import BASEDIR, logger
from .utils import parse_args, yaml_loader
from . import ENGINE_ID
from werkzeug import Response

# import trino


payloads = yaml_loader(BASEDIR / "API.yaml")["payloads"]
loggers = yaml_loader(BASEDIR / "config.yaml")
headers = {"Resurface-Engine-Id": ENGINE_ID}

placeholder = "RESURFACE_PLACEHOLDER"
# DB_CONN = trino.dbapi.connect(host="localhost", port=4000, user="admin")


async def create_task(app):
    msg = "Request completed succesfully!"
    task = None
    results = []

    headers = {}

    async with httpx.AsyncClient() as requests:
        tasks = []
        for payload in payloads:
            method_ = payload.get("method", "GET")
            url_ = payload.get("url").replace(placeholder, app.get("url"))
            logger.info(f"Running url '{url_}' for app '{app.get('name')}'")
            if payload.get("type", None) == "GQL":
                task = requests.post(
                    url_, json={"query": payload.get("request_body")}, headers=headers
                )
            elif str(method_).upper() == "GET":
                task = requests.get(url_, headers=headers)
            else:
                task = requests.post(
                    url_, data=payload.get("request_body"), headers=headers
                )

            tasks.append(task)

        reqs = await asyncio.gather(*tasks, return_exceptions=True)
        for i, req in enumerate(reqs):
            if not isinstance(req, httpx.Response):
                results.append(
                    {
                        "payload_number": i,
                        "app": app.get("name"),
                        "message": str(req),
                        "success": False,
                    }
                )
            else:

                results.append(
                    {
                        "payload_number": i,
                        "app": app.get("name"),
                        "message": str(msg),
                        "success": (
                            json.dumps(json.loads(payload.get("response_body")))
                            == json.dumps(req.json())
                        ),
                    }
                )
    return results


def main(request=None):
    if request is None:
        request = {"logger": "python"}

    all_all_good = []

    request_params = parse_args(request)
    logger_ = request_params.get("logger")
    logger.info(f"Running test for '{logger_}' logger with engine ID: '{ENGINE_ID}'")
    test_apps = loggers.get(str(logger_).lower())["apps"]
    logger.info(f"There are {len(test_apps)} test apps for '{logger_}' logger")

    for app in test_apps:

        cr_response = asyncio.run(create_task(app))
        logger.info(f"Running test against Resurface DB for '{logger_}' logger")
        all_good = all(x["success"] for x in cr_response)
        all_all_good.append(all_good)
        if not all_good:
            logger.error("Some or all tests did not passed!")
            logger.debug(pformat(cr_response))
    return Response(
        json.dumps({"status": "success" if all(all_all_good) else "failure"}),
        200 if all(all_all_good) else 400,
    )


if __name__ == "__main__":
    res = main()
    print(res)
