# VRTApplication stats: script analysis

This is a set of modules and scripts to collect and analyse the `stats:` output files produced by `VRTApplication`.

> Note: need to check these instructions work on windows.

> Note: need to add the "python -m build" invocation.

## Installation

Install python in a virtual environment and install the needed packages. For Mac or Linux:

```
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

For Windows `CMD`:

```
python -m venv .venv
".venv\Scripts\activate.bat" 
pip install -e .
```

For Windows PowerShell:

```
python -m venv .venv
& .venv\Scripts\Activate.ps1
pip install -e .
```


> Note: you should not try to use `bash` on Windows, this will not work because the `activate` script doesn't know how to modify `PATH` correctly.

After having done this once, you can use the scripts and utilities from any directory, by calling

```
. .../VRTstatistics/.venv/Scripts/activate
```

## Getting started

Check the `example` directory and the [example/README.md](example/README.md) file to get started.

## Debugging VRTstatistics

Many things can go wrong, especially because of the origin of this package (initially meant for one project, for one task).
For now, here is a way to see why things are going wrong:

- Run the venv initialization sequnce, above.
- Open `vscode` in this directory. Ensure you have all the right plugins for Python installed.
- Open a terminal in vscode. It should automatically find the `.venv` and load it.
- Now add the toplevel directory with your measurements with _File_ -> _Add Folder To Workspace..._
- You can now navigate all files and edit them.
- Run whatever tool is giving you problems with (for example) `VRTstatistics-plot --pausefordebug ...`.
- In vscode, goto debugger, select "Python: Attach using Process ID", select the process.
- You can now set breakpoints, whatever. When you type a _return_ in the terminal window the tool will start running under the debugger.

## Gathering data

> Note this section is incorrect at the moment (at least mostly incorrect). See the example.

### Creating your configuration

Edit `src/VRTstatistics/runnerconfig.py` and ensure the settings for the machines you want to use are correct. Generally, we use `foo.local` for manual runs and ssh access, and `foo` for runserver access.

Create a directory (or maybe a directory tree) to gather your data.

> Suggestion: for automatic testing, for example latency/bandwidth tests with different settings, use subdirectories with logical names. You can store per-experiment config files in those subdirectories and transfer them to the machines under test with the `--config` option.
> 
> For experiments with multiple participants use subdirectories with names like `YYYYMMDD-HHMM` so it is easier to match data with participants/runs.

#### Manual running

Run manually on the two machines.

After that, ingest the data with

```
VRTstatistics-ingest --nolog --norusage --annotator latency flauwte.local vrtiny.local
```

Then, do a spot-check of your data, for example plotting the latency. Check that the total session is as long as you expect, and the numbers seem somewhat reasonable.

> Command to be provided


#### runserver running

On both machines, run (in a `CMD` prompt on the machine, not in an ssh remote connection because then you won't have access to start the binary)

```
VRTStatistics-runserver
```
 
Now you can automatically start everything from your master/control machine with
 
```
VRTstatistics-ingest --run --config config.json --annotator latency flauwte vrtiny
```
 
## Processing the data

Processing the data with the scripts is likely to be disappointing (because everyone is interested in different graphs, tables, etc).

It is probably easiest to start playing with the data in `jupyter`.

> Example should be provided.

Once you think you know what data you need, and how you want to visualize it turn it into a Python script.

> Example to be provided.

Another option is the export only the data you want as a CSV file, for easy processing with other tools. For this there is a tool `VRTstatistics-filter`. With the `--predicate` option you pass a boolean function that selects the records you want in your output file. With the positional argument you say which fields you want.

> Examples to be provided.
> 
> Need examples for the predicate functions.
> 
> Also need examples of field constructs like `role=latency_ms` which selects one field as the field name and another as the data.

## Annotators

**Note**: you should probably look at the annotators (`VRTStatistics/annotator.py`). These create new fields in your database, by combining data from multiple fields and possibly multiple records.

For example, the latency annotator will lookup the `component` field (which may be something like `PointCloudRenderer#7`) and create a `component_role` field like `receiver.pointcloud.renderer.tile.2` which tells you what this record is about in the context of your measurements.

## Getting the data

> **Note**: This section is outdated.

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

> **Note**: This section is outdated.

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
