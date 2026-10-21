"""Checks the translation files of Dice Rush Extended against en.json.

usage:  python check_translations.py [code ...]      (no codes = all files)
Checks: valid JSON, same keys as en.json, same {placeholders}, "$" kept, no empty values.
Exit code 1 when a problem was found.
"""
import json, os, re, sys
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

ROOT = os.path.join(REPO, "src", "bdr", "i18n")
PLACEHOLDER = re.compile(r"\{[a-z_]+\}")


def check(code, en):
    path = os.path.join(ROOT, code + ".json")
    problems = []
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as error:
        return ["cannot read %s: %s" % (path, error)]
    missing = sorted(set(en) - set(data))
    extra = sorted(set(data) - set(en))
    if missing:
        problems.append("missing keys (%d): %s" % (len(missing), ", ".join(missing[:12])))
    if extra:
        problems.append("unknown keys (%d): %s" % (len(extra), ", ".join(extra[:12])))
    for key, source in en.items():
        if key not in data:
            continue
        value = data[key]
        if not isinstance(value, str) or not value.strip():
            problems.append("empty value: %s" % key)
            continue
        if sorted(PLACEHOLDER.findall(source)) != sorted(PLACEHOLDER.findall(value)):
            problems.append("placeholders differ in %s: %s -> %s" % (key, PLACEHOLDER.findall(source), PLACEHOLDER.findall(value)))
        if source.count("$") != value.count("$"):
            problems.append("'$' count differs in %s" % key)
    return problems


def main():
    en = json.load(open(os.path.join(ROOT, "en.json"), encoding="utf-8"))
    codes = sys.argv[1:] or sorted(f[:-5] for f in os.listdir(ROOT) if f.endswith(".json") and f not in ("en.json",))
    failed = False
    for code in codes:
        problems = check(code, en)
        if problems:
            failed = True
            print("%s: %d problem(s)" % (code, len(problems)))
            for problem in problems[:40]:
                print("   ", problem)
        else:
            print("%s: OK" % code)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
