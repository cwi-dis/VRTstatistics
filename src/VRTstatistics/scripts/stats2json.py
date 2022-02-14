import sys

from ..parser import StatsFileParser

def main():
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} logfile statsfile-or-dir')
        sys.exit(1)
    logfile = sys.argv[1]
    statsfile = sys.argv[2]
    parser = StatsFileParser(logfile)
    parser.parse()
    ok = parser.check()
    parser.save_json(statsfile)
    sys.exit(0 if ok else 1)
            
if __name__ == '__main__':
    main()
