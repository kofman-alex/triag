from db_client import DBClient
import logging
import sys
from argparse import ArgumentParser
import json
from datetime import datetime, timedelta
import os

event_row_template = ' {:>10} | {:20s} | {:^25s} | {:20s} | {:50s} '
event_header_bottom_template = ' {:>10} + {:20s} + {:^25s} + {:20s} + {:50s} '

header_events = f'{event_row_template.format("event_id", "user_id", "time", "type", "description")}\n\
{event_header_bottom_template.format("-"*10,"-"*20,"-"*25,"-"*20,"-"*50)}'

alert_row_template = ' {:>10} | {:20d} | {:^25s} | {:20s} | {:60s} '
alert_header_bottom_template = ' {:>10} + {:20s} + {:^25s} + {:20s} + {:60s} '

header_alerts = f'{event_row_template.format("alert_id", "user_id", "time", "rule_id", "msg")}\n\
{alert_header_bottom_template.format("-"*10,"-"*20,"-"*25,"-"*20,"-"*60)}'

header_events = f'{event_row_template.format("event_id", "user_id", "time", "type", "description")}\n\
{event_header_bottom_template.format("-"*10,"-"*20,"-"*25,"-"*20,"-"*50)}'

rule_row_template = ' {:20} | {:>8s} | {:^60s} | {:60s} '
rule_header_bottom_template = ' {:20} + {:8s} + {:60s} + {:60s} '

header_rules = f'{rule_row_template.format("rule_id", "priority", "summary", "msg")}\n\
{rule_header_bottom_template.format("-"*20,"-"*8,"-"*60,"-"*60)}'

def event2str(event):
    return event_row_template.format(event[0], event[1], event[2].replace(microsecond=0).isoformat(), event[3], event[4])

def alert2str(alert):
    return alert_row_template.format(alert[0], alert[1], alert[2].replace(microsecond=0).isoformat(), alert[3], alert[4])

def rule2str(rule):
    return rule_row_template.format(rule[0], str(rule[1]), rule[2], rule[3])

def _add_event(dbclient:DBClient, args):
    if not (args.user_id and args.ts and args.type and args.description):
        logging.error('Invalid arguments')
        sys.exit(1)

    timestamp = datetime.fromisoformat(args.ts).astimezone()
    dbclient.insert_event(args.user_id, timestamp, args.type, args.description)
    logging.info('OK')

def _get_events(dbclient:DBClient, args):
    rows = dbclient.get_events_by_user(args.user_id) if args.user_id else dbclient.get_events_all()

    print(header_events)
    for event in rows:
        print(event2str(event))

def _get_alerts(dbclient:DBClient, args):
    rows = dbclient.get_alerts_by_user(args.user_id) if args.user_id else dbclient.get_alerts_all()

    print(header_alerts)
    for alert in rows:
        print(alert2str(alert))

def _get_rules(dbclient:DBClient, args):
    rows = dbclient.get_rules()

    print(header_rules)
    for rule in rows:
        print(rule2str(rule))

def _clear_events(dbclient:DBClient, args):
    dbclient.clear_events()

def _clear_alerts(dbclient:DBClient, args):
    dbclient.clear_alerts()

def _clear_all(dbclient:DBClient, args):
    dbclient.clear_all()

def _rule_exists(rule_id:str, rules):
    return len(list(filter(lambda rule: rule[0] == rule_id, rules))) > 0

def _add_rule(dbclient:DBClient, args):
    spec = None
    
    with open(args.rule_spec) as spec_file:
        spec = json.load(spec_file)

    expr = '\n'.join(spec.get('expr'))
    
    if _rule_exists(spec.get('id'), dbclient.get_rules()):
        print(f'Rule \'{spec.get("id")}\' already exists.')
        sys.exit(1)

    print(f'Adding rule \'{spec.get("id")}\'...')
    dbclient.insert_rule(spec.get('id'), spec.get('priority'), spec.get('summary'), expr, spec.get('msg'))
    print('Done.')

def _delete_rule(dbclient:DBClient, args):
    if not args.rule_id:
        print('rule_id argument is missing')
        sys.exit(1)

    print(f'Deleting rule \'{args.rule_id}\'...')
    dbclient.delete_rule(args.rule_id)
    print('Done.')



