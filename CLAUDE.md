# VRTstatistics

This repo contains three Python packages with a shared `.venv`, managed as a monorepo.

## Packages

| Package | Entry point(s) | Role |
|---|---|---|
| `VRTrunserver` | `VRTrunserver` | Flask HTTP server (port 5002) embedded in VR2Gather builds; responds to commands from VRTrun |
| `VRTrun` | `VRTrun` | Remote-control client: reads `config/runconfig.json`, uploads per-machine configs, starts players, collects results |
| `VRTstatistics` | `VRTstatistics-ingest`, `-filter`, `-plot`, `-stats2json` | Parses log files, annotates and aligns multi-machine data, produces matplotlib plots and CSV exports |

## Use Cases

VRTstatistics/VRTrun serves three distinct purposes, which evolved over time:

**1. System-oriented experiments** (original purpose): Automated runs with no participants, varying transport protocol, framerate, encoder quality (octreeBits), tiling on/off. Goal: latency, bandwidth, resource usage for system-focused scientific papers. Multiple runs per configuration provide statistical robustness.

**2. User-centric experiments** (later addition): Sessions with two real users interacting in a VR experience. Goal: human behaviour metrics — turn-taking in speech, gaze direction/heat maps, movement and interaction patterns — for user-focused papers. Few or no parameter variations; key metadata is a participant number for matching to questionnaires/interviews. Requires completely different analysis from system experiments.

**3. Demo/exhibition control** (later addition): VRTrun used to start/stop VR2Gather on multiple machines from one laptop, avoiding running between rooms. Logs are timestamped for post-hoc debugging. No upfront analysis intended.

## System-oriented experiment structure

Each experiment lives in its own directory (often its own git repo or subdirectory of one). Conventional layout:

```
my-experiment/
  _config/                    # base config template, shared across all variants
    config.json
    config-user.json
    runconfig.json
    sender/config-user.json   # per-role overrides if needed
    receiver/config-user.json
  tiled_octree9_fps15/        # one directory per parameter combination
    config/                   # hand-edited copy of _config for this variant
    _run-20260528-1340/       # discarded/test run — underscore prefix excludes from analysis
    run-20260528-1410/        # actual run (multiple runs per variant for statistics)
    run-20260528-1430/
    run-20260528-1450/
  untiled_octree7_fps15/
    config/
    run-YYYYMMDD-HHMM/
    ...
  create_plots.py             # experiment-level batch plotting driver
```

**Variant naming:** encode the key parameters in the directory name (e.g. `tiled_octree9_fps15_socketio`).

**Hand-code each variant config.** Do not generate them programmatically. The effort of hand-coding forces justifying each variant before running it, keeping scope manageable and the paper story clear. (A `create_json_run.py` script exists in `2024-spirit-lldash/experiments/scripts/` and was used historically, but led to too many variants and an unclear story.)

Running each variant multiple times:
```bash
VRTstatistics-ingest -a latency --config tiled_octree9_fps15/config
# repeat N times for statistical robustness
```

