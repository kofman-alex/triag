# TRIAG – A Rule Service for Member Activity Monitoring

## Getting Started

### Prerequisites

- Python 3.7 or later
- PostgreSQL 13

Install required packages:

```sh
pip install -r requirements.txt
pip install -r requirements_test.txt
```

### Setup

1. Create the database schema:

    ```sh
    cd setup
    SCHEMA=<schema> ./setup_in_schema.sh "postgresql://USER:PASSWORD@/DATABASE?host=UNIX_SOCKET_PATH"
    ```

    For example, for schema `test` in a ClodSQL PostgreSQL instance, running the command on MacOS is as follows:

    ```sh
    SCHEMA=test ./setup_in_schema.sh "postgresql://USER:PASSWORD@/DATABASE?host=/Users/USERNAME/cloudsql/CONNECTION_NAME"
    ```

2. Deploy the rules:

    ```sh
    cd setup
    SCHEMA=<schema> ./create_rules_in_schema.sh "postgresql://USER:PASSWORD@/DATABASE?host=UNIX_SOCKET_PATH"
    ```

### Running the rule service locally

```sh
export USER=<USER> 
export PASSWORD=<PASSWORD>
export DATABASE=<DATABASE>
export UNIX_SOCKET=<UNIX_SOCKET_PATH>
export SCHEMA=<SCHEMA>
python rule_service.py
```

To execute the rule set on the contents of the database:

```sh
curl http://127.0.0.1:8080/execute_ruleset
```

The valid response would be:

```json
{"status":"OK"}
```

### Testing

Testing the rule engine and rules correctness:

```sh
export USER=<USER> 
export PASSWORD=<PASSWORD>
export DATABASE=<DATABASE>
export UNIX_SOCKET=<UNIX_SOCKET_PATH>
export SCHEMA=<SCHEMA>
pytest
```

Instead of environment variables, the configuration can also be specified in a json file (see [example](config.template.json)).
The command line would be as follows:

```sh
pytest [--config=<config file>]
```

if `--config` option not explicitly set, then the default path is `secrets/config.json`.

## Trigger a remote rule service

A remote instance of the rule service can be invoked by a GET HTTP request, as follows:

```sh
curl https://host:port/execute_ruleset
```

## Command Line Tool

You can use the `triagctl` command line tool to manage and test the service.

Run `python triagctl --help` to see the syntax and the available commands.

```sh
usage: triagctl.py [-h] [--config CONFIG] [--command COMMAND]
                   [--user_id USER_ID] [--ts TS] [--type TYPE]
                   [--description DESCRIPTION] [--debug] [--scenario SCENARIO]

TRIAG Command Line Tool

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       Configuration file (JSON)
  --command COMMAND     Command ["add-event | get-events | get-alerts |
                        create-scenario | clear-events | clear-alerts | clear-
                        all"]
  --user_id USER_ID     User ID
  --ts TS               Timestamp (yyyy-mm-ddThh:mm:ss)
  --type TYPE           Event type
  --description DESCRIPTION
                        Event description
  --debug               Print debug information
  --scenario SCENARIO   Name of the scenario to create: inactivity | missing-
                        medication | pro-deterioration | activity-endorsement
```

For example of the config file see [config.json](config.template.json) template.

## Architecture

See the [architecture overview](docs/architecture.md) document.
