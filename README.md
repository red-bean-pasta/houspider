# Houspider

A procedural spider model generator for SideFX Houdini. It builds a biologically plausible spider from Python and Houdini geometry attributes, then exposes the most useful shape and topology controls as editable Houdini parameters.

The final model is built as a Houdini node network, so the construction remains easy to inspect and debug.

Adjust the handles to explore different spider shapes without rebuilding the model by hand.


## How it works

The generator uses Houdini Python to create and connect the modeling network. Point, primitive, and global attributes identify anatomical regions and construction points as geometry moves through the network. The builder modules use those attributes to construct surfaces, connect regions, and expose controls on the generated nodes.

The project uses [`houkit`](https://github.com/red-bean-pasta/houkit) for reusable Houdini node, parameter, attribute, and reloadable-subnet helpers.


## Quick start

You need Houdini with `hython` available on your `PATH`.

1. Install dependency `houkit`:
```bash
hython -m pip install git+https://github.com/red-bean-pasta/houkit.git
```

2. Clone this project:
```bash
git clone https://github.com/red-bean-pasta/houspider.git
cd houspider
```

3. Build the example Houdini file:
```bash
hython scripts/build_test_hip.py
```
The model is then output to `test/test.hip`.


## Examples and topology views

Different parameter values can produce noticeably different body proportions and leg arrangements:

![Spider variant 1](docs/images/variant_example1.png)
![Spider variant 2](docs/images/variant_example2.png)

Wireframe views of the generated low-poly topology:

![Top perspective wireframe](docs/images/top_perspective_wireframe.png)
![Bottom perspective wireframe](docs/images/bottom_perspective_wireframe.png)
![Top wireframe](docs/images/top_wireframe.png)
![Bottom wireframe](docs/images/bottom_wireframe.png)


## Current limitations and TODOs

- Improve the layout of the control-handle parameters.
- Add a complete subdivision workflow; the authored topology is currently low-poly.
- Add support loops for leg coxas.
- Add eyeballs.
- Add flexing leg support. Legs are segmented and include membranes, but currently extend directly from the body.
- Add leg-segment section variance. Segments currently behave like tubes; the membrane workflow needs narrower ends that grow toward thicker sections.


## Parameter reference

The complete handle set is generated in Houdini from the builder modules. The controls below are the most useful ones for shaping the model.

### Sternum & Base

| Parameter | Default | Description |
| --- | ---: | --- |
| `front_back_length_ratios` | `(1.85, 1.6)` | Anterior and posterior sternum lengths relative to sternum half-width. |
| `spine_depth_ratio` | `0.25` | Maximum center-spine depression relative to sternum half-width. |
| `coxa_flap_extension_ratio` | `1.63` | Outward coxa-flap reach relative to sternum rim-edge length. |
| `coxa_flap_rise_angle` | `12` | Coxa-flap rise angle in degrees. |

### Dorsal

| Parameter | Default | Description |
| --- | ---: | --- |
| `height_ratio` | `0.375` | Dorsal top height relative to the base-to-chelicerae span. |
| `top_width_length_ratios` | `(1.0, 0.4)` | Dorsal top width and front-to-back length/flatness. |
| `top_face_offset_ratio` | `0.0` | Lengthwise offset of the top face. |
| `top_support_loop_ratios` | `(0.2, 0.5)` | Forward and rear placement of the top support loop. Larger values make the dorsal rounder. |
| `chelicerae_height_ratio` | `0.35` | Height of the upper chelicerae line relative to the base. |
| `lip_extrusion_ratio` | `(5.0, 1.0)` | Lengthwise and vertical lip extrusion. |

### Abdomen

| Parameter | Default | Description |
| --- | ---: | --- |
| `size_ratios` | `(1.2, 1.0, 1.2)` | Abdomen width, height, and length relative to the prosoma. |
| `width_hold_ratios` | `(0.1, 0.6)` | Start and end of the constant-width region along the abdomen. |
| `end_size_ratio` | `0.2` | Terminal abdomen width and height relative to its maximum size. This represents the spinnet. |

### Pedicel

| Parameter | Default | Description |
| --- | ---: | --- |
| `pedicel_opening_ratios` | `(0.5, 0.5)` | Controls the side/upper opening proportion and the lower opening position of the pedicel. |

### Chelicerae

| Parameter | Default | Description |
| --- | ---: | --- |
| `end_section_ratio` | `(0.25, 0.25)` | End-section width and height relative to the start section. |
| `end_section_offset` | `(0.2, 3.15, 1.25)` | End-section offset in local width, height, and length directions. |
| `end_section_rotation` | `(-90.0, 0.0)` | End-section rotation in the two local rotation directions. |
| `middle_section_ratio` | `(1.0, 1.2)` | Middle-section width and height relative to the start section. |
| `middle_section_offset` | `(0.1, 2.25)` | Middle-section offset in the local width and length directions. |
| `middle_section_height_ratio` | `0.4` | Middle-section height between the start and end sections. |

### Legs: basic and main legs

| Parameter | Default | Description |
| --- | ---: | --- |
| `coxa_length_ratio` | `1.2` | Front coxa length relative to the front socket width. |
| `segment_length_ratios` | `(0.33, 1.5, 0.9, 1.2, 1, 0.7)` | Length of each post-coxa front-leg segment relative to front coxa length. |
| `min_flex_angles` | `(180, 200, 30, 95, 150, 170)` | Minimum flex angle for each post-coxa segment joint. |
| `max_flex_angles` | `(180, 270, 160, 190, 178, 190)` | Maximum flex angle for each post-coxa segment joint. |
| `min_yaw_angles` | `(0, 0, 0, 0, 0, 0)` | Minimum yaw angle for each post-coxa segment joint. |
| `max_yaw_angles` | `(25, 0, 0, 0, 0, 20)` | Maximum yaw angle for each post-coxa segment joint. |
| `rest_flex_ratios` | `(0.5, 0.5, 0.5, 0.5, 0.5, 0.75, 0.5)` | Rest flex interpolation ratio between min and max flex angles for each joint (0=min, 1=max). |
| `leg_width_ratios` | `(0.8, 0.7, 0.8)` | Coxa-width scale for legs 2–4 relative to the front coxa. |
| `leg_length_ratios` | `(0.88, 0.9, 1.1)` | Coxa-length scale for legs 2–4 relative to the front coxa. |
| `*_sections` | MultiParm Vector3 | Cross-sections `(length_ratio, width_ratio, height_ratio)` for each segment under the "Segments" folder. |

### Pedipalp

| Parameter | Default | Description |
| --- | ---: | --- |
| `coxa_length` | `0.8` | Pedipalp coxa length relative to the front-leg coxa length. |
| `segment_length_ratios` | `(0.17, 0.8, 0.4, 0.45, 0.4)` | Length of each post-coxa pedipalp segment relative to pedipalp coxa length. |
| `endite_length_ratio` | `0.95` | Endite extension from its membrane attachment toward the coxa. |


## Acknowledgements

This project is manually directed, reviewed, structured, and tested at the method level. AI assists with implementation within that process.
