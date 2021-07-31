# logger-test-engine

## Configurations
- `config.yaml`: This file contains the configurations for logger and it's test apps.
```yaml
loggername:
    apps:
        - name: name of test app
          url: URL to your serverless app # Leave this as it is if your are in development mode.

```

- `API.yaml`: This file contains the scripts to run in the test apps. Do not change this.

## Development
### Setup
- Get the resurface docker contaienr and relevant test apps.
- Setup python virtual env
- Install requirements
- Edit `settings.py` file as  per your setup.
- Edit `config.yaml` file as per your setup.

## Run
Run the engine (This will run the default logger engine i.e., python)
```
python -m src.engine
```
To change the logger engine pass following request param in the main function:

```
main({logger: "go"}) # to run the go engine
```