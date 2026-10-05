# Repository Guidelines: houspider

## 1. Domain & Architecture

- **Project Purpose**: Procedural modeling of a biologically justifiable spider inside Houdini using the Houdini Object Model (HOM) in Python.
- **Houdini Environment**:
  - Python API module: `hou`.
  - Houdini Python executable: `hython`.
  - Documentation queries: Use `hhelp` directly instead of manually inspecting Python library sources (e.g., `hhelp html /nodes/sop/kinefx--capturepackedgeo.html`; `hhelp html` is valid syntax).
- **Network Scope**: The primary node hierarchy is under `.../models/spider/generator/`. Do not inspect upwards in the node graph unless explicitly required.
- **SOP Design**:
  - Build small, modular SOP nodes breaking complex geometry generation into clear sequential steps rather than monolithic nodes.
  - Avoid hardcoded Python or VEX SOPs. Always generate/wrap geometry operations using `sopify` / `sopify_chain` (from `houkit.noder` or `houspider.helper`).

---

## 2. Houdini Attributes & Data Conventions

- **Attribute Mapping**: The project heavily relies on Houdini's point and primitive attribute system to link 3D model space to biological components.
- **Attribute Definitions**: Use `StrEnum` definitions (see `attributes.py` across modules) and typed wrappers to maintain refactorability.
- **Temporary Attributes**: Prefix intermediate or working attributes with `tmp_` (e.g., `tmp_dir`, `tmp_length`), and clean them up before finalizing the subnet output.

---

## 3. Code Conventions & Ordering

- **Method Ordering (Project Rule)**: Place helper and modular methods **after** the parent calling method. Higher positions represent higher-level conceptual entry points. If two parent methods share a common child helper, place that helper at the bottom of the script.
- **Code Layout & Formatting**: Use newlines primarily for logical grouping rather than viewport-width line breaks.
- **Variable Naming**: Short abbreviations are acceptable in compact modular methods provided they are accompanied by an inline comment clarifying the full name upon first appearance.
- **HOM Assertions**: HOM natively supports standard Python `assert`; use assertions directly to validate geometry invariants without defensive boilerplate.

---

## 4. Documentation & Output Format

- **No LaTeX Math**: Do not use LaTeX math formatting (`$...$` or `$$...$$`). PyCharm's Markdown renderer does not render LaTeX reliably. Use plain Markdown and code formatting.

---

## 5. Verification & Testing

- **Avoid Inline `hython -c`**:
  It's encouraged to use or generalize reusable utility scripts at `scripts/`. This helps user add commands as auto-approvable tools. 
  If the command is unlikely to be reused again, you can use in-line methods and ask for approval.

- **HIP Generation**:
  At the conclusion of geometry edits, regenerate the test HIP:
  ```shell
  hython scripts/build_test_hip.py
  ```

- **Node Cooking Validation**:
  Inspect and cook all nodes in `/obj` (or under a specific root) using `scripts/cook_and_check.py`:
  ```shell
  hython scripts/cook_and_check.py test/test.hip
  # Or cook under a specific root:
  hython scripts/cook_and_check.py test/test.hip --root /obj/spider/generator/prosoma
  ```
  *(Note: Cooking verification can be skipped if the task is deliberately left midway per user instruction.)*

- **Geometry & Attribute Inspection**:
  To inspect point/prim attributes, counts, or coordinates on a node without writing inline python:
  ```shell
  hython scripts/inspect_geo.py /obj/spider/generator/prosoma/base --attrib id --value "basesternum(5, 1)"
  hython scripts/inspect_geo.py /obj/spider/generator/prosoma/base --type prim --attrib region
  ```

- **Isolated Stage Testing**:
  To test an isolated geometry processing function directly against an input node:
  ```shell
  hython scripts/run_stage.py houspider.bases.geos.coxa:correct_coxa_shape /obj/spider/generator/prosoma/sternum
  ```

- **Symbol & Source Introspection**:
  To inspect docstrings, members, or source code across HOM (`hou`) and project modules:
  ```shell
  hython scripts/inspect_symbol.py hou.Geometry --filter point
  hython scripts/inspect_symbol.py houkit.noder.sopify --source
  ```

---

## 6. Git & Commit Guidelines

- **Commit Messages**: Clear, concise, and descriptive one-liners following conventional commit style (`feat:`, `fix:`, `refactor:`, `chore:`, etc.), consistent with recent project history (`git log -n 10 --oneline`).
- **Atomic Commits**: Creating multiple focused commits is encouraged when it improves change tracking.
- **Pre-commit Inspection**:
  ```shell
  git status --short && echo && git --no-pager diff && echo && git --no-pager log -n 10 --oneline
  ```
- **Truth Source**: Treat `git diff` as the ultimate source of truth. Avoid running unrelated git exploration commands.
