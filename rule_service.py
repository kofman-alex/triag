from flask import Flask
import rules
import logging
import os

app = Flask(__name__)

logger = logging.getLogger()

@app.before_first_request
def init_rule_engine():
    global rule_engine

    config = {
        'connect_url': os.environ.get('CONNECT_URL'),
        'schema': os.environ.get('SCHEMA')
    }

    if not config['schema']:
        config['schema'] = 'public'

    rule_engine = rules.RuleEngine(config)

    rule_engine.load_rules()

@app.route('/execute_ruleset', methods=['GET'])
def execute_ruleset():
    rule_engine.execute_ruleset()
    return {'status': 'OK'}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)