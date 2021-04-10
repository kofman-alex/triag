import logging
from argparse import ArgumentParser
import json
import sys
from datetime import datetime
from string import Template
import db_client

class RuleEngineError(BaseException):
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
        if not config.get('duplicateInterval'):
            config['duplicateInterval'] = DEFAULT_DUP_INTERVAL

        self._dbclient = db_client.DBClient(config)
        
    def load_rules(self):
        logging.debug('Loading the rules...')

        try:
            self._ruleset = {}
            
            for rule in self._dbclient.get_rules(with_expr=True):
                logging.debug(f'Add rule {rule[0]}: {rule[2]}')

                self._ruleset[rule[0]] = {
                    'rule_id': rule[0],
                    'rule_priority': rule[1],
                    'summary': rule[2],
                    'expr': self._dbclient.compile_rule(rule[3]),
                    'msg': rule[4]
                }
                logging.debug('ok')
            
        except:
            e = sys.exc_info()[1]
            logging.error(f'Error: {e}')    
            raise RuleEngineError(f'Cannot load rules: {e}')
        
    def execute_ruleset(self):
        for rule_id in self._ruleset.keys():
            self.execute_rule(rule_id) 

    def execute_rule(self, rule_id):
        rule = self._ruleset.get(rule_id)
        
        if not rule:
            raise RuleEngineError(f'rule {rule_id} not found.')

        logging.debug(f'Evaluate rule {rule_id}')
        
        timestamp = datetime.now().astimezone()

        for res in self._dbclient.execute_rule(rule['expr']):
            logging.debug(f'Add alert (user_id={res[0]}, time={timestamp.strftime("%Y-%m-%dT%H:%M:%S%z")}, rule_id={rule.get("rule_id")}, msg={rule.get("msg")}')
            
            self._dbclient.add_alert(user_id=res[0], timestamp=timestamp, rule_id=rule['rule_id'], msg=rule.get('msg'))
            
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