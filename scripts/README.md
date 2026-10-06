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

---

## 2. Geometry Inspection & Measurement

### `inspect_geo.py`
Inspects point and primitive attributes, counts, and coordinates on any SOP node.
```shell
# Filter points by attribute and value
hython scripts/inspect_geo.py /obj/spider/geometry/prosoma/base --attrib id --value basesternum2

# Inspect primitive regions
hython scripts/inspect_geo.py /obj/spider/geometry/prosoma/base --type prim --attrib region
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
Measures distances, vectors, horizontal reach (XZ), elevation angles, and angular relationships between edges. Points can be specified by attribute `id` or point index (`#0` or `0`).
```shell
# Measure a single vector (length, reach, elevation to XZ plane)
hython scripts/measure_geo.py /obj/spider/geometry/prosoma/base/rotate_middle_edges \
  -p sternumrimmiddle1 basesternummiddle1

# Compare two edges (ratio, 3D angle, and XZ perpendicularity)
hython scripts/measure_geo.py /obj/spider/geometry/prosoma/base/rotate_middle_edges \
  --edge1 sternumrimmiddle1 basesternummiddle1 \
  --edge2 sternumrim1 sternumrim2

# Measure multiple point pairs in a summary table
hython scripts/measure_geo.py /obj/spider/geometry/prosoma/base/rotate_middle_edges \
  --pairs sternumrimmiddle1,basesternummiddle1 sternumrimmiddle2,basesternummiddle2
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
