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

- **HIP Generation & Cooking Check**:
  At the conclusion of geometry edits, regenerate the test HIP and verify that all nodes cook without errors:
  ```shell
  hython scripts/build_test_hip.py
  ```
- **Node Cooking Validation**:
  Inspect the generated `test/test.hip` by cooking all nodes in `/obj`:
  ```shell
  hython -c '
  import hou
  import sys

  hou.hipFile.load("test/test.hip")

  root = hou.node("/obj")
  if root is None:
      print("Node not found")
      sys.exit(1)

  for node in root.allSubChildren():
      print("Cooking:", node.path())
      try:
          node.cook(force=True)
      except hou.Error as exc:
          print("\nFAILED:", node.path())
          errors = node.errors()
          if errors:
              for err in errors:
                  print("  ERROR:", err)
          else:
              print("  ERROR:", exc)
          sys.exit(1)

  print("All nodes cooked successfully.")
  '
  ```
  *(Note: Cooking verification can be skipped if the task is deliberately left midway per user instruction.)*

---

## 6. Git & Commit Guidelines

- **Commit Messages**: Clear, concise, and descriptive one-liners following conventional commit style (`feat:`, `fix:`, `refactor:`, `chore:`, etc.), consistent with recent project history (`git log -n 10 --oneline`).
- **Atomic Commits**: Creating multiple focused commits is encouraged when it improves change tracking.
- **Pre-commit Inspection**:
  ```shell
  git status --short && echo && git --no-pager diff && echo && git --no-pager log -n 10 --oneline
  ```
- **Truth Source**: Treat `git diff` as the ultimate source of truth. Avoid running unrelated git exploration commands.
