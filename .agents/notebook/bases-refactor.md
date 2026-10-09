# Bases Refactoring & Houdini Geometry Findings

## Architecture & Pipeline
- **Sternum Growth Composition**: `houspider.bases` refactored from independently extruded coxa flaps that merge-fused with sternum to directly outsetting from sternum primitives (`houkit.topology.outset(list(geo.prims()), ...)`).
- **Prosoma Integration**: In `houspider.prosomas.build`, `merge_fuse_sternum_and_coxa` is eliminated. `base` outputs the complete sternum + bases mesh, which is fed directly into `build_dorsal` and `merge_fuse_base_and_dorsal`.
- **Subnet Indirect Inputs**: Inside `add_reloadable_subnet`, child SOPs must take `base.indirectInputs()[0]` as root input rather than the external parent input node.

## Parameter Contract (`houspider/bases/parameters.py`)
- Subnet parameters on `base`:
  - `coxa_height_ratio`: Outset reach for coxa flaps relative to sternum rim edges.
- Null `CONTROLS` parameters:
  - `coxa_rise_angle`: Flap elevation angle in degrees.
  - `socket_membrane_ratio` (3-tuple): Vector parameters representing side, upper, and lower membrane widths.
  - `dorsal_membrane_ratio`: Width of outer buffer membrane connecting base to dorsal.

## Topology & Attributing Rules
- **Outset Vertex Layout**: `houkit.topologies.face_offseter.outset` creates border quads where:
  - `points[0]` and `points[3]` are the inner boundary vertices (attached to sternum).
  - `points[1]` and `points[2]` are the newly created outer outset vertices.
  - Flap rotations must only process `Region.COXA` primitives, pair `(points[0], points[1])` and `(points[3], points[2])`, and set position relative to origin: `origin.position() + Vector3(offset.x * cos, length * sin, offset.z * cos)`. Calling `offset_point` erroneously accumulates onto existing coordinates.
- **Substring ID Replacements**: `STERNUMRIMMIDDLE` (`sternumrimmiddle`) contains `STERNUMRIM` (`sternumrim`) as a substring; string replacement must replace `STERNUMRIMMIDDLE` first before replacing `STERNUMRIM`.
- **Split IDs**:
  - `outset` points at indices 2, 3, 4 are undivided single points (`basesternum2`, `basesternum4`). Only 1, -1 (maxilla) and 5 (pedicel) are split into minor IDs `_1` and `_2`.
- **Inner Primitive Attribute Assignment**: `inset_inner_prims` returns only newly generated inner polygon primitives. Points on these inner primitives appear exactly once per ID, so IDs are assigned directly to point objects on `inner_prims` rather than indexing into global geometry point lists.
- **Pedicel Orientation**:
  - Spider anterior is negative Z (`sternumrim(0)` at $z \approx -187$).
  - Spider posterior is positive Z (`sternumrim(5)` at $z \approx +163$).
  - `baseend(0)` extends posterior along positive Z: `s5.position() + Vector3(0, y, z)`.
- **Downstream Dorsal Contract**:
  - `houspider.dorsals.base.extract_work_base` extracts points on the right half (x >= -1e-4) and asserts `expected_ids`: `sternumrim(0)`, `dorsalchelicerae(0)`, `basesternum(0)`, `basesternum(1, 2)`, `basesternum(3)`, `basesternum(5, 1)`, and `baseend(0)`.
  - `basesternum(5, 1)` must reside on the positive-X side to satisfy this contract.

## Outset Extruded Edges Rotation
- **Middle Edge Perpendicularity**: Outset computes vertex deltas following boundary corner bisectors or interior edge directions. For extruded edges connecting `sternumrimmiddle*` to `basesternummiddle*`, outset does not naturally preserve perpendicularity to the corresponding sternum rim edge.
- **Orientation Correction**: `rotate_middle_edges` rotates each extruded vector `(basesternummiddle - sternumrimmiddle)` around the Y axis passing through `sternumrimmiddle`. This preserves its original elevation angle to the XZ plane and total edge length while aligning its XZ projection perpendicular to the sternum rim edge (`sternumrim(i)` to `sternumrim(i+1)`).
- **Rim Edges Averaging**: `correct_rim_edges` repositions extruded corner vertices `basesternum(i)` for `i in (2, 3, 4)` and `(-2, -3, -4)` to the midpoint of their adjacent `basesternummiddle` neighbors: `(bsm(i-1) + bsm(i)) * 0.5`. Indices 0, 1 (and 1_1, 1_2), and 5 (and 5_1, 5_2) are excluded.

## Outset Ratio & Skew Mechanics
- **Half-Edge Boundary Evaluation**: `outset` evaluates `scalar` against the lengths of boundary edges directly adjacent to each vertex. Because `sternumrimmiddle*` vertices divide each sternum rim edge into two halves (`l_in = l_out = 0.5 * rim_edge_len`), `scalar = flap_ratio` yields an extrusion reach relative to the half-edge (`base_dist = 0.5 * rim_edge_len * flap_ratio`), which is half of the full rim length. Passing `flap_ratio * 2.0` scales the base reach to match `rim_edge_len * flap_ratio`.
- **Interior Edge Skew and Projection Inflation**: When `follow_existing_edge=True`, `outset` projects the offset along existing interior mesh edges (`-e_dir`) and scales the distance by `1 / cos_phi` (where `cos_phi = e_dir . n_inward`). At `sternumrimmiddle4`, the connecting interior edge to transition quad point 51 is angled at ~44.2 degrees relative to the boundary inward normal (`cos_phi ≈ 0.7171`):
  - **Length Inflation**: `dist = base_dist / cos_phi` inflates the extruded edge length by `1 / 0.7171 ≈ 1.395` (almost 40% longer than `basesternummiddle2` / `basesternummiddle3`).
  - **Direction Skew**: The interior edge direction points towards positive X and negative Z, so the outward extrusion `(-e_dir)` points towards negative X (inward toward spider midline) and positive Z (posteriorly), causing a severe directional skew compared to the rim normal.

## Midline Symmetry & Tolerance Invariants
- **Outset Numerical Float Drift**: Boundary outset bisectors accumulate float inaccuracy (e.g. `X ≈ -0.0008` instead of `0.0`). Midline vertices (`basesternum(0)`) are snapped to `X = 0.0` right upon creation in `extrude_sternum_rim` (`_align_midline_points`) and outer midline points (`basesternum(0)`, `baseend(0)`) are snapped in `extrude_base_buffer` (`_snap_midline_points`).
- **Downstream Right-Half Filtering**: With midline points correctly snapped to `X = 0.0` at the generation stages, `houspider.dorsals.base.extract_work_base` cleanly uses standard `x >= -1e-4` filtering without special-case `or` conditions.
- **`fill_face_with_attr` Contract**: `houspider.helper.fill_face_with_attr(points, attribute, value, reverse=False)` does not take `geo`. All consumers across `cheliceraes` (`sections.py`, `geometry.py`), `pedicel.py`, and `helper.py:bridge_loops` pass `points` directly.


