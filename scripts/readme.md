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

### Two-machine runs

Edit `getlogs.sh` and fix the hostnames and log file paths.

Create a directory to store the data.

Get the statistics logfiles from the machines and give them a logical name:

```
cd .../data
mkdir todays-measurements
cd todays-measurements
.../scripts/getlogs.sh
```

This will get the logfiles, turn them into json and combine them. It will also show an initial plot, to give you some confidence you've gotten the correct data (plotting the pointcounts of the renderers over time).

The file `combined.json` contains all the combined data from the run.

### One-machine run

If you're only interested in statistics of a single machine, inspect the `getlogs.sh` script and simply execute the corresponding (python) commands.

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

## Performance testing guidelines

Writing this down here because I keep forgetting.

The `getlogs-jitter.sh` script shows some graphs after getting the data and processing it that help you judge whether the data makes sense.

1. First graph is points per cloud. Ensure that this has the shape you expect, given the prerecorded stream you think you've selected, or however the subject moved in front of the camera.
2. Second graph is latencies, end-to-end and from different components. Eyeball and apply common sense.
3. Framerates per component. You may have to zoom in because of outliers. Check these confirm to what you think you've selected. 
4. Dropped frames per second, per component. If they're not all zeroes you should be able to come up with a good reason why not. 
   
   **Note** if you get serious frame dropping somewhere on the sender side your sender hardware is not powerful enough. Lowering framerate or pointcount is the only option.
5. Timestamp progression in source capturer and destination receiver. Should be linear upsloping lines with sender ahead of receiver.
