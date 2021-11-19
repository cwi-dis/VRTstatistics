# Analysis scripts

Here there are some scripts to parse the VRTApplication statistics logfiles and do some minimal analysis.

## Installation

Install python in a virtual environment and install the needed packages (only needed for plot, right now):

```
python -m venv .venv
. .venv/bin/activate # On windows use Scripts in stead of bin
pip install -r requirements.txt
```

> These instructions don't work on an M1 mac (numpy can't be built). In stead, use miniforge and conda to install a working Python. Follow instructions on <https://www.hendrik-erz.de/post/setting-up-python-numpy-and-pytorch-natively-on-apple-m1> and then manually install the packages from `requirements.txt`.

## Getting the data

Get the statistics logfiles from the machines and give them a logical name:

```
cd .../data
mkdir todays-measurements
cd todays-measurements
.../scripts/getlogs.sh
```

This will get the logfiles, turn them into json and combine them. It will also show an initial plot, to give you some confidence you've gotten the correct data (plotting the pointcounts of the renderers over time).

The file `combined.json` contains all the combined data from the run.

## Analysing the data

Converting to CSV and filtering can be done with
`filter.py`. It has a predicate argument allowing you to select the records you want to save. Each field can be addressed by name, so `sessiontime > 1 and sessiontime < 5` selects on sessiontime. Also, `record` has all fields, so `"fps" in record` can be used to select all records with an `fps` field.

You can specify the fields to be in the output file (default: all), which is especially good for CSV output.

You can also specify that that output field name is taken from an input field. So something like `role=fps` will add a column per `role`, and fill in the value from `fps` in that column.

Example, for untiled session:

```
python $scriptdir/filter.py combined/sessionname.json sessionname-latency.csv '"PointBufferRenderer" in component' sessiontime role=pc_latency_ms
```

Will create a 3-column CSV file with latencies for sender (self view) and receiver.

You can then plot the data:

```
python $scriptdir/plot.py sessionname-latency.csv
```

The plotter has options to save to file, select the X axis, more. Use `--help` to see the options.