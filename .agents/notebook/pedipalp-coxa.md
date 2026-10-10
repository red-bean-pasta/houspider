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

