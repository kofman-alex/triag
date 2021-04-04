import postgresql
import logging
from argparse import ArgumentParser
import json
import sys
from datetime import datetime

class ProcessorError(BaseException):
    def __init__(self, message):
        self.message = message

def parse_args():
    parser = ArgumentParser(
        description="Process rules"
    )

    parser.add_argument(
        "--config",
        type=str,
        default='secrets/config.json',
        help='Configuration file (JSON)',
    )

    return parser.parse_args()

class RuleEngine():
    def __init__(self, connect_url):
        self._connect_url = connect_url
        self._connection = None
    
    def _connect(self):
        if not self._connection or self._connection.closed:
            logging.debug('Connecting...')
            self._connection = postgresql.open(self._connect_url)
            logging.debug('Connected.')
    
    def __del__(self):
        logging.debug('Closing open connections...')
        self._connection.close()
        logging.debug('Done.')

    def load_rules(self):
        logging.debug('Loading the rules...')

        try:
            self._connect()
            
            get_rules = self._connection.prepare('select * from rules')
            
            self._insert_alert = self._connection.prepare('insert into alerts (user_id, time, rule_id, msg) values($1::integer, $2::timestamp with time zone, $3::integer, $4)')

            self._ruleset = []
            
            with self._connection.xact():
                for rule in get_rules.rows():
                    logging.debug(f'Add rule {rule[0]}: {rule[2]}')
                    self._ruleset.append({
                        'rule_id': rule[0],
                        'rule_priority': rule[1],
                        'summary': rule[2],
                        'expr': self._connection.prepare(rule[3]),
                        'msg': rule[4]
                    })
                    logging.debug('ok')
            
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise ProcessorError(f'Cannot load rules: {e}')
        
    def execute_ruleset(self):
        for rule in self._ruleset:
            self.execute_rule(rule) 

    def execute_rule(self, rule):
        logging.debug(f'Evaluate rule {rule.get("rule_id")}:{rule.get("summary")}')
        with self._connection.xact() as x:
            x.start()
            timestamp = datetime.now().astimezone()

            for res in rule.get('expr').rows():
                logging.debug(f'Insert alert (user_id={res[0]}, time={timestamp.strftime("%Y-%m-%dT%H:%M:%S%z")}, rule_id={rule.get("rule_id")}, msg={rule.get("msg")}')

                self._insert_alert(res[0], timestamp, rule.get('rule_id'), rule.get('msg'))
            
            x.commit()
        logging.debug('done.')

def main():
    args = parse_args()

    config = None

    with open(args.config) as config_file:
        config = json.load(config_file)

    if not config:
        logging.error("Cannot load config. Abort.")
        sys.exit(1)
    
    rule_engine = RuleEngine(config.get('connectURL'))

    rule_engine.load_rules()

    rule_engine.execute_ruleset()

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()