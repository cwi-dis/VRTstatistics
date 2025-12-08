# VRTstatistics - running VR2Gather apps remotely

_VRTStatistics_ helps with automatically running multiple VR2Gather-based application instances, optionally collecting the results and producing graphs or tables of things like bandwidth usage, frames per second, interaction patterns and much more.

It is intended to do repeatable experiments, for example for scientific papers, or for regression testing.

VRTstatistics contains two packages that it uses, _VRTrunserver_ and _VRTrun_. These two are also useful outside of VRTStatistics. _VRTRunserver_ is incorporated into VR2Gather-based applications (after v1.2.1) built for Windows or Mac, and it can start the VR2Gather-based app under remote control. _VRTrun_ provides that remote control.

Together, these allow a setup where a complete multi-user experience can be controlled from a single controlling computer. This can be useful for things like demonstrations or exhibitions.

Note that it is possible for the controlling computer to be the same as one of the end-user computers, VRTrun and VRTrunserver are completely independent.

This document presumes the end-user computers are running Windows (the controlling computers can run any of Mac, Linux or Windows). It is possible to use Linux or Mac end-user computers, but this is somewhat convoluted. Instructions will be forthcoming.

## Preparing the VR2Gather experience to run

- Build the Player for the experience you want to run, in the Unity Editor
- Zip, copy to all end-user machines, unzip
- On every end-user machine (Windows):
	- Ensure a compatible version of Python is installed
	- Run `VRTrunserver.ps1` with Powershell. This should install the VRTrunserver in a local (venv-based) Python. The _VRTrunserver_ is then started.
	- The installation should happen only the first time. So after that running the powershell script will start VRTrunserver directly.
	- This means that you can setup a Windows machine to auto-login after boot, and you can set `VRTrunserver.ps1` as a `Startup` program. This will prepare the machine for remote control automatically after booting.
- On every end-user machine (Mac, for development only):
	- Install the built VR2Gather as `VRTApp-Develop-built.app`.
	- Run with `./VRTApp-Develop-built.app/Contents/MacOS/VRTrunservermac.sh`
	- Note: you may have to add some symlinks here and there (specifically in the `.app` folder) to make the content work.

## Preparing the controlling computer

- Create a directory where you are going to run your experiments from, and where you will store the results.

  > If you care about repeatability it may be a good idea to store the ZIP file with the built VR2Gather experience here too.
  >
  > Also, you may want to think about storing this directory under `git`, but that may be a problem with the large ZIP file (which may be too large even for `git lfs`).
- Create a Python venv, and install _VRTrun_. Installing _VRTStatistics_ itself is optional.
	- Windows:
	
		```
		python -m venv .venv
		".venv\Scripts\activate.bat"
		pip install git+https://github.com/cwi-dis/VRTStatistics#subdirectory=VRTrun
		pip install git+https://github.com/cwi-dis/VRTStatistics#subdirectory=VRTstatistics
		```
	- Mac, Linux:
	
		```
		python3 -m venv .venv
		source .venv/bin/activate
		pip install git+https://github.com/cwi-dis/VRTStatistics#subdirectory=VRTrun
		pip install git+https://github.com/cwi-dis/VRTStatistics#subdirectory=VRTstatistics
		```
- Create a configuration directory `config` to store the configuration files for this experiment.
	- An example can be found in `examples/simple/config`
	- The configuration directory needs to contain at least a `runconfig.json` which lists the hostnames (or IP addresses) of the end-user machines and the role they take in this experiment.
	- More documentation is forthcoming.

## Running an experiment

- Ensure the correct _VRTrunserver_ is running on all end-user computers.
- On the controlling computer, in the experiment directory:
	- Activate the venv with `python -m venv .venv`
	- Run `VRTrun`
- The end-user computers should start their VR2Gather applications.
- After the VR2Gather applications have all terminated the results will be collected.
	- They will be in an output directory that has a timestamped name, such as `run-20250319-1230`.
	- Within that directory, there are per-role subdirectories.
	- Within each of those, all the log files from the run are stored. The configuration files that were used are stored there too.
	- This all taken together means that the output directory contains all the information needed to repeat a run, if needed in the future.

## Analyzing the results

To be provided.
	
## Development

If you want to modify anything here it is best to check out or fork the repository.

### Installing for development

Install python in a virtual environment and install the needed packages in an editable way. For Mac or Linux:

```
python -m venv .venv
source .venv/bin/activate
pip install -e VRTrun
pip install -e VRTrunserver
pip install -e VRTstatistics
```

For Windows `CMD`:

```
python -m venv .venv
".venv\Scripts\activate.bat" 
pip install -e VRTrun
pip install -e VRTrunserver
pip install -e VRTstatistics
```

For Windows PowerShell:

```
python -m venv .venv
& .venv\Scripts\Activate.ps1
pip install -e VRTrun
pip install -e VRTrunserver
pip install -e VRTstatistics
```

> Note: you should not try to use `bash` on Windows, this will not work because the `activate` script doesn't know how to modify `PATH` correctly.

After you have created the `.venv` you can select it in `vscode` with the `Python: Select Interpreter` command. Then all type checking and such will work.

Also, you can use the scripts and utilities from any directory, by calling

```
. .../VRTstatistics/.venv/Scripts/activate
```

Finally, most tools take a `--debugpy` argument. If you pass this argument the tool will wait after startup, and you can use the `vscode` Python Debugger `attach` command to attach a debugger. The tool will continue running once you have attached the debugger.

There is also a `--pausefordebug` argument that also waits after startup, but it doesn't wait for the python debugger. So you can attach any debugger by PID.

## Old readme.

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
