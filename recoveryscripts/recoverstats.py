import sys
import os

VERBOSE=False

def main():
    if len(sys.argv) != 3:
        print(f'Usage {sys.argv[0]} inputdir outputdir')
        sys.exit(1)
    for root, dirs, files in os.walk(sys.argv[1]):
        for file in files:
            path = os.path.join(root, file)
            process(path, sys.argv[2])

def process(inputfile, outputdir):
    if VERBOSE: print(f'process {inputfile}')
    outputfile = None
    ofp = None
    goodlinecount = 0
    badlinecount = 0
    for line in open(inputfile, encoding='latin-1'):
        if not line.startswith('stats: '):
            badlinecount += 1
            continue
        strippedline = line.strip()
        if len(strippedline) == len(line):
            if VERBOSE: print(f'{inputfile}: Missing end-of-line: {line}')
            badlinecount += 1
            continue
        entry = extractstats_single_new(strippedline[7:])
        toolongfield = False
        for k, v in entry.items():
            if k == 'statsFilename':
                continue
            if type(v) != type(''):
                continue
            if len(k) > 40 or len(v) > 40:
                toolongfield = True
                break
        if toolongfield:
            if VERBOSE: print(f'{inputfile}: line presumed bad: {line}')
            badlinecount += 1
            continue
        goodlinecount += 1
        # Write line
        if not ofp:
            # Create output file
            ts = int(entry['ts'])
            seq = entry.get('seq', 0)
            ofn = f'recovered-{ts:06d}-{seq:05d}.txt'
            outputfile = os.path.join(outputdir, ofn)
            while os.path.exists(outputfile):
                outputfile = outputfile + '.1'
            ofp = open(outputfile, 'w')
        if not line[-1] == '\n':
            line = line + '\n'
        ofp.write(line)
            
    if not goodlinecount:
        print(f'{inputfile}: no good lines')
        return
    ofp.close()
    fraction = goodlinecount / (goodlinecount + badlinecount)
    print(f'{inputfile}: {fraction*100:.0f}% recovered, {goodlinecount} lines of {goodlinecount+badlinecount}, written to {outputfile}')
    
def extractstats_single_new(line):
    """Extract new-style statistics from a single line"""
    entry = {}
    fields = line.split(',')
    for field in fields:
        field = field.strip()
        splitfield = field.split('=')
        k = splitfield[0]
        v = '='.join(splitfield[1:])
        # Try to convert v to natural value
        try:
            vi = int(v)
            v = vi
        except ValueError:
            try:
                vf = float(v)
                v = vf
            except ValueError:
                pass
        entry[k] = v
    return entry

if __name__ == '__main__':
    main()
