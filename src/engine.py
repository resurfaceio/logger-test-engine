import asyncio
import json

import httpx

from .settings import BASEDIR, logger
from .utils import parse_args, run_gql_query, yaml_loader

payloads = yaml_loader(BASEDIR / "API.yaml")["payloads"]
loggers = yaml_loader(BASEDIR / "config.yaml")

placeholder = "RESURFACE_PLACEHOLDER"
original_url = "localhost:8000"


async def create_task(payload, test_apps):
    msg = "Request completed succesfully!"
    task = None
    results = []

    async with httpx.AsyncClient() as requests:
        tasks = []
        for app in test_apps:
            url_ = payload.get("url").replace(placeholder, app.get("url"))
            logger.info(f"Running url '{url_}' for app '{app.get('name')}'")
            if payload.get("type", None) == "GQL":
                task = requests.post(url_, json={"query": payload.get("request_body")})

            else:
                task = requests.get(url_)

            tasks.append(task)

        reqs = await asyncio.gather(*tasks)

        for req in reqs:

            results.append(
                {
                    "url": url_,
                    "message": str(msg),
                    "success": (
                        json.dumps(json.loads(payload.get("response_body")))
                        == json.dumps(req.json())
                    ),
                }
            )
    return results


def main(request=None):
    results = []
    msg = None
    response = None
    if request is None:
        request = {"logger": "python"}

    request_params = parse_args(request)
    logger_ = request_params.get("logger")
    logger.info(f"Running test for '{logger_}' logger")
    test_apps = loggers.get(str(logger_).lower())["apps"]
    logger.info(f"There are {len(test_apps)} test apps for '{logger_}' logger")

    for payload in payloads:

        done, extra = asyncio.run(create_task(payload, test_apps))
        print(done)
        print(extra)


if __name__ == "__main__":
    main()
