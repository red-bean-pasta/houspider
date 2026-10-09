#!/usr/bin/env python
"""Inspects parameters, values, and controls on a Houdini node in a HIP file."""

import argparse
import fnmatch
import sys
import hou


def inspect_parms(
    hip_file: str,
    node_path: str,
    pattern: str | None = None,
    only_modified: bool = False,
    tree: bool = False,
    ref_hip: str | None = None,
    ref_path: str | None = None,
    output_format: str = "table",
) -> None:
    if ref_hip or ref_path:
        _diff_parms(
            hip_file,
            node_path,
            ref_hip=ref_hip,
            ref_path=ref_path,
            pattern=pattern,
            output_format=output_format,
        )
        return

    hou.hipFile.load(hip_file)
    node = hou.node(node_path)
    if node is None:
        print(f"Error: Node not found at path '{node_path}'")
        sys.exit(1)

    if tree:
        _inspect_parms_tree(
            node,
            pattern=pattern,
            only_modified=only_modified,
            output_format=output_format,
        )
        return

    parm_tuples = node.parmTuples()
    print(f"Node: {node.path()} [{node.type().name()}] in {hip_file}")
    print(f"Total Parameters: {len(parm_tuples)}\n")

    matched = []
    for pt in parm_tuples:
        if not _matches_filter(pt, pattern, only_modified):
            continue
        try:
            is_default = pt.isAtDefault()
        except Exception:
            is_default = True
        matched.append((pt, is_default))

    if not matched:
        print("No matching parameters found.")
        return

    if output_format == "python":
        _print_python_format(matched)
    else:
        _print_table_format(matched)


def _diff_parms(
    hip_file: str,
    node_path: str,
    ref_hip: str | None = None,
    ref_path: str | None = None,
    pattern: str | None = None,
    output_format: str = "table",
) -> None:
    actual_ref_hip = ref_hip if ref_hip else hip_file
    actual_ref_path = ref_path if ref_path else node_path

    hou.hipFile.load(actual_ref_hip)
    ref_node = hou.node(actual_ref_path)
    if ref_node is None:
        print(f"Error: Reference node not found at '{actual_ref_path}' in '{actual_ref_hip}'")
        sys.exit(1)

    ref_parms = {}
    for pt in ref_node.parmTuples():
        ref_parms[pt.name()] = (pt.description(), _eval_parm_value(pt))

    hou.hipFile.load(hip_file)
    cur_node = hou.node(node_path)
    if cur_node is None:
        print(f"Error: Target node not found at '{node_path}' in '{hip_file}'")
        sys.exit(1)

    cur_parms = {}
    for pt in cur_node.parmTuples():
        cur_parms[pt.name()] = (pt.description(), _eval_parm_value(pt))

    all_keys = sorted(set(ref_parms.keys()) | set(cur_parms.keys()))
    diffs = []
    for k in all_keys:
        if pattern:
            desc = cur_parms.get(k, ref_parms.get(k))[0]
            if not (fnmatch.fnmatch(k, pattern) or fnmatch.fnmatch(desc, pattern)):
                continue

        ref_info = ref_parms.get(k)
        cur_info = cur_parms.get(k)

        if not ref_info:
            diffs.append((k, cur_info[0], "<Not present>", cur_info[1]))
        elif not cur_info:
            diffs.append((k, ref_info[0], ref_info[1], "<Not present>"))
        elif ref_info[1] != cur_info[1]:
            diffs.append((k, cur_info[0], ref_info[1], cur_info[1]))

    print(f"Comparing parameters:")
    print(f"  Reference (A): {actual_ref_path} [{actual_ref_hip}]")
    print(f"  Target    (B): {node_path} [{hip_file}]")
    print(f"Differing parameters: {len(diffs)}\n")

    if not diffs:
        print("All matching parameter values are identical.")
        return

    if output_format == "python":
        for name, _, _, val_cur in diffs:
            print(f"{name} = {repr(val_cur)}")
        return

    print(f"{'Parameter':<32} {'Label':<24} {'Ref Value':<28} {'Target Value':<28}")
    print("-" * 114)
    for name, label, v_ref, v_cur in diffs:
        str_ref = str(v_ref)
        str_cur = str(v_cur)
        print(f"{name:<32} {label:<24} {str_ref:<28} {str_cur:<28}")


