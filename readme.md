# VRTstatistics - running VR2Gather apps remotely

_VRTStatistics_ helps with automatically running multiple VR2Gather-based application instances, optionally collecting the results and producing graphs or tables of things like bandwidth usage, frames per second, interaction patterns and much more.

It is intended to do repeatable experiments, for example for scientific papers, or for regression testing.

VRTstatistics contains two packages that it uses, _VRTrunserver_ and _VRTrun_. These two are also useful outside of VRTStatistics. _VRTRunserver_ is incorporated into VR2Gather-based applications (after v1.2.1) built for Windows or Mac, and it can start the VR2Gather-based app under remote control. _VRTrun_ provides that remote control.

Together, these allow a setup where a complete multi-user experience can be controlled from a single controlling computer. This can be useful for things like demonstrations or exhibitions.

Note that it is possible for the controlling computer to be the same as one of the end-user computers, VRTrun and VRTrunserver are completely independent.

This document presumes the end-user computers are running Windows (the controlling computers can run any of Mac, Linux or Windows). It is possible to use Linux or Mac end-user computers, but this is somewhat convoluted. Instructions will be forthcoming.

## Use cases

**System-oriented experiments** (primary use): Automated runs with no participants, varying parameters such as transport protocol, framerate, encoder quality, and tiling. Goal: measure latency, bandwidth, and resource usage for system-focused scientific papers. Multiple runs per configuration provide statistical robustness.

**User-centric experiments**: Sessions with two real participants interacting. Goal: measure human behaviour — turn-taking in speech, gaze direction, movement patterns — for user-focused scientific papers. Fewer parameter variations; key metadata is a participant identifier for matching to questionnaires or interviews.

**Demo/exhibition control**: VRTrun used to start and stop VR2Gather on multiple machines from a single laptop, avoiding running between rooms. Logs are timestamped for post-hoc debugging. No upfront analysis intended.

## System-oriented experiment structure

Each experiment lives in its own directory (often its own git repo). The structure for a system experiment with multiple parameter variants:

```
my-experiment/
  _config/                    # base config template, shared across variants
    config.json
    config-user.json
    runconfig.json
    sender/config-user.json   # per-role overrides if needed
    receiver/config-user.json
  tiled_octree9_fps15/        # one directory per parameter combination
    config/                   # hand-edited copy of _config for this variant
    _run-20260528-1340/       # discarded or test run (underscore prefix)
    run-20260528-1410/        # actual run — multiple runs per variant
    run-20260528-1430/        # for statistical robustness
    run-20260528-1450/
  untiled_octree7_fps15/
    config/
    run-20260528-1510/
    ...
```

**Variant naming:** encode the key parameters in the directory name (e.g. `tiled_octree9_fps15_socketio`). Names should read as a description of what distinguishes this variant.

**Hand-code each variant config.** Do not generate them programmatically. The effort of hand-coding forces you to justify each variant before running it, which keeps the experiment scope manageable and the eventual paper story clear.

Running each variant multiple times (from the experiment directory):

```bash
VRTstatistics-ingest -a latency --config tiled_octree9_fps15/config
VRTstatistics-ingest -a latency --config tiled_octree9_fps15/config
VRTstatistics-ingest -a latency --config tiled_octree9_fps15/config
```

Each run lands in `tiled_octree9_fps15/run-YYYYMMDD-HHMM/combined.json`. Prefix a run directory with `_` to mark it as a test or excluded run.

**Using prerecorded data for parameter sweeps:** Running real participants for every parameter variant is impractical. The recommended pattern is:

1. Run one session with two real participants using live RGBD capture. Record their movement, gaze, and the raw RGBD camera streams (large files, stored outside the repo).
2. Validate that a prerecorded playback session gives comparable latency and performance numbers to the live session.
3. Run all parameter variants using prerecorded playback (`variant_str: prerecorded` in the VR2Gather config, pointing at the recorded data). Sessions run unattended overnight; human variability is eliminated and input is identical across all variants.

This is what the `prerecorded` variant in the VR2Gather `RepresentationPointcloudConfig` is for. The `synthetic` variant used in the `examples/` configs is a self-contained substitute that works without data files, but is not suitable for publication-quality measurements.

