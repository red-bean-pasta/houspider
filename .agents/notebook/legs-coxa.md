# Legs and Coxa Modular Decomposition

## SOP Pipeline Architecture
The monolithic `extrude_legs` SOP was decomposed into sequential SOP stages connected via `sopify_chain` in `houspider/legs/build.py`:
1. `record_global_info`: Global attribute assignment for joint limits.
2. `extract_right_leg_points`: Prunes geometry to right-side socket points.
3. `build_basic`: Constructs straight 4-leg segments (tubes, loop cuts, membranes, tarsus) at the origin with full point ID tags.
4. `position_basic`: Translates and rotates each leg's points from origin into place matching each socket frame.
5. `adjust_coxa_start`: Adjusts coxa start loop positions according to `coxa_start_wedge_angle` and updates intermediate coxa loops.
6. `fill_coxa_upper_pentagon`: Generates upper buffer pentagon faces and attributes `legsegmentinset(leg_idx, 1, 1, 4/3)` and `legsegmentbuffer(leg_idx, 1, 1/2)`.
7. `fill_coxa_bottom_pentagon`: Generates bottom buffer pentagon faces and attributes `legsegmentinset(leg_idx, 1, 1, 1/2)` and `legsegmentbuffer(leg_idx, 1, 3/4)`.
8. `fill_coxa_back_faces`: Builds the 2 quad faces on the back (+Z) side.
9. `fill_coxa_front_faces`: Builds the front (-Z) transition quads connecting socket to coxa.
10. `cleanup`: Default primitive region tagging.

## Fixed: Duplicate Vertex in Front Faces
In `fill_coxa_front_faces`, the third front quad:
```python
fill_face([b_start_b1, b_start_b1, start_b1, start_u1])
```
repeated `b_start_b1` twice. This was corrected to:
```python
fill_face([b_start_u1, b_start_b1, start_b1, start_u1])
```
matching the `[top_left, bottom_left, bottom_right, top_right]` quad winding conventions of the neighboring faces.

## Position Basic: Top Edge Alignment
Previously, `position_basic` set `origin.y = top_mid.y()`, placing the leg's centroid (`y = 0`) at the socket's top edge midpoint. This caused the leg to sit half its height too high.
Fixed in `_get_leg_socket_frame` by querying the unpositioned coxa start loop top edge midpoint `leg_top_y = (p_u1.y + p_u2.y) * 0.5` (points `legsegmentedge(leg_idx, 1, 1, 4)` and `legsegmentedge(leg_idx, 1, 1, 3)`), and computing:
```python
origin.y = top_mid.y() - leg_top_y
```
This guarantees the coxa start loop's top edge midpoint is aligned in Y with the socket top edge midpoint `(basecoxamemebrane_4 + basecoxamemebrane_3) * 0.5`.

## adjust_coxa_start: Midpoint-Driven Wedge Projection
Previously, `adjust_coxa_start` moved corners along divergent corner-to-corner vectors using coxa end loop heights, distorting the coxa loop width from 144.8 down to 104.5.
Rewritten from scratch:
1. Projects bottom edge midpoint from `basecoxamembranemiddle(leg_idx, 1)` along the leg's local `-z` direction (`direction`) by `wedge_offset = y_delta * tan(wedge_angle)` on the bottom XZ plane. Moves bottom edge rigidly.
2. Calculates `ratio = wedge_offset / total_len_b` along the coxa length.
3. Positions top edge midpoint at `pos_stm + (end_mid_u - pos_stm) * ratio` and moves top edge rigidly.
4. Updates support loops and intermediate loops via `update_intermediate_positions`.
Preserves 100% of coxa start width across all 4 legs without distortion.

## Intermediate / Support Loop Position Resolution: Baseline + Offset Decomposition
Previously, after `adjust_coxa_start` moved the start loop, `support_1` loops had bizarre distorted shapes sagging downwards and shifted along local right.
Root cause:
`update_intermediate_positions` only computed displacement along corner 0's `local_z` vector (`segment[0] - segment[-4]`) and applied `displacement = local_z * (target - segment[idx]).dot(local_z)`. In world space after `position_basic`, the start loop moved 80+ units transversely perpendicular to `local_z`. Projecting onto `local_z` discarded all transverse movement, leaving intermediate points anchored at their old transverse world coordinates. Furthermore, using corner 0's vector for corners 2 and 3 sheared top corners along the bottom corner's orientation.
Fix:
Implemented clean **baseline + offset decomposition** in [`houspider/segments/helper.py`](file:///home/xuh/Documents/git-him-back/houspider/houspider/segments/helper.py):
1. `compute_intermediate_ratios`: For each intermediate point `p` at corner `c`, captures ratio `t` and the section-size deviation `offset_vec = p - (start[c] * (1 - t) + end[c] * t)`. (Zero for support loops, non-zero for custom-sized intermediate sections).
2. `update_intermediate_positions`: Calculates the new baseline `target = start_new[c] * (1 - t) + end_new[c] * t + offset_vec` along each corner edge independently.
This preserves 100% of custom section width/height differences when present, tracks arbitrary 3D movements/wedges without transverse drift, and eliminates the `linear` flag entirely.

## Scripts Additions & Enhancements
- [`scripts/list_nodes.py`](file:///home/xuh/Documents/git-him-back/houspider/scripts/list_nodes.py): Search and list scene nodes under a root path with glob matching, type filters, and input inspection.
- [`scripts/inspect_geo.py`](file:///home/xuh/Documents/git-him-back/houspider/scripts/inspect_geo.py): Added glob matching for attribute values and `--unique` to inspect unique attribute value distributions.
- [`scripts/inspect_parms.py`](file:///home/xuh/Documents/git-him-back/houspider/scripts/inspect_parms.py): Inspect node parameters, values, labels, and modified overrides on any node in a HIP file.
- [`scripts/measure_geo.py`](file:///home/xuh/Documents/git-him-back/houspider/scripts/measure_geo.py): Extended `-p`/`--points` to handle 1 point (coordinates, radius, elevation), 2 points (edges), 3 points (corner angles and normals), and 4 points (quad loop widths, heights, diagonals, centroid, coplanarity). Added optional positional `hip_file` argument.
## Ratio Equivalence Verification
Verified across all 4 legs in `adjust_coxa_start`:
Projected to local -z (`direction = (pos_stm.xz - pos_sbm.xz).normalized()`), the ratio:
`(m_socket_bottom -> m_start_bottom) : (m_start_bottom -> m_end_bottom)`
strictly equals:
`(m_socket_top -> m_start_top) : (m_start_top -> m_end_top)`
- Leg 1: Ratio = 0.504525 (Split = 1.018267), difference = 6.49e-09
- Leg 2: Ratio = 0.392901 (Split = 0.647179), difference = 1.01e-09
- Leg 3: Ratio = 0.309426 (Split = 0.448071), difference = 5.38e-08
- Leg 4: Ratio = 0.329194 (Split = 0.490744), difference = 1.83e-08
Identical down to machine epsilon across all legs.
