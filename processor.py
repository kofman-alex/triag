import postgresql
import logging
from argparse import ArgumentParser
import json
import sys
from datetime import datetime

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

def main():
    args = parse_args()

    config = None

    with open(args.config) as config_file:
        config = json.load(config_file)

    if not config:
        logging.error("Cannot load config. Abort.")
        sys.exit(1)
    
    logging.debug('Connecting to the database...')

    with postgresql.open(config.get('connectURL')) as db:
        logging.debug('Connected.')
        
        logging.debug('Loading the rules...')

        get_rules = db.prepare('SELECT * from rules')

        insert_alert = db.prepare('insert into alerts (user_id, time, rule_id, msg) values($1::integer, $2::timestamp with time zone, $3::integer, $4)')
        
        rules = []

        with db.xact() as x:
            for rule in get_rules.rows():
                logging.debug(f'Add rule {rule[0]}: {rule[2]}')
                rules.append({
                    'rule_id': rule[0],
                    'rule_priority': rule[1],
                    'summary': rule[2],
                    'expr': db.prepare(rule[3]),
                    'msg': rule[4]
                })
                logging.debug('ok')

            timestamp = datetime.now().astimezone() #.strftime('%Y-%m-%dT%H:%M:%S%z')

            x.start()

            for rule in rules:
                logging.debug(f'Evaluate rule {rule.get("rule_id")}:{rule.get("summary")}')
                for res in rule.get('expr').rows():
                    logging.debug(f'Insert alert (user_id={res[0]}, time={timestamp.strftime("%Y-%m-%dT%H:%M:%S%z")}, rule_id={rule.get("rule_id")}, msg={rule.get("msg")}')

                    insert_alert(res[0], timestamp, rule.get('rule_id'), rule.get('msg'))

            x.commit()

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()