def _inspect_parms_tree(
    node: hou.OpNode,
    pattern: str | None = None,
    only_modified: bool = False,
    output_format: str = "table",
) -> None:
    ptg = node.parmTemplateGroup()

    def process_folder(folder_entry: hou.FolderParmTemplate, depth: int = 0) -> list[str]:
        lines = []
        is_mp = folder_entry.folderType() == hou.folderType.MultiparmBlock
        if is_mp:
            count_parm = node.parm(folder_entry.name())
            count = count_parm.eval() if count_parm else 0
            mp_lines = []
            for i in range(count):
                for sub in folder_entry.parmTemplates():
                    inst_name = sub.name().replace("#", str(i + 1))
                    pt = node.parmTuple(inst_name)
                    if pt and _matches_filter(pt, pattern, only_modified):
                        val = _eval_parm_value(pt)
                        def_str = "yes" if pt.isAtDefault() else "MODIFIED"
                        indent = "  " * (depth + 1)
                        if output_format == "python":
                            mp_lines.append(f"{indent}{inst_name} = {repr(val)}")
                        else:
                            mp_lines.append(f"{indent}- {inst_name} ({pt.description()}): {val} [{def_str}]")
            if mp_lines or not (pattern or only_modified):
                indent = "  " * depth
                lines.append(f"{indent}[Multiparm] {folder_entry.label()} (count: {count})")
                lines.extend(mp_lines)
        else:
            child_lines = []
            for entry in folder_entry.parmTemplates():
                if isinstance(entry, hou.FolderParmTemplate):
                    child_lines.extend(process_folder(entry, depth + 1))
                else:
                    pt = node.parmTuple(entry.name())
                    if pt and _matches_filter(pt, pattern, only_modified):
                        val = _eval_parm_value(pt)
                        def_str = "yes" if pt.isAtDefault() else "MODIFIED"
                        indent = "  " * (depth + 1)
                        if output_format == "python":
                            child_lines.append(f"{indent}{pt.name()} = {repr(val)}")
                        else:
                            child_lines.append(f"{indent}- {pt.name()} ({pt.description()}): {val} [{def_str}]")
            if child_lines:
                indent = "  " * depth
                lines.append(f"{indent}[Folder] {folder_entry.label()}")
                lines.extend(child_lines)
        return lines

    all_lines = []
    for entry in ptg.entries():
        if isinstance(entry, hou.FolderParmTemplate):
            all_lines.extend(process_folder(entry, depth=0))
        else:
            pt = node.parmTuple(entry.name())
            if pt and _matches_filter(pt, pattern, only_modified):
                val = _eval_parm_value(pt)
                def_str = "yes" if pt.isAtDefault() else "MODIFIED"
                if output_format == "python":
                    all_lines.append(f"{pt.name()} = {repr(val)}")
                else:
                    all_lines.append(f"- {pt.name()} ({pt.description()}): {val} [{def_str}]")

    print(f"Node Hierarchy: {node.path()} [{node.type().name()}]\n")
    if not all_lines:
        print("No matching parameters found.")
        return

    for line in all_lines:
        print(line)


def _matches_filter(pt: hou.ParmTuple, pattern: str | None, only_modified: bool) -> bool:
    if pattern:
        name_match = fnmatch.fnmatch(pt.name(), pattern)
        label_match = fnmatch.fnmatch(pt.description(), pattern)
        if not (name_match or label_match):
            return False
    if only_modified:
        try:
            if pt.isAtDefault():
                return False
        except Exception:
            return False
    return True


def _eval_parm_value(pt: hou.ParmTuple) -> object:
    try:
        val = pt.eval()
        if len(pt) == 1:
            return val[0]
        return tuple(val)
    except Exception as exc:
        return f"<Error: {exc}>"


def _print_table_format(matched: list[tuple[hou.ParmTuple, bool]]) -> None:
    print(f"{'Parameter':<28} {'Label':<26} {'Value':<30} {'Default?'}")
    print("-" * 92)
    for pt, is_default in matched:
        name = pt.name()
        label = pt.description()
        val = _eval_parm_value(pt)
        default_str = "yes" if is_default else "MODIFIED"
        print(f"{name:<28} {label:<26} {str(val):<30} {default_str}")


def _print_python_format(matched: list[tuple[hou.ParmTuple, bool]]) -> None:
    for pt, _ in matched:
        val = _eval_parm_value(pt)
        print(f"{pt.name()} = {repr(val)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect node parameters in a Houdini HIP file.")
    parser.add_argument("node_path", help="Path to node (e.g. /obj/spider/geometry/legs/CONTROL)")
    parser.add_argument("hip_file", nargs="?", default="test/test.hip", help="Path to .hip file (default: test/test.hip)")
    parser.add_argument("-p", "--pattern", help="Filter parameter names or labels by glob (e.g. '*wedge*', '*ratio*')")
    parser.add_argument("-m", "--modified", action="store_true", help="Only show parameters modified from their defaults")
    parser.add_argument("-t", "--tree", action="store_true", help="Display parameters grouped by folder and multiparm hierarchy")
    parser.add_argument("--ref-hip", help="Reference HIP file path for cross-HIP parameter comparison")
    parser.add_argument("--ref", help="Reference node path (defaults to target node_path if --ref-hip is set)")
    parser.add_argument("-f", "--format", choices=["table", "python"], default="table", help="Output format (default: table)")
    args = parser.parse_args()

    inspect_parms(
        args.hip_file,
        args.node_path,
        pattern=args.pattern,
        only_modified=args.modified,
        tree=args.tree,
        ref_hip=args.ref_hip,
        ref_path=args.ref,
        output_format=args.format,
    )


if __name__ == "__main__":
    main()