**Plotting:** For now, write a small `create_plots.py` driver script in your experiment directory that calls `VRTstatistics.plots` functions (`plot_latencies`, `plot_framerates_and_dropped`, `plot_resources`, etc.) on each `combined.json` and saves the output alongside it. See `2024-spirit-lldash/experiments/scripts/create_plots.py` for a working example. A proper `VRTstatistics-plot` command that handles the standard cases is planned (see [issue #21](https://github.com/cwi-dis/VRTstatistics/issues/21)).

## Preparing the VR2Gather experience to run

- Build the Player for the experience you want to run, in the Unity Editor
- Zip, copy to all end-user machines, unzip
- On every end-user machine (Windows):
	- Ensure a compatible version of Python is installed
	- **Windows SmartScreen:** the app is not code-signed, so Windows will show a "Windows protected your PC" dialog on first launch. Click **More info**, then **Run anyway**.
	- Run `VRTrunserver.ps1` with Powershell. This should install the VRTrunserver in a local (venv-based) Python. The _VRTrunserver_ is then started.
	- The installation should happen only the first time. So after that running the powershell script will start VRTrunserver directly.
	- This means that you can setup a Windows machine to auto-login after boot, and you can set `VRTrunserver.ps1` as a `Startup` program. This will prepare the machine for remote control automatically after booting.
- On every end-user machine (Mac, for development only):
	- Install the built VR2Gather as `VRTApp-Develop-built.app`.
	- **macOS Gatekeeper:** the app is not code-signed, so macOS will block it on first launch. After attempting to open it and seeing "app can't be opened", go to **System Settings → Privacy & Security → Security**, click **Open Anyway** next to the blocked app, then click **Open Anyway** again in the security dialog.
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

- Ensure clocks are synchronized on all machines. Desync above ~30 ms (one frame time) will distort latency measurements and may cause plots to fail. Use **ChronyControl** on Mac and **NetTime** (also known as `timesynctool`) on Windows.
- Ensure Windows machines use a **dot as the decimal separator**. VR2Gather's stats formatter is locale-sensitive; a comma decimal separator (common in European Windows locales) corrupts the stats log (see [VR2Gather #318](https://github.com/cwi-dis/VR2Gather/issues/318)). Until fixed: change this in Settings → Time & Language → Region → Additional settings.
- Ensure the correct _VRTrunserver_ is running on all end-user computers.
- On the controlling computer, in the experiment directory:
	- Activate the venv with `source .venv/bin/activate` (Mac/Linux) or `.venv\Scripts\activate` (Windows)
	- Run `VRTrun`
- The end-user computers should start their VR2Gather applications.
- After the VR2Gather applications have all terminated the results will be collected.
	- They will be in an output directory that has a timestamped name, such as `run-20250319-1230`.
	- Within that directory, there are per-role subdirectories.
	- Within each of those, all the log files from the run are stored. The configuration files that were used are stored there too.
	- This all taken together means that the output directory contains all the information needed to repeat a run, if needed in the future.

## Analyzing the results

See [testing.md](testing.md) for a full end-to-end walkthrough including ingesting logs and producing plots.

Quick summary: after a run, use `VRTstatistics-ingest -a latency` (or `--norun <dir>` to re-ingest an existing run). Results land in `run-YYYYMMDD-HHMM/combined.json`. Plot with:

```python
from VRTstatistics.datastore import DataStore
from VRTstatistics.plots import plot_latencies
import matplotlib.pyplot as plt
ds = DataStore("run-YYYYMMDD-HHMM/combined.json")
ds.load()
plot_latencies(ds)
plt.show()
```

For exploratory analysis, load `combined.json` into Jupyter and use the `DataStore` API directly — `get_dataframe(predicate, fields)` gives you a pandas DataFrame you can manipulate freely.

To export selected fields to CSV for external tools, use `VRTstatistics-filter`:

```
VRTstatistics-filter -d combined.json -o output.csv -p 'predicate' field1 field2
```

The `--predicate` option is a Python boolean expression (`sessiontime > 10`, `"fps" in record`). Field arguments select and rename columns; `role=fps` uses the value of the `role` field as the column name.

> Examples to be provided. Also need examples for field constructs like `role=latency_ms`.


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

## Performance testing guidelines

Writing this down here because I keep forgetting. After running the plots, check:

1. First graph is points per cloud. Ensure that this has the shape you expect, given the prerecorded stream you think you've selected, or however the subject moved in front of the camera.
2. Second graph is latencies, end-to-end and from different components. Eyeball and apply common sense.
3. Framerates per component. You may have to zoom in because of outliers. Check these confirm to what you think you've selected. 
4. Dropped frames per second, per component. If they're not all zeroes you should be able to come up with a good reason why not. 
   
   **Note** if you get serious frame dropping somewhere on the sender side your sender hardware is not powerful enough. Lowering framerate or pointcount is the only option.
5. Timestamp progression in source capturer and destination receiver. Should be linear upsloping lines with sender ahead of receiver.
