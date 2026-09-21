"""Detached worker entry point; all output is captured in the owning job's log."""
import argparse
from jobs import Jobs

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', required=True)
    parser.add_argument('--job', required=True)
    args = parser.parse_args()
    Jobs(args.runtime).run(args.job)
