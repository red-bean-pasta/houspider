#!/usr/bin/env python
"""Executes an isolated geometry processing function directly against a node's geometry."""

import argparse
import importlib
import sys
import hou


def run_stage(func_spec: str, node_path: str, hip_file: str = "test/test.hip") -> None:
    hou.hipFile.load(hip_file)
    node = hou.node(node_path)
    if node is None:
        print(f"Error: Node not found at path '{node_path}'")
        sys.exit(1)

    node.cook(force=True)
    geo = node.geometry().freeze()

    if ":" not in func_spec:
        print(f"Error: func_spec must be in 'module.path:function_name' format. Got: '{func_spec}'")
        sys.exit(1)

    mod_name, func_name = func_spec.split(":", 1)
    print(f"Importing {func_name} from {mod_name}...")
    mod = importlib.import_module(mod_name)
    func = getattr(mod, func_name)

    print(f"Executing {func_name}(geo) on geometry from {node_path} ({len(geo.points())} pts, {len(geo.prims())} prims)...")
    res = func(geo)

    result_geo = res if isinstance(res, hou.Geometry) else geo
    print(f"Function executed successfully.")
    print(f"Resulting geometry: {len(result_geo.points())} points, {len(result_geo.prims())} primitives.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an isolated geometry processing stage.")
    parser.add_argument("func_spec", help="Function spec in 'module.path:func_name' format")
    parser.add_argument("node_path", help="Path to input node supplying the initial geometry")
    parser.add_argument("--hip", default="test/test.hip", help="Path to .hip file (default: test/test.hip)")
    args = parser.parse_args()

    run_stage(args.func_spec, args.node_path, args.hip)


if __name__ == "__main__":
    main()
