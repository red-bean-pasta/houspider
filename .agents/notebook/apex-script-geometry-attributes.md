# APEX Script Geometry Attribute Access & Streamed Data

## Reading Geometry Detail Attributes in APEX Script

In APEX Script snippets (such as those compiled into `apex::autorigcomponent::3.0`), the character input is bound via:
```apex
character: Geometry = BindInput();
```

The underlying APEX callback for reading detail attributes is `geo::DetailAttribValue<T>`. In APEX Script syntax, typed methods are exposed directly on the `Geometry` object:
```apex
limits, success = character.detailAttribValue_Dict("joint_limits");
val, success = character.detailAttribValue_Float("my_float");
s, success = character.detailAttribValue_String("my_string");
```
When `success` is true, the value can be indexed directly (e.g. `limits["spider:leg:min_flex"]`).

## Packed Character Propagation Caveat

When building a character via `kinefx::packcharacter`:
1. It packages shapes and skeletons into separate embedded packed primitives (`Base.shp`, `Base.skel`).
2. It does **not** automatically copy detail attributes from the source geometry onto the packed container root primitive / detail dictionary.
3. Standard APEX autorig components (like `apex::autorigcomponent::3.0`) expect detail attributes to reside on the character geometry passed into their input port.

### Workaround / Pattern
To forward upstream detail attributes (such as `GlobalAttrib.JOINT_LIMITS`) into downstream APEX autorig components:
- Insert an `attribcopy` SOP between `packcharacter` and downstream components.
- Configure `attribcopy` with `class = 0` (Detail), `attribnames = "<attrib_name>"`, copying from the upstream source geometry (`indirectInputs()[0]`) onto the packed character output.
- Downstream APEX components preserve these detail attributes through their character input/output stream.

## APEX Script Language Quirk: Math Functions

- APEX Script is statically typed and does not provide Python's `math.radians()` or VEX's `radians()` as built-in functions.
- Angle conversions must be calculated explicitly:
  ```apex
  deg_to_rad: float = 0.017453292519943295;
  rad_val: float = deg_val * deg_to_rad;
  ```