**Plotting:** Each experiment needs a `create_plots.py` driver that calls `VRTstatistics.plots` functions and saves output alongside each `combined.json`. See `2024-spirit-lldash/experiments/scripts/create_plots.py` for a reference implementation. A proper `VRTstatistics-plot` command is planned (issue #21) but not yet implemented.

## Development Setup

```
python3 -m venv .venv
source .venv/bin/activate          # Mac/Linux
pip install -e VRTrun
pip install -e VRTrunserver
pip install -e VRTstatistics
```

All three packages share the `.venv` at the repo root. Python ≥ 3.12 is required.

VS Code: select the `.venv` interpreter with `Python: Select Interpreter`. A `launch.json` for debugpy attach is in `.vscode/`.

Most tools accept `--debugpy` (waits for debugpy attach on port 5678) or `--pausefordebug` (waits for a keypress to attach by PID).

## Data Flow

```
VR2Gather app  →  "stats: key=value,..." lines in log file
                          ↓
               VRTrun collects into run-YYYYMMDD-HHMM/<role>/
                          ↓
          VRTstatistics-ingest parses + annotates → combined.json
                          ↓
        VRTstatistics-plot / -filter / Jupyter notebook
```

### Running a session

See `testing.md` for a full step-by-step walkthrough including current config file formats and common failure modes.

1. Ensure VRTrunserver is running on each end-user machine.
2. Create a `config/` directory containing `runconfig.json` (list of `{role, address}` entries).
   Per-role subdirectories (`config/<role>/`) are uploaded to the corresponding machine — files there overwrite the top-level files.
3. Run `VRTrun` from the experiment directory.
   Results land in `run-YYYYMMDD-HHMM/<role>/` (log files + configs used).

### Ingesting and analyzing

`VRTstatistics-ingest` can both run the session and ingest:
- Runs the session (unless `--norun <dir>` is passed to re-ingest an existing run).
- Parses `stats.log` and (if present) `rusage.log` or `vq-brisque.log` from each role.
- Applies an annotator (`-a latency` is the main one) to add `component_role`, align clocks, and merge.
- Saves `combined.json` in the run directory.

## Key Concepts

### The stats log format

VR2Gather components write lines like:

```
stats: component=PointCloudRenderer#7, seq=1234, ts=12.345, fps=30, ...
```

`parser.py` extracts these into dicts, converting numeric strings to int/float. It also converts the midnight-based `ts=` timestamps to `localtime` and `orchtime` (NTP-based) once it sees the orchestrator time-sync record.

### DataStore

`datastore.py` is the central data container. It loads `.log`, `.json`, or `.csv` files and exposes:
- `get_dataframe(predicate, fields)` — returns a pandas DataFrame
- `filter(predicate, fields)` — returns a filtered DataStore
- `find_first_record(predicate)` / `find_all_records(predicate)`

Predicates are Python boolean expressions evaluated with the record fields as globals. The special name `record` refers to the whole dict, e.g. `'"fps" in record'`.

### FieldSpecifier syntax

When calling `get_dataframe(fields=[...])` or `filter(fields=[...])`:

| Syntax | Meaning |
|---|---|
| `"fps"` | include field `fps` as-is |
| `"role=fps"` | use value of field `role` as the output column name, value from `fps` |
| `"component_role.=fps"` | column name = `component_role` value + `.` + `"fps"` |
| `"f1.f2=fps"` | column name = `f1` value + `.` + `f2` value |

This is how per-component columns like `sender.pc.grabber.fps` are generated from records that each have a `component_role` and an `fps` field.

### component_role

The `Annotator` examines structure records early in each log to identify pipeline components by name, then adds a `component_role` field to every record. The naming hierarchy:

**Sender side:**
- `sender.pc.grabber` / `sender.pc.encoder` / `sender.pc.writer.{tile}`
- `sender.voice.grabber` / `sender.voice.encoder` / `sender.voice.writer`

**Receiver side:**
- `receiver.pc.reader.{tile}` / `receiver.pc.decoder.{tile}` / `receiver.pc.preparer.{tile}` / `receiver.pc.renderer.{tile}`
- `receiver.pc.tileselector`
- `receiver.synchronizer`
- `receiver.voice.reader` / `receiver.voice.decoder` / `receiver.voice.preparer` / `receiver.voice.renderer`

`{tile}` is a zero-based integer, or `all` for protocols (SocketIO, TCPReflector) that use a single reader/writer for all tiles.

### Annotators

`annotator.py` contains the annotator hierarchy:
- `Annotator` — base: aligns timestamps, adds `sessiontime` and `role` fields
- `LatencySenderAnnotator` / `LatencyReceiverAnnotator` — add `component_role`; discover protocol, nTiles, nQualities
- `LatencyCombinedAnnotator` — merges sender + receiver into one sorted DataStore; records experiment metadata (protocol, nTiles, desync, usernames)

The `combine()` function drives the full annotation pipeline.
The `deserialize()` function reconstructs an Annotator from the metadata embedded in `combined.json`.

### Plotting (plots.py)

Main functions (all accept a `DataStore` as first argument):
- `plot_latencies()` — stacked area (queue/encode/decode durations) + line overlay (end-to-end latency). The main plot for latency experiments.
- `plot_framerates()` / `plot_framerates_dropped()` / `plot_framerates_and_dropped()`
- `plot_pointcounts()` — receiver point counts over time
- `plot_resources()` — CPU, memory, bandwidth (from `rusage.log`)
- `plot_latencies_per_tile()` — per-tile breakdown (requires nTiles > 1)

`analyze.py` provides `TileCombiner` and `SessionTimeFilter`: chainable `DataFrameFilter` objects used internally by the plot functions to aggregate per-tile columns.

## Output Directory Structure

```
run-YYYYMMDD-HHMM/
  sender/
    stats.log       # VR2Gather stats output
    rusage.log      # resource usage (CPU, mem, bandwidth)
    config*.json    # config files that were used
  receiver/
    stats.log
    rusage.log
    ...
  combined.json     # merged + annotated data (written by VRTstatistics-ingest)
```

## Known Issues / Historical Artifacts

- **`VRTstatistics-combine`** appears in the installed `.venv/bin` but is not in the current `setup.cfg` — leftover from an older version.
- **`scripts/` at repo root** (`getlogs.sh`, `genplots.sh`, etc.) — explicitly documented as outdated in `readme.md`. Probably dead.
- **`plot_latencies_rev()`** in `plots.py` — an experimental variant (sender/receiver roles reversed?), not in `__all__`, not documented. Needs review.
- **`analyze.py` TileCombiner logic** — the interaction between `combined`, `keep`, and `previous_filter` is subtle and the code has some rough edges (e.g. the length-adjustment loop at lines 95-99). Worth a cleanup pass.
- **No example Jupyter notebooks** despite Jupyter being a stated dependency and the readme recommending it.
- **`readme.md`** still has an "Analyzing the results: To be provided" section and an "Old readme" section that contradicts the current workflow.
