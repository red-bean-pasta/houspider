# Pedipalp Coxa Geometry & Maxilla Pole

## Coxa Tube Corners & Orientation
For pedipalp segment 1 (coxa):
- `pedipalpsegmentedge(1, 1, -1, corner_idx)`:
  - 1: LB (left bottom / medial bottom)
  - 2: RB (right bottom / lateral bottom)
  - 3: RU (right upper / lateral top)
  - 4: LU (left upper / medial top)
- Medial boundary of coxa has lower X coordinates (`X ~ 42..88`), facing the midline/mouth. Lateral boundary has higher X coordinates (`X ~ 111..128`).

## Maxilla Pole Calculation (`_get_maxilla_pole`)
- **End Plane Definition**: The end face of the coxa tube (joint with trochanter) is defined by three points:
  - `e1`: LB (`pedipalpsegmentedge(1, 1, -1, 1)`)
  - `e2`: LU (`pedipalpsegmentedge(1, 1, -1, 4)`)
  - `e3`: RU (`pedipalpsegmentedge(1, 1, -1, 3)`)
- **Forward Projection Direction**: The extrusion direction along the coxa tube uses `_get_coxa_base_direction(geo)` (collinear with `e3 - es3`), rather than socket attachment diagonals like `m4 - m1` which diverge laterally.
- **Offset Alignment**: `v2 = (e1 - e2).normalized()` defines the downward vertical vector along the medial edge of the tube (LB - LU), lowering the pole centroid to align with `ct2` (`pedipalpcoxabuffer(1, "base", 2)`) at `Y ≈ -14.32`.

## Maxilla Opening Rim & Base Trapezoid
- `pedipalpcoxabuffer(1, "base", 2)` (`pos_p4`) is anterior (`Z ≈ -585`), adjacent to `m2`.
- `pedipalpcoxabuffer(1, "base", 1)` (`pos_p3`) is posterior (`Z ≈ -464`), adjacent to `m1`.
- Along the base trapezoid quad, edges are `(m1, m2)`, `(m2, ct2)`, `(ct2, ct1)`, `(ct1, m1)`.
- The open rim of the maxilla follows perimeter: `m2 -> ct2 -> ct1 -> cb -> cfb -> cf -> m2`.
- `fill_maxilla_faces` bridges `p0..p5` to this rim via `[p0, m2, ct2, p4]`, `[p4, ct2, ct1, p3]`, and `[p3, ct1, cb, p2]`.

## Coxa Socket & End Section Aspect Ratio
- **Front Leg Socket Ratio**: `hw_ratio = front_coxa_height / front_coxa_width` (evaluated from `basecoxamembranemiddle(1, 2) - (1, 1)` and `basecoxamemebrane(1, 3) - (1, 4)`).
- **Pedipalp Base Socket Sizing**:
  - `pedipalp_socket_width = length(bm3 - bm4)`
  - `pedipalp_socket_height = pedipalp_socket_width * hw_ratio`
- **End Coxa Cross-Section Aspect Ratio**:
  - Pedipalps coxa sections inherit `(w_ratio, h_ratio)` from leg parameters (`param.segment_sections[0]`).
  - At any section $k$, `w_k = socket_width * w_ratio_k` and `h_k = socket_height * h_ratio_k`.
  - Since `socket_height / socket_width = hw_ratio` for both pedipalp and front leg, the aspect ratio `h_k / w_k = hw_ratio * (h_ratio_k / w_ratio_k)` is identical across both front leg and pedipalp end coxa sections.

## Coxa Length & Bottom Trim Mechanics
- **Parameter Calculation**:
  `pedipalp_coxa_length = front_leg_coxa_socket_width * legs.parm("coxa_length_ratio") * pedipalps.parm("coxa_length")`.
- **Initial Build**: In `build_basic`, coxa tube is constructed along `-Z` with length `pedipalp_coxa_length` from start loop ($Z=0$) to end section ($Z=-\text{pedipalp\_coxa\_length}$).
- **Trimming (`trim_bottom_side_length`)**:
  - `trim_length = length_xz(bm3 - bm1)`
  - Shifts all pedipalp points past loop 1 forward by `+trim_length` along $Z$.
  - This shortens the upper span from start to end to: `upper_length = pedipalp_coxa_length - trim_length`.
- **Positioning (`position_basic`)**:
  - Aligns `start 3` (Right Upper / lateral upper corner) to `bm4` (`basemaxillamembrane(4)`).
  - Upper side length from `bm4` to coxa end section is `pedipalp_coxa_length - trim_length`.
- **Bottom Span**:
  - Bottom attachment at `bm1` sits `~trim_length` posteriorly behind `bm4`.
  - The bottom reach from `bm1` to coxa end section is `(pedipalp_coxa_length - trim_length) + offset_axial(bm4 - bm1) ≈ pedipalp_coxa_length`.

## Base Trapezoid Inversion Handling
- In `_add_base_trapezoid`, `pos_p4` is the ray intersection point and `pos_p3` is its mirrored counterpart across `m1 - m2`.
- When `pos_p4` steps over `pos_p3` along `u = (m2 - m1).normalized()`, the quad `[m1, m2, p4, p3]` degenerates into an hourglass shape.
- Handled by `_is_trapezoid_inverted`: tests `(p_base2 - p_base1).dot(u) < 0`.
- If inverted, `_swap_point_ids(p3, p4)` swaps point IDs between the points and exchanges `p3, p4 = p4, p3`, so that `p4` (`base 2`) always resides near `m2` and `p3` (`base 1`) resides near `m1`, preserving proper quad topology without crossing.



