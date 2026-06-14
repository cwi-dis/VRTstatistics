# Changelog

All notable changes to this project will be documented here.

Version numbers follow VR2Gather major.minor, with an independent patch number for
fixes and improvements within a VR2Gather release cycle. Versions are derived from
git tags (see `FILEVERSION` / `OLDEST_COMPATIBLE_VERSION` in `datastore.py` for the
combined.json format version scheme).

## [1.4.0] — 2026-06-14

- Plot refactor (closes #21): extract / render / publish three-step pipeline
    - Introduce `PlotStyle` dataclass: `figsize`, `ylim_top`, `plot_kwargs`, `label_kwargs`, `tick_kwargs`, `legend_kwargs`, `legend_row_major` — construct once, reuse across all plots in an experiment
    - All `render_*` functions now take `style: PlotStyle`; `plot_*` wrappers remain backward-compatible
    - View registry: `View` subclasses self-register via `__init_subclass__`; `register_extractor` / `register_renderer` wire in functions (both overridable at runtime)
    - `VRTstatistics-plot --type NAME` produces a standard plot; `--list-types` enumerates registered types; `--import MODULE` loads external View subclasses
    - `extract_latencies` gains `show_framedrops` / `show_tileswitches` flags (replaces `show_disruptions` on `render_latencies`)
    - Add voice latency to `plot_latencies`; fix x-axis auto-scaling; role names in description
- Parser: fail fast on malformed stats lines (locale-induced comma decimal separators, cwi-dis/VR2Gather#318)
- Add `examples/latency-tiled-voice`; update `examples/latency` config
- readme: document NTP sync tools and Windows decimal separator workaround
- Refactor annotator into `SessionNormalizer` + declarative `AnnotationEngine` (closes #25)
    - New `VRTstatistics-annotate` CLI for re-annotating existing combined.json files
    - Add `--list` to `VRTstatistics-annotate` to show available annotation steps
    - Fix `combine()` to handle 1..N roles instead of exactly 2 (closes #23)
    - Fix `TileCombiner` double-applying `previous_filter` in chain (closes #19)
- Fix component_map collision when same component name appears on multiple machines
- Add `fileversion` to combined.json for schema compatibility checks
- Derive package versions from git tags via setuptools-scm
- Add `--version` to all CLI entry points

## [1.3.0] — last release before automated versioning

This is the last release that predates setuptools-scm version derivation. No
CHANGELOG was maintained before this point.
