import asyncio
import json
import sys
import time
from pprint import pformat

import argh
import httpx
from werkzeug import Response

from . import ENGINE_ID, connect_db, generate_app_id
from .queries import fetch_data
from .settings import CONFIG_DIR, IS_DEV, LOCAL_URL, logger
from .utils import parse_args, safe_json, wake_apps, yaml_loader

# from typing import Optional


payloads = yaml_loader(CONFIG_DIR / "API.yaml")["payloads"]
loggers = yaml_loader(CONFIG_DIR / "config.yaml")


placeholder = "RESURFACE_PLACEHOLDER"


def create_task(app, app_id):
    msg = "Request completed succesfully!"
    task = None
    results = []

    headers = {"Resurface-App-Id": app_id}

    for i, payload in enumerate(payloads):
        try:
            method_ = payload.get("method", "GET")
            url_ = payload.get("url").replace(
                placeholder, LOCAL_URL if IS_DEV else app.get("url")
            )
            logger.info(f"Running url '{url_}' for app '{app.get('name')}'")
            if payload.get("type", None) == "GQL":
                task = httpx.post(
                    url_,
                    json={"query": payload.get("request_body")},
                    headers=headers,
                    timeout=None,
                )
            elif str(method_).upper() == "GET":
                task = httpx.get(url_, headers=headers, timeout=None)
            else:
                task = httpx.post(
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
            _extracted_from_test_with_db_5(cnn, app_id, results)
    except Exception as e:
        logger.error(
            "There was some issue with DB test. Ignoring the DB test for now. See logs for more details."
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


def _extracted_from_test_with_db_5(cnn, app_id, results):
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
            res_body_ok = json.dumps(json.loads(safe_json(data[2]))) == json.dumps(
                json.loads(payloads[i].get("response_body"))
            )
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


def main(request=None, app_name=None):
    if request is None:
        request = {"logger": "python"}

    if isinstance(request, str):
        logger_ = request
    else:
        request_params = parse_args(request)
        logger_ = request_params.get("logger")

    if not logger_:
        return Response(json.dumps({"status": "option"}), 204)
    logger.info(f"Running test for '{logger_}' logger with engine ID: '{ENGINE_ID}'")
    if app_name is None:
        test_apps = loggers.get(str(logger_).lower())["apps"]
    else:
        test_apps = [app_name]

    logger.info(f"There are/is {len(test_apps)} test app(s) for '{logger_}' logger")

    # Wake sleeping apps
    if not IS_DEV:
        logger.info("waking up sleeping apps")
        try:
            asyncio.run(wake_apps([x.get("url") for x in test_apps]))
        except Exception:
            pass

    all_all_good = []

    for app in test_apps:
        app_id = generate_app_id()

        try:
            task_response = create_task(app, app_id)
        except Exception:
            task_response = [{"success": False}]
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
        all_all_good.append(all_good)

    return Response(
        json.dumps({"status": "success" if all(all_all_good) else "failure"}),
        200 if all(all_all_good) else 400,
    )


def cli():
    print(
        """
.  . .  .  . .  .  . .  .  . .  .  . .  .  . .  
.       .       .       .       .       .     .
    .  .    .  .    .  .   . . .    .  .    .    
.       .       .       . @8: .  .      .     .  
.  .    .  .    .  .  . t8 @ 8 .   .    .  .  .
.    .  .    .  .    .  . %8X@X8:..   .   .     
.       .       .     . :88@XS@8;.    .    .  
.   . .    .  .    .  .  ..8X8@@@X8  .     .   .
.     .    .  .         :88X88@@ S..   .   .  
.    .   .       .  .  .. t88 : 88888 .         
    .   .   .  .    .         : %8@8X8  . .  . . 
.    .      .   .    .   .   . 8%@@XS  .        
.    . .. .. . . .  . .  ..88S@8@8@S .  .  .  
.   . .:X8@8    888@XS S 8S8@@@@8XSSX8 .   .   .
.   88 8888    88XSXX@XSX@@@8@8@8@8  . .      
.  . %@88@@@8 888@8@@@@@@@@@8@888888 ;.     .   
    . %8  8:8S88 888X@@8@@8@@@88 888@; .  .    . 
.   . @ tSS  ;88@  8S8@@@@@888 ;88@8..     .    
.   X88t888t :8@88@@@@8@88@888888;.  . .   .  
.   .   888:88888:S8888S@@88XS888 :.       .    
        .; 8@X t8@888%8888@@@8@XX@88S . .      . 
.  .        8888S  ;8X8S8@8@XX@@@@8@;:   . .    
.     .   :t XX8888888@@88        . ..      .  
    .         :%%%  t8@@XtXX@    :.   . . .     
.  .  .          ..    88888X;    ..    .    .   
            .       :          .. .     .   . 
.  .  .          .   .            .   . .       
    █▀█ █▀▀ █▀ █░█ █▀█ █▀▀ ▄▀█ █▀▀ █▀▀
    █▀▄ ██▄ ▄█ █▄█ █▀▄ █▀░ █▀█ █▄▄ ██▄
"""
    )
    argh.dispatch_command(main)


if __name__ == "__main__":
    loggername = {"logger": sys.argv[1]} if len(sys.argv) > 1 else None
    res = main(loggername)
    print(res)
    sys.exit(0) if res.status_code == 200 else sys.exit(1)
