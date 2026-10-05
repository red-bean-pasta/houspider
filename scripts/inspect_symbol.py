#!/usr/bin/env python
"""Inspects symbols, docstrings, and source code across hou, houkit, and houspider."""

import argparse
import importlib
import inspect
import sys


def resolve_symbol(path: str):
    parts = path.split(".")
    # Progressively find longest importable module
    for i in range(len(parts), 0, -1):
        mod_name = ".".join(parts[:i])
        try:
            obj = importlib.import_module(mod_name)
            for attr in parts[i:]:
                obj = getattr(obj, attr)
            return obj
        except (ImportError, AttributeError):
            continue
    return None


def inspect_symbol(path: str, show_source: bool = False, filter_str: str | None = None) -> None:
    obj = resolve_symbol(path)
    if obj is None:
        print(f"Error: Could not resolve symbol '{path}'")
        sys.exit(1)

    print(f"Symbol: {path}")
    print(f"Type: {type(obj)}")

    if show_source:
        try:
            print("\n--- Source Code ---")
            print(inspect.getsource(obj))
        except (TypeError, OSError) as exc:
            print(f"Could not retrieve source: {exc}")
        return

    doc = inspect.getdoc(obj)
    if doc:
        print(f"\nDocstring:\n{doc}\n")

    attrs = dir(obj)
    if filter_str:
        attrs = [a for a in attrs if filter_str.lower() in a.lower()]
    print(f"Attributes / Members ({len(attrs)}):")
    for a in attrs:
        print(f"  {a}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Python and HOM symbols.")
    parser.add_argument("symbol_path", help="Fully qualified symbol path (e.g. hou.Geometry, houkit.noder.sopify)")
    parser.add_argument("--source", action="store_true", help="Display full source code if available")
    parser.add_argument("--filter", dest="filter_str", help="Filter members by substring")
    args = parser.parse_args()

    inspect_symbol(args.symbol_path, args.source, args.filter_str)


if __name__ == "__main__":
    main()
