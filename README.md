# Houspider

A procedural spider model generator for SideFX Houdini. It exposes the most useful shape and topology controls as editable Houdini parameters. 

Adjust the parameters to explore different spider shapes. Enter `obj/spider/skeleton/animate_scene` and enable Animate View to pose the limbs.

This project wish to explore and experiment with fully procedural, code-driven organic modeling.

## How it works

The generator uses Houdini Python (Houdini Object Model) to create and connect the modeling network. It heavily relies on Houdini's attributing system to identify points and faces. It still builds in node networks to mkae inspection and debugging easy.

The project uses [`houkit`](https://github.com/red-bean-pasta/houkit) for reusable Houdini node, parameter, and attribute helpers.


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

![Side](docs/images/side_posed_wireframe.png)
![Top](docs/images/top_posed_wireframe.png)
![Bottom](docs/images/bottom_posed_wireframe.png)
![Posing](docs/images/pedipalp_ik_demo.webp)

## Current limitations and TODOs

- Add a complete subdivision workflow; it's currently low-poly.
- Add eyeballs.


## Parameter reference

These top-level parameters on `/obj/spider` let you shape the body, limbs, and poses without diving into node networks.

### Prosoma & Carapace (Head & Main Body)

| Parameter | Description |
| --- | --- |
| `Front / Back Length` | Length of the front and back of the main body. |
| `Top Height` | How tall the upper body is. |
| `Top Width / Length` | Width and length of the top surface. |
| `Chelicerae Height` | How high the fangs sit on the body. |

### Chelicerae (Fangs)

| Parameter | Description |
| --- | --- |
| `Middle Section Size & Offset` | Thickness and outward curve of the middle of the fangs. |
| `End Section Size & Offset` | Tip sharpness and how far down the fangs reach. |
| `End Section Rotation` | Inward and downward angle of the fangs. |

### Abdomen

| Parameter | Description |
| --- | --- |
| `Width / Height / Length` | Width, height, and length of the rear body. |
| `Constant Width Range` | How far the rear body stays wide before tapering. |

### Legs

| Parameter | Description |
| --- | --- |
| `Coxa Length` | How far the legs extend before the first joint. |
| `Segment Lengths` | Length of each leg segment. |
| `Other Leg Lengths & Widths` | Length and width of the middle and back legs relative to the front legs. |
| `Segment Profiles` | Thickness profile along each leg segment. |
| `Joint Limits` | Bending limits for each joint. |
| `Rest Flex Ratios` | How bent the legs are in their rest pose. |

### Pedipalps (Front Feelers)

| Parameter | Description |
| --- | --- |
| `Coxa & Segment Lengths` | Length of the front feelers. |
| `Endite Length & Surface Size` | Size of the mouth plates beside the fangs. |
| `Rest Flex Ratios` | How curled the front feelers are in their rest pose. |

> Fine-tuning details, like seam widths, junction tolerances, and internal clearance angles, are left off this list. Explore the full parameter set, including the **Advanced** controls, directly on `/obj/spider` in `test/test.hip`.

## Acknowledgements

This project is manually directed, reviewed, structured, and tested at the method level. AI assists with implementation within that process.
