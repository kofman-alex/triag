import postgresql
import logging
import sys
from datetime import datetime

class DBError(BaseException):
    def __init__(self, message):
        self.message = message

class DBClient():
    def __init__(self, config):
        self._connect_params = config.get('connectParams')
        self._schema = config.get('schema')
        self._connection = None
    
    def _connect(self):
        if not self._connection or self._connection.closed:
            logging.debug('Connecting...')
            self._connection = postgresql.open(**self._connect_params)
            self._prepare()
            logging.debug('Connected.')
    
    def _prepare(self):
        self._insert_event = self._connection.prepare(f'insert into {self._schema}.events (user_id, time, type, description) values($1::integer, $2::timestamp with time zone, $3, $4)')
        self._get_alerts_all = self._connection.prepare(f'select * from {self._schema}.alerts order by time')
        self._get_alerts_by_user = self._connection.prepare(f'select * from {self._schema}.alerts where user_id=$1 order by time')
        self._get_events_all = self._connection.prepare(f'select * from {self._schema}.events order by time')
        self._get_events_by_user = self._connection.prepare(f'select * from {self._schema}.events where user_id=$1 order by time')
        self._clear_events = self._connection.prepare(f'truncate {self._schema}.events')
        self._clear_alerts = self._connection.prepare(f'truncate {self._schema}.alerts')
        self._insert_rule = self._connection.prepare(f'insert into {self._schema}.rules (rule_id, rule_priority, summary, expr, msg) values ($1, $2, $3, $4, $5)')
        self._get_rules = self._connection.prepare(f'select rule_id, rule_priority, summary, msg from {self._schema}.rules')

    def __del__(self):
        logging.debug('Closing open connections...')
        if self._connection:
            self._connection.close()
        logging.debug('Done.')
    
    def insert_event(self, user_id:int, ts: datetime, event_type:str, description:str):
        logging.debug(f'Insert event user_id={user_id}, time={ts}, type={event_type}, description={description}')
        try:
            self._connect()
            with self._connection.xact():
                self._insert_event(int(user_id), ts, event_type, description)
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise DBError(e)

    def get_events_all(self):
        logging.debug('Get all events')
        try:
            self._connect()
            with self._connection.xact():
                return self._get_events_all.rows()
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise DBError(e)

    def get_events_by_user(self, user_id):
        logging.debug('Get all events for user {user_id}')
        try:
            self._connect()
            with self._connection.xact():
                return self._get_events_by_user.rows(user_id)
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise DBError(e)

    def get_alerts_all(self):
        logging.debug('Get all alerts')
        try:
            self._connect()
            with self._connection.xact():
                return self._get_alerts_all.rows()
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise DBError(e)

    def get_alerts_by_user(self, user_id):
        logging.debug(f'Get all alerts for user {user_id}')
        try:
            self._connect()
            with self._connection.xact():
                return self._get_alerts_by_user.rows(int(user_id))
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise DBError(e)

    def clear_events(self):
        logging.debug('Clear events')
        try:
            self._connect()
            with self._connection.xact():
                self._clear_events()
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise DBError(e)
            
    def clear_alerts(self):
        logging.debug('Clear alerts')
        try:
            self._connect()
            with self._connection.xact():
                self._clear_alerts()
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise DBError(e)

    def clear_all(self):
        logging.debug('Clear all events and alerts')
        try:
            self._connect()
            with self._connection.xact():
                self._clear_events()
                self._clear_alerts()
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise DBError(e)

    def insert_rule(self, rule_id, priority:int, summary:str, expr:str, msg:str):
        logging.debug(f'Insert rule rule_id={rule_id}, priority={priority}, summary={summary}, expr={expr}, msg={msg}')
        try:
            self._connect()
            with self._connection.xact():
                self._insert_rule(rule_id, priority, summary, expr, msg)
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise DBError(e)
    
    def get_rules(self):
        logging.debug('Get rules')
        try:
            self._connect()
            with self._connection.xact():
                return self._get_rules.rows()
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise DBError(e)