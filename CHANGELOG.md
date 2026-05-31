# Changelog

All notable changes to this project will be documented here.

Version numbers follow VR2Gather major.minor, with an independent patch number for
fixes and improvements within a VR2Gather release cycle. Versions are derived from
git tags (see `FILEVERSION` / `OLDEST_COMPATIBLE_VERSION` in `datastore.py` for the
combined.json format version scheme).

## [Unreleased] — targeting 1.4.0

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