# 25 hours of inactivity
def _scenario_inactivity(dbclient:DBClient):
    timestamp = datetime.now().astimezone()
    dbclient.insert_event('1', timestamp - timedelta(hours=25), 'steps', '10000')

# missing medications 3 days in a row
def _scenario_missing_medication(dbclient:DBClient):
    timestamp = datetime.now().astimezone()
    dbclient.insert_event('1', timestamp - timedelta(days=3), 'medication', 'done')
    dbclient.insert_event('1', timestamp - timedelta(hours=2), 'water', '3 cups')

# PRO increasing 3 days in a row
def _scenario_pro_deterioration(dbclient:DBClient):
    timestamp = datetime.now().astimezone()
    dbclient.insert_event('1', timestamp - timedelta(days=2), 'PRO', '10 - Low')
    dbclient.insert_event('1', timestamp - timedelta(days=1), 'PRO', '15 - Mid')
    dbclient.insert_event('1', timestamp - timedelta(days=0), 'PRO', '20 - High')

# more than 5 events in one day
def _scenario_activity_endorsement(dbclient:DBClient):
    timestamp = datetime.now().astimezone()
    dbclient.insert_event('1', timestamp - timedelta(hours=10), 'steps', '10000')
    dbclient.insert_event('1', timestamp - timedelta(hours=8), 'mind', 'Quality of Sleep')
    dbclient.insert_event('1', timestamp - timedelta(hours=7), 'water', '2 cups')
    dbclient.insert_event('1', timestamp - timedelta(hours=6), 'mind', 'Energy level')
    dbclient.insert_event('1', timestamp - timedelta(hours=4), 'medication', 'Done')
    dbclient.insert_event('1', timestamp - timedelta(hours=2), 'PRO', '5 - Low')

scenarios = {
    'inactivity': _scenario_inactivity,
    'missing-medication': _scenario_missing_medication,
    'pro-deterioration': _scenario_pro_deterioration,
    'activity-endorsement': _scenario_activity_endorsement
}

def _create_scenario(db_client:DBClient, args):
    if not args.scenario in scenarios.keys():
        print(f'Unsupported scenario: {args.scenario}')
        sys.exit(1)
    
    scenarios[args.scenario](db_client)

commands = {
    'add-event': _add_event,
    'get-events': _get_events,
    'get-alerts': _get_alerts,
    'clear-events': _clear_events,
    'clear-alerts': _clear_alerts,
    'clear-all': _clear_all,
    'create-scenario': _create_scenario,
    'add-rule': _add_rule,
    'delete-rule': _delete_rule,
    'get-rules': _get_rules
}

def parse_args():
    parser = ArgumentParser(
        description="TRIAG Command Line Tool"
    )

    parser.add_argument(
        "--config",
        type=str,
        default='secrets/config.json',
        help='Configuration file (JSON)',
    )

    parser.add_argument(
        "--command",
        type=str,
        default='get-events',
        help='Command ["add-event | get-events | get-alerts | create-scenario | clear-events | clear-alerts | clear-all | add-rule"]',
    )

    parser.add_argument(
        "--user_id",
        type=str,
        default=None,
        help='User ID'
    )

    parser.add_argument(
        "--ts",
        type=str,
        default=None,
        help='Timestamp (yyyy-mm-ddThh:mm:ss)'
    )

    parser.add_argument(
        "--type",
        type=str,
        default=None,
        help='Event type'
    )

    parser.add_argument(
        "--description",
        type=str,
        default=None,
        help='Event description'
    )

    parser.add_argument(
        "--debug",
        action='store_true',
        help='Print debug information'
    )

    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help='Name of the scenario to create: inactivity | missing-medication | pro-deterioration | activity-endorsement'
    )

    parser.add_argument(
        "--rule_spec",
        type=str,
        default=None,
        help='Path to the rule spec (JSON)'
    )

    parser.add_argument(
        "--rule_id",
        type=str,
        default=None,
        help='Rule ID'
    )


    return parser.parse_args()

def main():
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    config = None
    with open(args.config) as config_file:
        config = json.load(config_file)
    
    db = DBClient(config)

    command = commands.get(args.command)

    if command:
        command(db, args)
    else:
        logging.error(f'command {args.command} is not supported')
        sys.exit(1)


if __name__ == '__main__':
    main()

