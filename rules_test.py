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

    # verify empty alerts after setting up the test
    def test_alerts(self, db_conn, config):
        count_alerts = db_conn.prepare(f'select count(*) from {config.get("schema")}.alerts')
        assert count_alerts.first() == 0

    # no activity in 26 hours - should fire a rule about lack of activity in last 24 hours
    def test_rule_no_activity_in_24h_fired(self, db_conn, config, statements):
        current_ts = datetime.now().astimezone()
        ago_26h = current_ts - timedelta(hours=26)

        with db_conn.xact():
            statements['create_user'](1, 'john', 'smith', 'someprog')
            statements['add_event']('1', ago_26h, 'steps', '1')

        rule_engine = rules.RuleEngine(config)
        rule_engine.load_rules()
        rule_engine.execute_rule('inactivity')

        alerts = statements.get('get_alerts_for_user').rows(1)
        alerts_as_list = list(alerts)
        assert len(alerts_as_list) == 1
        # user_id == 1
        assert alerts_as_list[0][1] == 1 
        # rule_id == 'inactivity'
        assert alerts_as_list[0][3] == 'inactivity'
    
    # last activity 12 hours ago - rule about lack of activity in last 24 hours MUST NOT fire
    def test_rule_no_activity_in_24h_not_fired(self, db_conn, config, statements):
        current_ts = datetime.now().astimezone()
        ago_12h = current_ts - timedelta(hours=12)

        with db_conn.xact():
            statements['create_user'](1, 'john', 'smith', 'someprog')
            statements['add_event']('1', ago_12h, 'steps', '1')

        rule_engine = rules.RuleEngine(config)
        rule_engine.load_rules()
        rule_engine.execute_rule('inactivity')

        alerts = statements.get('get_alerts_for_user').rows(1)
        assert len(list(alerts)) == 0

    # last medication reported 4 days ago - "User did not report his medication 3 days in a row" must fire
    def test_rule_no_medication_in_3d_fired(self, db_conn, config, statements):
        current_ts = datetime.now().astimezone()
        ago_4d = current_ts - timedelta(days=4)

        with db_conn.xact():
            statements['create_user'](1, 'john', 'smith', 'someprog')
            statements['add_event']('1', ago_4d, 'medication', 'done')

        rule_engine = rules.RuleEngine(config)
        rule_engine.load_rules()
        rule_engine.execute_rule('missing-medication')

        alerts = statements.get('get_alerts_for_user').rows(1)
        alerts_as_list = list(alerts)
        assert len(alerts_as_list) == 1
        # user_id == 1
        assert alerts_as_list[0][1] == 1 
        # rule_id == 'missing-medication'
        assert alerts_as_list[0][3] == 'missing-medication'

    # last medication reported 1 day ago - "User did not report his medication 3 days in a row" must NOT fire
    def test_rule_no_medication_in_3d_not_fired(self, db_conn, config, statements):
        current_ts = datetime.now().astimezone()
        ago_1d = current_ts - timedelta(days=1)

        with db_conn.xact():
            statements['create_user'](1, 'john', 'smith', 'someprog')
            statements['add_event']('1', ago_1d, 'medication', 'done')

        rule_engine = rules.RuleEngine(config)
        rule_engine.load_rules()
        rule_engine.execute_rule('missing-medication')

        alerts = statements.get('get_alerts_for_user').rows(1)
        alerts_as_list = list(alerts)
        assert len(alerts_as_list) == 0

    # 6 events reported during the last 6 hours - "The user has more than 5 tasks done at the same day" must fire
    def test_rule_activity_endorsement_fired(self, db_conn, config, statements):
        current_ts = datetime.now().astimezone()

        with db_conn.xact():
            statements['create_user'](1, 'john', 'smith', 'someprog')
            for delta_hours in range(6,0,-1):
                statements['add_event']('1', current_ts - timedelta(hours=delta_hours), 'medication', 'done')

        rule_engine = rules.RuleEngine(config)
        rule_engine.load_rules()
        rule_engine.execute_rule('activity-endorsement')

        alerts = statements.get('get_alerts_for_user').rows(1)
        alerts_as_list = list(alerts)
        assert len(alerts_as_list) == 1
        # user_id == 1
        assert alerts_as_list[0][1] == 1 
        # rule_id == 'activity-endorsement'
        assert alerts_as_list[0][3] == 'activity-endorsement'

    # 3 events reported during the day - "The user has more than 5 tasks done at the same day" must NOT fire
    def test_rule_activity_endorsement_fired(self, db_conn, config, statements):
        current_ts = datetime.now().astimezone()

        with db_conn.xact():
            statements['create_user'](1, 'john', 'smith', 'someprog')
            for delta_hours in range(3,0,-1):
                statements['add_event']('1', current_ts - timedelta(hours=delta_hours), 'medication', 'done')

        rule_engine = rules.RuleEngine(config)
        rule_engine.load_rules()
        rule_engine.execute_rule('activity-endorsement')

        alerts = statements.get('get_alerts_for_user').rows(1)
        alerts_as_list = list(alerts)
        assert len(alerts_as_list) == 0

    # PRO deterioration - increasing PRO values over the last 3 days - the rule must fire
    def test_rule_pro_deterioration_fired(self, db_conn, config, statements):
        current_ts = datetime.now().astimezone()

        with db_conn.xact():
            statements['create_user'](1, 'john', 'smith', 'someprog')
            statements['add_event']('1', current_ts - timedelta(days=2), 'PRO', '5 - Low')
            statements['add_event']('1', current_ts - timedelta(days=1), 'PRO', '15 - Mid')
            statements['add_event']('1', current_ts - timedelta(days=0), 'PRO', '20 - Critical')

        rule_engine = rules.RuleEngine(config)
        rule_engine.load_rules()
        rule_engine.execute_rule('pro-deterioration')

        alerts = statements.get('get_alerts_for_user').rows(1)
        alerts_as_list = list(alerts)
        assert len(alerts_as_list) == 1
        assert alerts_as_list[0][1] == 1 
        # rule_id == 'activity-endorsement'
        assert alerts_as_list[0][3] == 'pro-deterioration'

    # PRO deterioration - increasing PRO values over the last 3 days - the rule must NOT fire
    def test_rule_pro_deterioration_not_fired(self, db_conn, config, statements):
        current_ts = datetime.now().astimezone()

        with db_conn.xact():
            statements['create_user'](1, 'john', 'smith', 'someprog')
            statements['add_event']('1', current_ts - timedelta(days=2), 'PRO', '15 - Mid')
            statements['add_event']('1', current_ts - timedelta(days=1), 'PRO', '15 - Mid')
            statements['add_event']('1', current_ts - timedelta(days=0), 'PRO', '10 - Low')

        rule_engine = rules.RuleEngine(config)
        rule_engine.load_rules()
        rule_engine.execute_rule('pro-deterioration')

        alerts = statements.get('get_alerts_for_user').rows(1)
        alerts_as_list = list(alerts)
        assert len(alerts_as_list) == 0
