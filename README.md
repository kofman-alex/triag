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
USER=<USER> PASSWORD=<PASSWORD> DATABASE=<DATABASE> UNIX_SOCKET=<UNIX_SOCKET_PATH> SCHEMA=<SCHEMA> python rule_service.py
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
USER=<USER> PASSWORD=<PASSWORD> DATABASE=<DATABASE> UNIX_SOCKET=<UNIX_SOCKET_PATH> SCHEMA=<SCHEMA> pytest
```

## Architecture

See the [architecture overview](docs/architecture.md) document.
