"""JSON stdin/stdout bridge. Heavy imports are confined to analysis operations."""
import argparse
import json
import sys
from pathlib import Path
import traceback
import storage


def execute(request, runtime):
    operation = request['operation']
    args = request.get('args', {})
    if operation == 'create':
        return storage.create(args['source'], args['parent'])
    if operation == 'snapshot':
        return storage.snapshot(args['root'])
    if operation == 'save':
        return storage.save_edits(args['root'], args['edits'])
    if operation == 'export':
        return storage.export(args['root'])
    if operation == 'delete_analysis':
        from jobs import Jobs
        from control_errors import BusyError
        if Jobs(runtime).latest()['running']:
            raise BusyError()
        return storage.delete_analysis(args['root'])
    if operation == 'analyze':
        from pipeline import run
        run(args['root'], runtime, args['options'])
        return {'finished': True}
    if operation in ('start_job', 'latest_job', 'cancel_job'):
        from jobs import Jobs
        jobs = Jobs(runtime)
        if operation == 'start_job':
            return jobs.start(args['root'], args['options'])
        if operation == 'cancel_job':
            return jobs.cancel(args['jobId'])
        return jobs.latest(include_log=True)
    if operation in ('next_ui_request', 'ack_ui_request'):
        from ui_requests import UiRequests
        requests = UiRequests(runtime)
        if operation == 'next_ui_request':
            return requests.next()
        return requests.acknowledge(args['requestId'], args['state'], args.get('message'))
    raise ValueError('Unknown operation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', required=True, type=Path)
    args = parser.parse_args()
    try:
        response = execute(json.load(sys.stdin), args.runtime)
        print(json.dumps({'ok': True, 'value': response}, ensure_ascii=False, allow_nan=False))
    except Exception as error:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False))
        sys.exit(1)
