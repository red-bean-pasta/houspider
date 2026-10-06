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
  Use or generalize reusable utility scripts under `scripts/` (see [`scripts/README.md`](scripts/README.md)). This helps user flag commands as auto-approvable.
  If the command is unlikely to be reused again, use inline methods and ask for approval.
  If the script expects reuse only within the current task, harbor it at `.aiassistant/tmp/`.
  Analyze invoked commands and generalize reusable scripts at the end of each turn.

- **Core Verification Workflow**:
  ```shell
  # Regenerate test HIP at conclusion of geometry edits:
  hython scripts/build_test_hip.py

  # Validate node cooking across scene (or specify --root):
  hython scripts/cook_and_check.py test/test.hip
  ```

- **Inspection & Debugging Utilities**:
  Refer to [`scripts/README.md`](scripts/README.md) for full usage and examples of dedicated CLI tools:
  - `inspect_geo.py`: Query points/primitives and attributes with filtering.
  - `diff_geo.py`: Stage & node diffing (point displacements, added/removed elements, attribute changes).
  - `measure_geo.py`: Distances, vectors, elevation to XZ plane, and edge perpendicularity / angles.
  - `run_stage.py`: Isolated geometry stage testing against an input node.
  - `inspect_symbol.py`: HOM and project symbol source and docstring introspection.

---

## 6. Git & Commit Guidelines

- **Commit Messages**: Clear, concise, and descriptive one-liners following conventional commit style (`feat:`, `fix:`, `refactor:`, `chore:`, etc.), consistent with recent project history (`git log -n 10 --oneline`).
- **Atomic Commits**: Creating multiple focused commits is encouraged when it improves change tracking.
- **Pre-commit Inspection**:
  ```shell
  git status --short && echo && git --no-pager diff && echo && git --no-pager log -n 10 --oneline
  ```
- **Truth Source**: Treat `git diff` as the ultimate source of truth. Avoid running unrelated git exploration commands.
