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
        return storage.delete_analysis(args['root'])
    if operation == 'analyze':
        from pipeline import run
        run(args['root'], runtime, args['options'])
        return {'finished': True}
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
