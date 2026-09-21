"""Public one-request CLI; stdout contains exactly one versioned JSON response."""
import argparse
import contextlib
import json
import os
import sys
from pathlib import Path
from control import Control
from control_errors import ControlError


def main():
    parser = argparse.ArgumentParser(description='Music Sweeper headless API')
    parser.add_argument('--runtime', default=os.environ.get('MUSIC_SWEEPER_RUNTIME', str(Path(__file__).resolve().parents[1] / '.runtime')))
    parser.add_argument('--projects')
    parser.add_argument('--registry')
    parser.add_argument('--allow-root', action='append', default=[])
    parser.add_argument('operation', nargs='?', help='Omit to read {operation,args} from stdin')
    parser.add_argument('--args', default='{}', help='JSON object; stdin is recommended for shell-sensitive text')
    args = parser.parse_args()
    try:
        request = {'operation': args.operation, 'args': json.loads(args.args)} if args.operation else json.load(sys.stdin)
        with contextlib.redirect_stdout(sys.stderr):
            service = Control(args.runtime, args.projects, args.registry, args.allow_root)
            value = service.dispatch(request['operation'], request.get('args', {}))
        response, exit_code = {'schemaVersion': 1, 'ok': True, 'value': value}, 0
    except Exception as error:
        code = error.code if isinstance(error, ControlError) else 'NOT_FOUND' if isinstance(error, FileNotFoundError) else 'INVALID_ARGUMENT' if isinstance(error, (ValueError, KeyError, TypeError)) else 'INTERNAL_ERROR'
        response, exit_code = {'schemaVersion': 1, 'ok': False, 'error': {'code': code, 'message': str(error)}}, 1
    print(json.dumps(response, ensure_ascii=False, allow_nan=False))
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
