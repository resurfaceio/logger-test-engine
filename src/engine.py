import asyncio
import json
import time
import sys
import httpx as requests

from pprint import pformat
from .settings import BASEDIR, logger, IS_DEV, LOCAL_URL
from .utils import parse_args, yaml_loader, safe_json, wake_apps
from . import generate_app_id, connect_db, ENGINE_ID
from .queries import fetch_data
from werkzeug import Response


payloads = yaml_loader(BASEDIR / "API.yaml")["payloads"]
loggers = yaml_loader(BASEDIR / "config.yaml")


placeholder = "RESURFACE_PLACEHOLDER"


def create_task(app, app_id):
    msg = "Request completed succesfully!"
    task = None
    results = []

    headers = {"Resurface-Engine-Id": app_id}

    for i, payload in enumerate(payloads):
        try:
            method_ = payload.get("method", "GET")
            url_ = payload.get("url").replace(
                placeholder, LOCAL_URL if IS_DEV else app.get("url")
            )
            logger.info(f"Running url '{url_}' for app '{app.get('name')}'")
            if payload.get("type", None) == "GQL":
                task = requests.post(
                    url_,
                    json={"query": payload.get("request_body")},
                    headers=headers,
                    timeout=None,
                )
            elif str(method_).upper() == "GET":
                task = requests.get(url_, headers=headers, timeout=None)
            else:
                task = requests.post(
                    url_,
                    data=payload.get("request_body"),
                    headers=headers,
                    timeout=None,
                )

            if task.status_code != payload.get("response_status"):
                results.append(
                    {
                        "payload_number": i,
                        "payload_descriptions": app.get("descriptions"),
                        "app": app.get("name"),
                        "message": str(task),
                        "success": False,
                    }
                )
            else:
                results.append(
                    {
                        "payload_number": i,
                        "payload_descriptions": app.get("descriptions"),
                        "app": app.get("name"),
                        "message": str(msg),
                        "success": (
                            json.dumps(json.loads(payload.get("response_body")))
                            == json.dumps(task.json())
                        ),
                    }
                )
        except Exception as e:
            results.append(
                {
                    "payload_number": i,
                    "payload_descriptions": app.get("descriptions"),
                    "app": app.get("name"),
                    "message": str(e),
                    "success": False,
                }
            )
    return results


def test_with_db(app_id):
    results = []
    try:
        with connect_db as cnn:
            curr = cnn.cursor()
            curr.execute(fetch_data.format(id_=app_id))
            logger.info("DB found running test against DB")
            time.sleep(2)
            rows = curr.fetchall()

            if not rows:
                results.append(
                    {
                        "payload_number": None,
                        "message": "Nothing was recorded in DB",
                        "success": False,
                    }
                )

            for i, data in enumerate(rows):

                d0 = None
                try:  # Hack to get query from GQL
                    d0 = safe_json(data[0])["query"]
                except Exception:
                    d0 = safe_json(data[0])

                req_body_ok = d0 == payloads[i].get("request_body", None)
                try:  # Hack to get str body
                    res_body_ok = json.dumps(
                        json.loads(safe_json(data[2]))
                    ) == json.dumps(json.loads(payloads[i].get("response_body")))
                except TypeError:
                    res_body_ok = json.dumps(safe_json(data[2])) == json.dumps(
                        json.loads(payloads[i].get("response_body"))
                    )
                results.append(
                    {
                        "payload_number": i,
                        "message": f"Testing {data} against DB",
                        "success": all([req_body_ok, res_body_ok]),
                    }
                )
    except Exception as e:
        logger.error(
            "There was some issue with DB test. \
                Ignoring the DB test for now. See logs for more details."
        )

        logger.error(e)
        results.append(
            {
                "payload_number": None,
                "message": "Exception on test against DB",
                "success": False,
            }
        )
    return results


def main(request=None):
    if request is None:
        request = {"logger": "python"}

    request_params = parse_args(request)
    logger_ = request_params.get("logger")
    if not logger_:
        return Response(json.dumps({"status": "option"}), 204)
    logger.info(f"Running test for '{logger_}' logger with engine ID: '{ENGINE_ID}'")
    test_apps = loggers.get(str(logger_).lower())["apps"]
    logger.info(f"There are/is {len(test_apps)} test app(s) for '{logger_}' logger")

    # Wake sleeping apps
    if not IS_DEV:
        logger.info("waking up sleeping apps")
        asyncio.run(wake_apps([x.get("url") for x in test_apps]))

    for app in test_apps:
        app_id = generate_app_id()

        task_response = create_task(app, app_id)
        logger.info(f"Init test against Resurface DB for '{logger_}' logger")

        # Had to wait to get data populated
        # Find some robust solution
        time.sleep(5)

        db_response = test_with_db(app_id)

        all_good = all(x["success"] for x in [*task_response, *db_response])

        if not all_good:
            logger.error(
                f"Some or all tests did not passed or engine ID: '{ENGINE_ID}'"
            )
            logger.error(pformat(task_response))
            logger.error(pformat(db_response))
        else:
            logger.info(
                f"All tests passed with db and payloads for engine ID: '{ENGINE_ID}'"
            )

    return Response(
        json.dumps({"status": "success" if all_good else "failure"}),
        200 if all_good else 400,
    )


if __name__ == "__main__":
    loggername = {"logger": sys.argv[1]} if len(sys.argv) > 1 else None
    res = main(loggername)
    print(res)
    sys.exit(0) if res.status_code == 200 else sys.exit(1)
