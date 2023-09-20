# VRTApplication stats: script analysis

This is a set of modules and scripts to collect and analyse the `stats:` output files produced by `VRTApplication`.

> Note: need to check these instructions work on windows.

> Note: need to add the "python -m build" invocation.

## Installation

Install python in a virtual environment and install the needed packages (only needed for plot, right now):

```
python -m venv .venv
. .venv/bin/activate # On windows use Scripts in stead of bin
pip install -e .
```

After having done this once, you can use the scripts and utilities from any directory, by calling

```
. .../VRTstatistics/.venv/bin/activate
```

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
`VRTstatistics.scripts.filter`. It has a predicate argument allowing you to select the records you want to save. Each field can be addressed by name, so `sessiontime > 1 and sessiontime < 5` selects on sessiontime. Also, `record` has all fields, so `"fps" in record` can be used to select all records with an `fps` field.

You can specify the fields to be in the output file (default: all), which is especially good for CSV output.

You can also specify that that output field name is taken from an input field. So something like `role=fps` will add a column per `role`, and fill in the value from `fps` in that column.

Example, for untiled session:

```
python -m VRTstatistics.scripts.filter combined/sessionname.json sessionname-latency.csv -p '"PointBufferRenderer" in component' sessiontime role=pc_latency_ms
```

Will create a 3-column CSV file with latencies for sender (self view) and receiver.

You can then plot the data:

```
python -m VRTstatistics.scripts.plot sessionname-latency.csv
```

The plotter has options to save to file, select the X axis, more. Use `--help` to see the options.

### Filtering observer camera

Sometimes it may be necessary to filter out the log entries of an observer. To
do this, the script `remove_observer_camera.py` can be used. It expects a JSON
log file as input and can be invoked as follows:

```
python -m VRTstatistics.scripts.remove_observer_camera input_log.json filtered.json
```

Where `input_log.json` is the file to be filtered and `filtered.json` is the
output file where all records for the observer camera have been removed. If no
output file name is given, the result is printed to the standard output.

The observer camera is assumed to be the camera which has moved the least
during the course of the session. So for files that do not contain an observer
or if the observer has moved more than participants, the script will not return
accurate data. Please double check the results.

## Performance testing guidelines

Writing this down here because I keep forgetting.

The `getlogs-jitter.sh` script shows some graphs after getting the data and processing it that help you judge whether the data makes sense.

1. First graph is points per cloud. Ensure that this has the shape you expect, given the prerecorded stream you think you've selected, or however the subject moved in front of the camera.
2. Second graph is latencies, end-to-end and from different components. Eyeball and apply common sense.
3. Framerates per component. You may have to zoom in because of outliers. Check these confirm to what you think you've selected. 
4. Dropped frames per second, per component. If they're not all zeroes you should be able to come up with a good reason why not. 
   
   **Note** if you get serious frame dropping somewhere on the sender side your sender hardware is not powerful enough. Lowering framerate or pointcount is the only option.
5. Timestamp progression in source capturer and destination receiver. Should be linear upsloping lines with sender ahead of receiver.
