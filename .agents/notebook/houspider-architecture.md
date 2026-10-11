# Houspider Project Architecture & Tooling

## Technical Findings

- **Houdini Environment**:
  - Python API: `hou`
  - Python Executable: `hython`
  - Documentation command: Search with `hhelp search "<term>"` and read with `hhelp textify -o <file> <path>` (see `hhelp-cli.md`). Raw `hhelp html` outputs unrendered HTML boilerplate.
- **Node Network**:
  - Primary network scope lives under `.../models/spider/generator/`.
  - Node generation avoids hardcoded Python/VEX SOPs, instead relying on `sopify` and `sopify_chain` from `houkit.noder` and `houspider.helper`.
- **Attribute Conventions**:
  - Point and primitive attributes link geometric components to spider biological features.
  - Enumerations defined via `StrEnum` across component modules (e.g. `attributes.py`).
  - Temporary attributes use prefix `tmp_`.
- **Verification Workflow**:
  - Build script: `hython scripts/build_test_hip.py` generates `test/test.hip`.
  - HIP validation cooks all nodes under `/obj` to ensure zero cook errors.
