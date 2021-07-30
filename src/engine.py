from utils import yaml_loader, run_gql_query
import requests
import json

payloads = yaml_loader("API.yaml")["payloads"]

placeholder = "RESURFACE_PLACEHOLDER"
original_val = "localhost:8000"


def main():
    results = []
    msg = None
    response = None

    for payload in payloads:
        URL = payload.get("url").replace(placeholder, original_val)
        try:
            if payload.get("type", None) == "GQL":
                response = run_gql_query(
                    url=URL,
                    query=payload.get("request_body"),
                )
            else:
                response = requests.get(URL).json()
            msg = "Request completed succesfully!"
        except Exception as e:
            msg = e

        results.append(
            {
                "url": URL,
                "message": msg,
                "success": (
                    json.dumps(json.loads(payload.get("response_body")))
                    == json.dumps(response)
                ),
            }
        )
    return results, all(x["success"] for x in results)


if __name__ == "__main__":
    _, all_good = main()
    print(_)