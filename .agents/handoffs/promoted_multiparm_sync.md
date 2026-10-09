# Handoff: Promoted Multiparm Desynchronization on Femur Sections

## 1. Goal
Fix the duplicate section error (`ValueError: Duplicate section position detected at 0.00000`) when adding a new section to `femur` (or any leg segment) in Houdini. Ensure changes made to newly added multiparm sections on the parent node (`/obj/spider`) properly propagate down to the child subnet (`/obj/spider/geometry/legs`) automatically without leaking promotion details to the consumers.

## 2. Completed Phases & Observed Facts
- **Observed (Runtime & Houdini Behavior)**:
  - In `houspider/main.py`, `_propagate_parameters` calls `promote_subnets(spider_node, depth=None, dest_group="Build")`.
  - On `/obj/spider`, promoted parameters are created with prefixes, e.g. `geometry_legs_femur_sections`, `geometry_legs_femur_section1x`, etc.
  - On `/obj/spider/geometry/legs`, the child multiparm parameters initially have expressions pointing up to `/obj/spider`:
    - `femur_sections` -> `ch("../../geometry_legs_femur_sections")`
    - `femur_section1x` -> `ch("../../geometry_legs_femur_section1x")`
    - `femur_section2x` -> `ch("../../geometry_legs_femur_section2x")`
  - When the user clicks `+` on the top-level `/obj/spider` multiparm (increasing count to 3):
    - Houdini creates instances on `/obj/spider`: `geometry_legs_femur_section3x, y, z`.
    - The child count `legs.parm("femur_sections")` evaluates the expression to `3`, causing Houdini to expand the multiparm on `legs` as well.
    - **Crucial limitation in Houdini**: Houdini does *not* automatically generate channel expressions (`ch(...)`) on newly spawned child instances in a multiparm block.
    - Thus, `legs.parmTuple("femur_section3")` is created on `legs` with default value `(0.0, 1.0, 1.0)` and *no link* to `/obj/spider`.
  - When the user edits `geometry_legs_femur_section3x` to `0.5` on `/obj/spider`:
    - `/obj/spider` has `0.5`.
    - But `houspider.legs.attributes.get_segment_sections(parent)` evaluates parameters on `node.parent()` (`/obj/spider/geometry/legs`).
    - Because `legs.parmTuple("femur_section3")` is unlinked, it evaluates to `(0.0, 1.0, 1.0)`.
    - `LimbParam.__post_init__` receives `[(0.0, 1, 1), (1.0, 1, 1), (0.0, 1, 1)]`, sorts it to `[0.0, 0.0, 1.0]`, detects duplicate `0.00000`, and raises `ValueError`.

- **User-Stated Architectural Constraint**:
  - `get_segment_sections` in `houspider` is a hacky workaround, not a fix: it requires the leg build logic to be aware of parameter promotion.
  - The fix belongs strictly on the **`houkit`** side (`houkit.parameterizer` / `houkit.parameterizings.promoter`), so any multiparm promotion across subnets maintains link consistency without pushing responsibility to the consumer.

- **Observed / Researched Solutions in Houdini & SideFX Ecosystem**:
  1. **HScript `opmultiparm` (Official SideFX dynamic linking mechanism)**:
     - `opmultiparm <node> "<multiparm_parm#>" "<referenced_parm#>"` establishes dynamic linking using `#` tokens.
     - Can be called via `hou.hscript(f'opmultiparm {child.path()} "{child_parm}#" "{parent.path()}/{parent_parm}#"')`.
     - When either node adds or removes instances, Houdini maintains channel references automatically across all instances.
  2. **`setDefaultExpression` on child's parameter template with `#` token**:
     - Inside `FolderParmTemplate(folder_type=MultiparmBlock)`, child templates can have `setDefaultExpression((f'ch("{parent_path}/{parent_parm}#")', ...))`.
     - Whenever the child multiparm expands (due to the count parameter evaluating the parent expression), Houdini automatically initializes newly spawned child instances with that default expression, substituting `#` with the current instance index.

## 3. Failed / Rejected Approaches Worth Not Repeating
- **Modifying `houspider/legs/attributes.py` (`get_segment_sections`)**:
  - Rejected: Leaks promotion concerns into downstream procedural generators and violates single-responsibility principles.
- **Multiparm Callbacks on parent node**:
  - Disfavored: Callbacks only fire on GUI interactions in the parameter pane and do not trigger reliably during scripted batch builds, procedural parameter sets, or background cooks.

## 4. Next Concrete Action
1. Inspect and modify `promote_parms_from` / `_format_child_multiparm` in [`houkit/parameterizings/promoter.py`](file:///home/xuh/.local/lib/python3.13/site-packages/houkit/parameterizings/promoter.py):
   - Option A: When cloning and linking a multiparm block, invoke `opmultiparm` between `child` and `parent` for the parameter templates in the multiparm.
   - Option B: Update the child node's own multiparm templates via `child.parmTemplateGroup()` to set `setDefaultExpression` pointing to `ch(parent/prefix_#)`.
2. Also update the default value for `vec_template` in [`houspider/legs/build.py`](file:///home/xuh/Documents/git-him-back/houspider/houspider/legs/build.py#L170) from `(0.0, 1.0, 1.0)` to `(0.5, 1.0, 1.0)` so newly added section rows default to a sensible midpoint rather than colliding with `0.0`.
3. Verify by running:
   ```shell
   hython scripts/build_test_hip.py && hython scripts/cook_and_check.py test/test.hip
   ```
   and test adding multiparm instances on `/obj/spider` and verifying child evaluation.

## 5. Active Files
- [`houkit/parameterizings/promoter.py`](file:///home/xuh/.local/lib/python3.13/site-packages/houkit/parameterizings/promoter.py#L58-L167): Primary target where multiparm parameter promotion and channel linking should be fixed.
- [`houspider/legs/build.py`](file:///home/xuh/Documents/git-him-back/houspider/houspider/legs/build.py#L166-L188): Multiparm template definitions and default section values.
- [`houspider/main.py`](file:///home/xuh/Documents/git-him-back/houspider/houspider/main.py#L45-L51): Where `promote_subnets` is invoked on the spider hierarchy.
- [`houspider/segments/models.py`](file:///home/xuh/Documents/git-him-back/houspider/houspider/segments/models.py#L46-L65): Section normalization and duplicate position validation.
