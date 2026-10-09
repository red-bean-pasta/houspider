# Promoted Multiparm Synchronization in Houdini

## Problem
In Houdini, when spare parameters are promoted from a child subnet (e.g. `/obj/spider/geometry/legs`) up to a parent container (e.g. `/obj/spider`), channel references (`ch(...)`) are initially linked.
However, when a **multiparm block** count is increased on the parent:
1. The parent creates new instances (`parm3x`, `parm3y`, `parm3z`).
2. The child count expression evaluates the new count and Houdini expands the child multiparm.
3. **Limitation**: Houdini does *not* automatically generate expressions on the child node's newly spawned instances.
4. The newly spawned child parameters remain unlinked, stuck at their template default values.

## Solution Patterns
1. **Upstream Linking via houkit (Architectural Fix)**:
   The fix belongs in `houkit.parameterizer` (`promote_parms_from`) rather than downstream consumers:
   - **`opmultiparm` (HScript command)**: Run `opmultiparm <child_node> "<parm#>" "<driving_node_parm#>"` during promotion. This registers persistent pattern links (`#`) across instances natively in Houdini, causing Houdini to automatically populate and maintain channel references when instances are added or removed.
   - **`setDefaultExpression` on Child ParmTemplate**: Update the child's parameter template inside the multiparm block so that its default expression points to `ch("<parent_parm>#")`. Newly spawned instances will automatically evaluate the parent parameter.
2. **Template Default Tuning**:
   Set multiparm instance default values (e.g. position `0.5` instead of `0.0`) to avoid duplicate key validation collisions upon creation before values are adjusted.
3. **Reader Following the Driving Channel (Hack / Anti-pattern)**:
   Avoid having consumers inspect raw expressions to chase parent nodes; this introduces leaky abstractions into procedural SOP code.

## Implementation Details
- `houkit.parameterizings.promoter`:
  - When cloning multiparm blocks during parameter promotion, recursively traverse sub-templates to pair each child parameter pattern with the corresponding parent parameter pattern.
  - Multi-component parameters (e.g. `XYZW`, `RGBA`, `Base1`) require separate component pairs in `opmultiparm` (e.g. `"section#x" "../../parent_section#x"`), because `opmultiparm` operates on individual channel names.
  - In HScript, parameter names containing `#` must be double-quoted to prevent `#` being interpreted as a comment marker.
  - `opmultiparm` works with relative paths (e.g. `../../target_parm#`), preserving portable subnet structures.
  - Suffix lookup is based on `tmpl.namingScheme()` and `tmpl.numComponents()`.

