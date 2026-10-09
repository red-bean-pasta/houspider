# Houdini Development & Inspection Utilities

Command-line utilities for cooking, inspecting, measuring, and debugging geometry and nodes inside Houdini (`hython`).

---

## 1. Scene Build & Validation

### `build_test_hip.py`
Regenerates `test/test.hip` from the current project code.
```shell
hython scripts/build_test_hip.py
```

### `cook_and_check.py`
Cooks all nodes in a HIP file and reports any errors or warnings.
```shell
# Cook all nodes in the scene
hython scripts/cook_and_check.py test/test.hip

# Cook under a specific root subnet
hython scripts/cook_and_check.py test/test.hip --root /obj/spider/geometry/prosoma
```

### `list_nodes.py`
Lists and searches nodes across the scene graph with glob pattern and type filtering.
```shell
# List immediate children of a subnet
hython scripts/list_nodes.py test/test.hip --root /obj/spider/geometry/legs

# Search nodes matching pattern recursively
hython scripts/list_nodes.py test/test.hip --pattern "*leg*" -r

# Filter by node type with input connection display
hython scripts/list_nodes.py test/test.hip --root /obj/spider/geometry/legs --type python --inputs
```

---

## 2. Geometry Inspection & Measurement

### `inspect_geo.py`
Inspects point and primitive attributes, counts, and coordinates on any SOP node. Supports glob pattern matching and unique value aggregation.
```shell
# Filter points by attribute and value (or glob pattern)
hython scripts/inspect_geo.py /obj/spider/geometry/prosoma/base --attrib id --value basesternum2
hython scripts/inspect_geo.py /obj/spider/geometry/legs/OUT_LEGS --attrib id --value "legsegment1_1*"

# Inspect all distinct values and counts for an attribute
hython scripts/inspect_geo.py /obj/spider/geometry/legs/OUT_LEGS --attrib region --type prim --unique
```

### `diff_geo.py`
Compares a SOP node against its direct input (or an explicit reference node) to see what changed: displaced points, added/removed points, and modified attributes.
```shell
# Diff node against its input
hython scripts/diff_geo.py /obj/spider/geometry/prosoma/base/correct_rim_edges

# Diff against a specific reference node
hython scripts/diff_geo.py /obj/spider/geometry/prosoma/base/correct_rim_edges \
  --ref /obj/spider/geometry/prosoma/base/rotate_middle_edges

# Filter by minimum displacement distance
hython scripts/diff_geo.py /obj/spider/geometry/prosoma/base/rotate_coxa_flaps --min-dist 0.1
```

### `measure_geo.py`
Measures distances, vectors, horizontal reach (XZ), elevation angles, angular relationships between edges, and quad loops. Points can be specified by attribute `id` or point index (`#0` or `0`).
```shell
# Inspect a single point (coordinates, distance from origin, radius, elevation)
hython scripts/measure_geo.py /obj/spider/geometry/legs/adjust_coxa_start -p "#0"

# Measure a single vector (length, reach, elevation to XZ plane)
hython scripts/measure_geo.py /obj/spider/geometry/prosoma/base/rotate_middle_edges \
  -p sternumrimmiddle1 basesternummiddle1

# Measure a corner angle across 3 vertices (arms lengths, included angle, plane normal)
hython scripts/measure_geo.py /obj/spider/geometry/legs/adjust_coxa_start -p "#0" "#1" "#2"

# Analyze a 4-point quad loop (top/bottom widths, heights, diagonals, centroid, coplanarity)
hython scripts/measure_geo.py /obj/spider/geometry/legs/adjust_coxa_start -p "#0" "#1" "#2" "#3"

# Compare two edges (ratio, 3D angle, and XZ perpendicularity)
hython scripts/measure_geo.py /obj/spider/geometry/prosoma/base/rotate_middle_edges \
  --edge1 sternumrimmiddle1 basesternummiddle1 \
  --edge2 sternumrim1 sternumrim2

# Measure multiple point pairs in a summary table
hython scripts/measure_geo.py /obj/spider/geometry/prosoma/base/rotate_middle_edges \
  --pairs sternumrimmiddle1,basesternummiddle1 sternumrimmiddle2,basesternummiddle2
```

### `inspect_parms.py`
Inspects node parameter values, labels, and default overrides on any node in a HIP file.
```shell
# Inspect all parameters on a control node
hython scripts/inspect_parms.py /obj/spider/geometry/legs/CONTROL

# Filter parameter names or labels by glob pattern
hython scripts/inspect_parms.py /obj/spider/geometry/legs/CONTROL -p "*wedge*"

# Only show parameters modified from their defaults
hython scripts/inspect_parms.py /obj/spider/geometry/legs/CONTROL -m
```

---

## 3. Isolation & Introspection

### `run_stage.py`
Executes an isolated geometry processing function directly against an input node's geometry without needing a full scene cook.
```shell
hython scripts/run_stage.py houspider.bases.geos.coxa:correct_coxa_shape /obj/spider/geometry/prosoma/sternum
```

### `inspect_symbol.py`
Inspects docstrings, members, or Python source code across HOM (`hou`) and project modules.
```shell
# Filter members of a class
hython scripts/inspect_symbol.py hou.Geometry --filter point

# View source code of a function
hython scripts/inspect_symbol.py houkit.noder.sopify --source
```
