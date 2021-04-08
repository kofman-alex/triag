from db_client import DBClient
import logging
import sys
from argparse import ArgumentParser
import json
from datetime import datetime
import os

event_row_template = ' {:>10} | {:20s} | {:^25s} | {:20s} | {:50s} '
event_header_bottom_template = ' {:>10} + {:20s} + {:^25s} + {:20s} + {:50s} '

header_events = f'{event_row_template.format("event_id", "user_id", "time", "type", "description")}\n\
{event_header_bottom_template.format("-"*10,"-"*20,"-"*25,"-"*20,"-"*50)}'

alert_row_template = ' {:>10} | {:20d} | {:^25s} | {:20s} | {:60s} '
alert_header_bottom_template = ' {:>10} + {:20s} + {:^25s} + {:20s} + {:60s} '
header_alerts = f'{event_row_template.format("alert_id", "user_id", "time", "rule_id", "msg")}\n\
{alert_header_bottom_template.format("-"*10,"-"*20,"-"*25,"-"*20,"-"*60)}'

def event2str(event):
    return event_row_template.format(event[0], event[1], event[2].isoformat(), event[3], event[4])

def alert2str(alert):
    return alert_row_template.format(alert[0], alert[1], alert[2].replace(microsecond=0).isoformat(), alert[3], alert[4])

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

def _clear_events(dbclient:DBClient, args):
    dbclient.clear_events()

def _clear_alerts(dbclient:DBClient, args):
    dbclient.clear_alerts()

def _clear_all(dbclient:DBClient, args):
    dbclient.clear_all()

commands = {
    'add-event': _add_event,
    'get-events': _get_events,
    'get-alerts': _get_alerts,
    'clear-events': _clear_events,
    'clear-alerts': _clear_alerts,
    'clear-all': _clear_all
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
        help='Command ["add-event | get-events | get-alerts | clear-events | clear-alerts | clear-all"]',
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

