# Base Shape & Geometric Topology

## Shape Overview & Analogy
- **Peripheral Collar / Flared Brim**: The base forms an outward-flaring radial collar extruded directly around the perimeter of the sternum.
- **Anatomical Role**:
  - Bridges the ventral sternum plate to the lateral flanks and dorsal carapace.
  - Houses the 4 pairs of walking leg articulation sockets laterally.
  - Shapes the mouthparts (labium and maxillae) along the anterior margin.
  - Forms the pedicel waist bridge at the posterior apex.
- **Spatial Orientation**:
  - **Symmetry**: Bilaterally symmetric across `X = 0`.
  - **Upward Flaring (+Y)**: Unlike the sunken central sternum, the base flaps angle upwards, elevating the outer perimeter and forming the concave undercarriage of the spider prosoma.

## Coxa Flap Formation & Radial Geometry
- **Radial Extrusions**: Outset directly from the sternum rim edges, creating radiating quadrilateral flaps whose radial length is scaled by `coxa_height_ratio`.
- **Flap Elevation Angle**: Each lateral coxa flap is rotated upwards around its sternum rim hinge by `coxa_rise_angle` (e.g. 12°), lifting the coxa beds out of the ventral horizontal plane.
- **Perpendicular Projection**: Outer flap midpoints project perpendicular in the horizontal plane (XZ) to their respective sternum rim segments, ensuring coxa sockets align cleanly with leg axes.
- **Symmetric Flap Outlines**: Flap corner vertices are mirrored across the central mid-axis of each socket to produce balanced, clean rectangular/trapezoidal coxa beds.

## Anterior & Posterior Transitions
- **Anterior Margin (Labium & Maxillae)**:
  - **Labium Shelf**: The front center extrudes into a straight, level transverse front shelf representing the labium (lower lip).
  - **Maxilla Wings**: At the anterolateral corners between the labium and Coxa 1, dedicated quads fill the diagonal gap, forming outward-flaring maxillae (endites) for pedipalp articulation.
- **Posterior Apex (Pedicel Waist)**:
  - The trailing gap between the left and right 4th coxa flaps closes into a rearward-extending quad centered on `X = 0`.
  - Forms the ventral collar of the pedicel (the anatomical waist connecting prosoma to abdomen).

## Socket Cavities & Concentric Membrane Bands
- **Open Articular Sockets**:
  - Each coxa, maxilla, and labium region is inset to separate the central socket aperture from its surrounding border.
  - The interior socket faces are hollowed out (primitives deleted), leaving open window apertures where leg coxae articulate.
- **Tunable Membrane Borders**:
  - The quads surrounding each open socket form flexible articular membrane borders, with independently configurable side, distal (upper), and proximal (lower) margins via `socket_membrane_ratio`.
- **Outermost Buffer Ring**:
  - An all-around boundary outset loop surrounding the entire base perimeter (`BASEBUFFERMEMBRANE`).
  - Acts as the transitional weld flange that fuses the ventral base assembly directly into the dorsal carapace.
