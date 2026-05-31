import sys
import argparse
from importlib.metadata import version as _pkg_version

from ..parser import StatsFileParser


def main():
    parser = argparse.ArgumentParser(description="Convert a VR2Gather stats log to JSON")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_pkg_version('VRTstatistics')}")
    parser.add_argument("logfile", help="Input stats log file")
    parser.add_argument("statsfile", help="Output JSON file or directory")
    args = parser.parse_args()
    stats_parser = StatsFileParser(args.logfile)
    stats_parser.parse()
    ok = stats_parser.check()
    stats_parser.save_json(args.statsfile)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
