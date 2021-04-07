import pytest
import postgresql
import os
from datetime import datetime, timedelta
import rules

class TestRules():
    @pytest.fixture(scope='session', autouse=True)
    def config(self):
        _config = {
            'connectParams': {
                'user': os.environ.get('USER'),
                'password': os.environ.get('PASSWORD'),
                'database': os.environ.get('DATABASE'),
                'unix': os.environ.get('UNIX_SOCKET')
            },
            'schema': os.environ.get('SCHEMA')
        }
        yield _config

    @pytest.fixture(scope='class', autouse=True)
    def db_conn(self, config):
        db = postgresql.open(**config.get('connectParams'))
        yield db

        print('Closing the database connection...')
        db.close()
        print('Done.')

    @pytest.fixture(scope='class', autouse=True)
    def statements(self, db_conn, config):
        schema = config.get('schema')

        _statements = {
            'create_user': db_conn.prepare(f'insert into {schema}.users values ($1, $2, $3, $4)'),
            'add_event': db_conn.prepare(f'insert into {schema}.events (user_id, time, type, description) values($1, $2, $3, $4)'),
            'get_alerts_for_user': db_conn.prepare(f'select * from {schema}.alerts where user_id=$1')
        }

        yield _statements

    # FIXME need to take care of the schema which is currently not parameterized in the rules sql file
    # @pytest.fixture(scope='class', autouse=True)
    # def add_rules(self, db_conn, config):
    #     with open('./setup/create_rules.sql') as rules_sql_file:
    #         sql_commands = rules_sql_file.read().split(';')
    #         map(lambda cmd: db_conn.execute(cmd), sql_commands)

    #     yield
    #     trunc_rules = db_conn.prepare(f'truncate {config.get("schema")}.rules cascade')                


    @pytest.fixture(autouse=True)       
    def cleanup_tables(self, db_conn, config):
        yield
        trunc_events = db_conn.prepare(f'truncate {config.get("schema")}.events cascade')
        trunc_alerts = db_conn.prepare(f'truncate {config.get("schema")}.alerts cascade')
        trunc_users = db_conn.prepare(f'truncate {config.get("schema")}.users cascade')

        trunc_events()
        trunc_alerts()
        trunc_users()
    
    def test_alerts(self, db_conn, config):
        count_alerts = db_conn.prepare(f'select count(*) from {config.get("schema")}.alerts')
        assert count_alerts.first() == 0

    def test_rule_no_activity_in_24h_fired(self, db_conn, config, statements):
        current_ts = datetime.now().astimezone()
        ago_26h = current_ts - timedelta(hours=26)

        with db_conn.xact():
            statements['create_user'](1, 'john', 'smith', 'someprog')
            statements['add_event']('1', ago_26h, 'steps', '1')

        rule_engine = rules.RuleEngine(config)
        rule_engine.load_rules()
        rule_engine.execute_ruleset()

        alerts = statements.get('get_alerts_for_user').rows(1)
        assert len(list(alerts)) == 1

