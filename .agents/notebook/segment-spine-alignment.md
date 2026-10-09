# Leg Segment Spine Alignment

## Problem
In procedural limb modeling (`houspider/segments/cube.py`), limb segments previously positioned each section within a segment with bounds `[-h / 2, +h / 2]`, aligning sections along their centroids (`center_y = 0.0`). Consequently, any segment whose sections varied in height had discontinuous spine positions (`Y_spine = Y_top - h * spine_ratio`) across sections, even though inter-segment joints aligned the consecutive segment ends along `spine_ratio`.

## Formulation
Given a reference section of height `h_ref` and a target section of height `h`:
- Vertical shift of target top edge relative to reference top edge:
  `delta_y_top = (h - h_ref) * spine_ratio`
- Vertical shift of target center relative to reference center:
  `delta_y_center = (h_ref - h) / 2 + delta_y_top = (h_ref - h) * (0.5 - spine_ratio)`

When each section `i` in a segment is positioned with `y_center = delta_y_center(h_0, h_i, spine_ratio)`:
- The spine position `Y_spine = y_top - h * spine_ratio = h_0 * (0.5 - spine_ratio)` remains constant across all sections in the segment.
- Since section 0 has `y_center = 0`, inter-segment joint positioning and wedging remain directly compatible without offset compounding.
- Across joints, the spine line continues seamlessly through the full leg from Coxa to Tarsus.
