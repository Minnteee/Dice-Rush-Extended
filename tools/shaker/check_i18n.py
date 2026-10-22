"""Checks the Dice Shaker translations against en.json.

For every language file in src/shaker/i18n: same keys as en.json, no empty texts, the same
{placeholders}, the same number of "$" (currency) signs and the same line breaks.

usage: python check_i18n.py [lang ...]      (no argument = all languages)
exit code 1 if anything is wrong.
"""
import json
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
I18N = os.path.join(REPO, "src", "shaker", "i18n")
LANGUAGES = ["ar", "bg", "cs", "da", "de", "el", "en", "es", "es_419", "fi", "fr", "hu", "id", "it", "ja", "ko", "ms",
             "nl", "no", "pl", "pt_BR", "pt_PT", "ro", "ru", "sv", "th", "tr", "uk", "vi", "zh_CN", "zh_TW"]
PLACEHOLDER = re.compile(r"\{[a-z0-9_]+\}")


def load(lang):
    with open(os.path.join(I18N, lang + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


def check(lang, en):
    problems = []
    path = os.path.join(I18N, lang + ".json")
    if not os.path.exists(path):
        return ["file missing"]
    try:
        data = load(lang)
    except Exception as error:  # noqa: BLE001
        return ["invalid json: %s" % error]
    for key in en:
        if key not in data:
            problems.append("missing key " + key)
            continue
        value = data[key]
        if not isinstance(value, str) or not value.strip():
            problems.append("empty " + key)
            continue
        if sorted(PLACEHOLDER.findall(value)) != sorted(PLACEHOLDER.findall(en[key])):
            problems.append("placeholders differ in %s: %r" % (key, value))
        if value.count("$") != en[key].count("$"):
            problems.append("currency sign count differs in %s: %r" % (key, value))
        if value.count("\n") != en[key].count("\n"):
            problems.append("line breaks differ in %s" % key)
    for key in data:
        if key not in en:
            problems.append("unknown key " + key)
    return problems


def main():
    en = load("en")
    langs = sys.argv[1:] or [lang for lang in LANGUAGES if lang != "en"]
    bad = 0
    for lang in langs:
        problems = check(lang, en)
        if problems:
            bad += 1
            print("%s: %d problem(s)" % (lang, len(problems)))
            for problem in problems[:25]:
                print("   ", problem)
        else:
            print("%s: ok" % lang)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
