import postgresql
import logging
from argparse import ArgumentParser
import json
import sys
from datetime import datetime
from string import Template

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

# time interval during which two alerts of the same type and for the same user are considered duplicates
DEFAULT_DUP_INTERVAL = '12 hours'

class RuleEngine():
    def __init__(self, config):
        self._connect_params = config.get('connectParams')
        self._schema = config.get('schema')
        self._duplicate_interval = config.get('duplicateInterval')
        if not self._duplicate_interval:
            self._duplicate_interval = DEFAULT_DUP_INTERVAL
        self._connection = None
    
    def _connect(self):
        if not self._connection or self._connection.closed:
            logging.debug('Connecting...')
            self._connection = postgresql.open(**self._connect_params)
            logging.debug('Connected.')
    
    def __del__(self):
        logging.debug('Closing open connections...')
        self._connection.close()
        logging.debug('Done.')

    def load_rules(self):
        logging.debug('Loading the rules...')

        try:
            self._connect()
            
            get_rules = self._connection.prepare(f'select * from {self._schema}.rules')
            
            self._insert_alert = self._connection.prepare(f"""insert into {self._schema}.alerts (user_id, time, rule_id, msg)
                select $1, $2, $3, $4
                where not exists (
                    select 1 from {self._schema}.alerts where user_id=$1 and $2 - time < interval '{self._duplicate_interval}')""")

            self._ruleset = {}
            
            with self._connection.xact():
                for rule in get_rules.rows():
                    logging.debug(f'Add rule {rule[0]}: {rule[2]}')

                    rule_expr = Template(rule[3]).substitute({'schema': self._schema})

                    self._ruleset[rule[0]] = {
                        'rule_id': rule[0],
                        'rule_priority': rule[1],
                        'summary': rule[2],
                        'expr': self._connection.prepare(rule_expr),
                        'msg': rule[4]
                    }
                    logging.debug('ok')
            
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise ProcessorError(f'Cannot load rules: {e}')
        
    def execute_ruleset(self):
        for rule_id in self._ruleset.keys():
            self.execute_rule(rule_id) 

    def execute_rule(self, rule_id):
        rule = self._ruleset.get(rule_id)
        
        if not rule:
            raise Exception(f'rule {rule_id} not found.')

        logging.debug(f'Evaluate rule {rule_id}')
        
        with self._connection.xact():
            timestamp = datetime.now().astimezone()

            for res in rule.get('expr').rows():
                logging.debug(f'Insert alert (user_id={res[0]}, time={timestamp.strftime("%Y-%m-%dT%H:%M:%S%z")}, rule_id={rule.get("rule_id")}, msg={rule.get("msg")}')

                self._insert_alert(int(res[0]), timestamp, rule.get('rule_id'), rule.get('msg'))
            
        logging.debug('done.')

def main():
    args = parse_args()

    with open(args.config) as config_file:
        config = json.load(config_file)
    
    rule_engine = RuleEngine(config)

    rule_engine.load_rules()

    rule_engine.execute_ruleset()

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()