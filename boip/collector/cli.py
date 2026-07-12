"""Collector entry point.  Usage:  python -m boip.collector.cli vmware"""
import json
import sys

from . import vmware


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("vmware",):
        print(json.dumps({"error": "usage: python -m boip.collector.cli vmware"}))
        sys.exit(2)
    print(json.dumps(vmware.run()))


if __name__ == "__main__":
    main()
