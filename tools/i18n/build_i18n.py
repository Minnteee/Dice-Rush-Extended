"""Builds src/bdr/i18n/en.json and de.json from strings.py (+ every strings_*.py module)
and the dice catalog. Other languages: src/bdr/i18n/<code>.json produced by translation,
missing keys fall back to English at runtime."""
import glob, importlib.util, json, os
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(REPO, "src", "bdr", "i18n")
CATALOG = os.path.join(REPO, "src", "bdr", "data", "dice_catalog.json")


def collect():
    merged = {}
    for path in sorted(glob.glob(os.path.join(HERE, "strings*.py"))):
        spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for key, value in module.S.items():
            if key in merged:
                raise SystemExit("duplicate key " + key)
            merged[key] = value
    catalog = json.load(open(CATALOG, encoding="utf-8"))["dice"]
    for entry in catalog:
        merged["dice.%s.name" % entry["id"]] = (entry["name"]["en"], entry["name"]["de"])
        merged["dice.%s.desc" % entry["id"]] = (entry["desc"]["en"], entry["desc"]["de"])
    return merged


def main():
    merged = collect()
    os.makedirs(OUT, exist_ok=True)
    for index, code in ((0, "en"), (1, "de")):
        data = {key: value[index] for key, value in merged.items()}
        with open(os.path.join(OUT, code + ".json"), "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=1, sort_keys=True)
    print("i18n keys:", len(merged))


if __name__ == "__main__":
    main()
