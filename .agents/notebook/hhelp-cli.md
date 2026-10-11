# Houdini `hhelp` CLI Reference & Workarounds

## Overview
`hhelp` (`/opt/hfs<version>/bin/hhelp`) is SideFX Houdini's command-line help utility powered by the Bookish documentation engine (`houdinihelp`).

## Official Primary Use Cases
1. **Central Help Server:**
   ```shell
   hhelp serve --host=0.0.0.0 --port=8080 --bgindex=true
   ```
   Hosts documentation locally over HTTP. Widely used in studio pipelines to avoid every workstation spinning up individual help servers.
2. **Static Generation:**
   ```shell
   hhelp generate <dirpath>
   ```
   Pre-renders all documentation into static HTML for hosting via Nginx/Apache.
3. **Index Management:**
   ```shell
   hhelp index --clean
   ```
   Rebuilds the local full-text search index (stored in `$HFS/houdini/config/Help/index3.0`).

## Terminal Querying Workflows

### 1. Searching for Help Paths (`search`)
Query Houdini's built-in search index:
```shell
hhelp search "<query>"
```
Examples:
- `hhelp search "capture packed"` -> `/nodes/sop/kinefx--capturepackedgeo Capture Packed Geometry`
- `hhelp search "cross"` -> `/vex/functions/cross cross`, `/hom/hou/Vector3#cross`
- `hhelp search "polyextrude"` -> `/nodes/sop/polyextrude Poly Extrude`

### 2. Reading Formatted Documentation (`textify`)
Avoid `hhelp html <path>` in the terminal; it outputs raw HTML boilerplate (CSS, scripts, nav containers).
Instead, use `hhelp textify` to convert pages into formatted plain text.

> **Bug in Houdini Python 3**:
> Running `hhelp textify <path>` directly to stdout fails with `TypeError: write() argument must be str, not bytes` (`houdinihelp/cli.py:391`).
> **Workaround**: Output to a file with `-o`:
```shell
hhelp textify -o /tmp/doc.txt /nodes/sop/kinefx--capturepackedgeo
cat /tmp/doc.txt
```
This produces clean text containing the summary, usage tips, and full parameter lists.
