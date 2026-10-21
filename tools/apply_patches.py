"""Applies the Dice Rush Extended patches to the original (decompiled) game scripts.

For every original script X.gd that has a folder src/patches/X/ :
  * every *.gd file in that folder contains top-level blocks (func / var / const / signal).
    A func/var/const with the same name as in the original replaces it, otherwise it is added
    (funcs at the end, vars/consts after the original declarations).
  * lines "#@delete <name>" remove the original top-level block with that name.
  * edits.py (optional) defines EDITS = [(old, new), ...] exact text replacements that must
    match exactly once (applied after the block replacements).
The result is written to src/game/scripts/X.gd (that folder is generated - never edit it by hand).
"""
import importlib.util, os, re, sys
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

ORIG = os.path.join(REPO, "work", "recovered", "scripts")
PATCHES = os.path.join(REPO, "src", "patches")
OUT = os.path.join(REPO, "src", "game", "scripts")

BLOCK_RE = re.compile(r'^(static func|func|static var|var|const|signal|@onready var|enum)\s+(\w+)')


def split_blocks(text):
    lines = text.split("\n")
    blocks = []
    current = None
    pending_annotations = []
    for line in lines:
        match = BLOCK_RE.match(line)
        if match:
            if current:
                blocks.append(current)
            kind = match.group(1)
            kind = {"static func": "func", "@onready var": "var", "static var": "var"}.get(kind, kind)
            current = [kind, match.group(2), pending_annotations + [line]]
            pending_annotations = []
        elif line.startswith("@") and not line.startswith("@tool") and current is not None and current[0] != "header":
            # annotation that belongs to the next declaration
            pending_annotations.append(line)
        else:
            if pending_annotations:
                current[2].extend(pending_annotations)
                pending_annotations = []
            if current is None:
                current = ["header", "", [line]]
            else:
                current[2].append(line)
    if pending_annotations and current:
        current[2].extend(pending_annotations)
    if current:
        blocks.append(current)
    return blocks


def join_blocks(blocks):
    parts = []
    for _kind, _name, lines in blocks:
        parts.append("\n".join(lines).rstrip("\n"))
    return "\n\n\n".join(parts) + "\n"


def apply_script(name):
    orig_path = os.path.join(ORIG, name + ".gd")
    patch_dir = os.path.join(PATCHES, name)
    text = open(orig_path, encoding="utf-8").read().replace("\r\n", "\n")
    blocks = split_blocks(text)
    index = {}
    for i, (kind, bname, _lines) in enumerate(blocks):
        index[(kind if kind == "func" else "decl", bname)] = i
    deletions = set()
    new_funcs = []
    new_decls = []
    replaced = 0
    for file_name in sorted(os.listdir(patch_dir)):
        if not file_name.endswith(".gd"):
            continue
        patch_text = open(os.path.join(patch_dir, file_name), encoding="utf-8").read().replace("\r\n", "\n")
        for line in patch_text.split("\n"):
            if line.startswith("#@delete "):
                for target in line[len("#@delete "):].split():
                    deletions.add(target.strip())
        for kind, bname, lines in split_blocks(patch_text):
            if kind == "header":
                continue
            key = (kind if kind == "func" else "decl", bname)
            # strip trailing blank lines of the block
            while lines and not lines[-1].strip():
                lines.pop()
            if key in index:
                blocks[index[key]] = [kind, bname, lines]
                replaced += 1
            elif kind == "func":
                new_funcs.append([kind, bname, lines])
            else:
                new_decls.append([kind, bname, lines])
    # deletions
    result = []
    for block in blocks:
        if block[0] != "header" and block[1] in deletions:
            continue
        result.append(block)
    # insert new declarations after the last top-level declaration that precedes the first func
    first_func = next((i for i, b in enumerate(result) if b[0] == "func"), len(result))
    result[first_func:first_func] = new_decls
    result.extend(new_funcs)
    out_text = join_blocks(result)
    edits_path = os.path.join(patch_dir, "edits.py")
    if os.path.exists(edits_path):
        spec = importlib.util.spec_from_file_location("edits_" + name, edits_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for number, (old, new) in enumerate(module.EDITS):
            count = out_text.count(old)
            if count != 1:
                raise SystemExit("%s edits[%d]: expected 1 match, found %d:\n%s" % (name, number, count, old[:300]))
            out_text = out_text.replace(old, new)
        for old, new in getattr(module, "GLOBAL_EDITS", []):
            out_text = out_text.replace(old, new)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".gd"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(out_text)
    return replaced, len(new_funcs), len(new_decls), len(deletions)


def main():
    if os.path.isdir(OUT):
        for file_name in os.listdir(OUT):
            if file_name.endswith(".gd"):
                os.remove(os.path.join(OUT, file_name))
    for name in sorted(os.listdir(PATCHES)):
        if os.path.isdir(os.path.join(PATCHES, name)):
            stats = apply_script(name)
            print("patched %-28s replaced=%d new_funcs=%d new_decls=%d deleted=%d" % ((name,) + stats))


if __name__ == "__main__":
    main()
