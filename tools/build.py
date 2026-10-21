"""Dice Rush Extended build tool.

Collects the mod sources, writes remap files for modified vanilla scripts,
packs everything into DiceRushExtended.pck with the game's own engine
(PCKPacker) and prepares an installable dist folder.

usage: python build.py [--release] [--install-test] [--install-game]
"""
import json, os, shutil, subprocess, sys, time
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

ROOT = REPO
SRC = os.path.join(ROOT, "src")
GEN = os.path.join(ROOT, "build", "generated")
DIST = os.path.join(ROOT, "dist")
PACKER_DIR = os.path.join(ROOT, "tools", "packer")
TESTGAME = os.path.join(ROOT, "testgame")


def _game_dir():
    """The DICE RUSH game folder for --install-game: environment variable DICE_RUSH_DIR or the
    file tools/local_paths.json ({"game_dir": "C:/.../DICE RUSH"}, not part of the repository)."""
    if os.environ.get("DICE_RUSH_DIR"):
        return os.environ["DICE_RUSH_DIR"]
    local = os.path.join(ROOT, "tools", "local_paths.json")
    if os.path.exists(local):
        return json.load(open(local, encoding="utf-8")).get("game_dir", "")
    return ""


GAME = _game_dir()

SKIP_EXT = {".import", ".uid", ".tmp", ".bak", ".pyc", ".md"}
# review images of the art generator - not used by the game
SKIP_NAMES = {"contact_sheet.png"}


def collect():
    files = []  # (res_path, abs_source)
    # modified vanilla files
    game_dir = os.path.join(SRC, "game")
    remaps = []
    for base, _dirs, names in os.walk(game_dir):
        for name in names:
            if os.path.splitext(name)[1] in SKIP_EXT:
                continue
            abs_path = os.path.join(base, name)
            rel = os.path.relpath(abs_path, game_dir).replace("\\", "/")
            files.append(("res://" + rel, abs_path))
            if rel.endswith(".gd"):
                remaps.append(rel)
    # new mod files (hand written + generated)
    for root_dir in (os.path.join(SRC, "bdr"), os.path.join(GEN, "bdr")):
        if not os.path.isdir(root_dir):
            continue
        for base, _dirs, names in os.walk(root_dir):
            for name in names:
                if os.path.splitext(name)[1] in SKIP_EXT or name in SKIP_NAMES:
                    continue
                abs_path = os.path.join(base, name)
                rel = os.path.relpath(abs_path, root_dir).replace("\\", "/")
                files.append(("res://bdr/" + rel, abs_path))
    # remaps so that res://scripts/x.gd points at our text script instead of the original .gdc
    remap_dir = os.path.join(ROOT, "build", "remaps")
    if os.path.isdir(remap_dir):
        shutil.rmtree(remap_dir)
    for rel in remaps:
        target = os.path.join(remap_dir, rel.replace("/", os.sep) + ".remap")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write('[remap]\n\npath="res://%s"\n' % rel)
        files.append(("res://" + rel + ".remap", target))
    return files


def pack(files, output):
    manifest = {"output": output.replace("\\", "/"), "files": [[res, src.replace("\\", "/")] for res, src in files]}
    manifest_path = os.path.join(ROOT, "build", "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=1)
    if os.path.exists(output):
        os.remove(output)
    exe = os.path.join(PACKER_DIR, "Dice Rush.exe")
    started = time.time()
    proc = subprocess.run([exe, "--headless", "--", "--manifest=" + manifest_path.replace("\\", "/")],
                          cwd=PACKER_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    log = proc.stdout + proc.stderr
    if "BDR_PACK_DONE" not in log or proc.returncode != 0 or not os.path.exists(output):
        print(log)
        raise SystemExit("packing failed (exit %s)" % proc.returncode)
    print("packed %d files -> %s (%.1f KB, %.1fs)" % (len(files), output, os.path.getsize(output) / 1024, time.time() - started))


def make_dist():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "DiceRushExtended"))
    shutil.copy2(os.path.join(SRC, "loader", "override.cfg"), os.path.join(DIST, "override.cfg"))
    shutil.copy2(os.path.join(SRC, "loader", "boot.gd"), os.path.join(DIST, "DiceRushExtended", "boot.gd"))
    for extra in ("README.txt", "INSTALL.txt", "UNINSTALL.bat"):
        p = os.path.join(SRC, "loader", extra)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(DIST, extra))
    return os.path.join(DIST, "DiceRushExtended", "DiceRushExtended.pck")


OLD_NAMES = ("BetherDiceRush", "Bether Dice Rush deinstallieren.bat")   # first version of the mod
UNINSTALL_NAME = "Uninstall Dice Rush Extended.bat"


def install(target, test=False):
    # remove the files of the first version (it was called "Bether Dice Rush")
    for old in OLD_NAMES:
        old_path = os.path.join(target, old)
        if os.path.isdir(old_path):
            shutil.rmtree(old_path)
        elif os.path.isfile(old_path):
            os.remove(old_path)
    os.makedirs(os.path.join(target, "DiceRushExtended"), exist_ok=True)
    for name in ("boot.gd", "DiceRushExtended.pck"):
        shutil.copy2(os.path.join(DIST, "DiceRushExtended", name), os.path.join(target, "DiceRushExtended", name))
    if test:
        harness = os.path.join(SRC, "testing", "bdr_test_harness.gd")
        if os.path.exists(harness):
            shutil.copy2(harness, os.path.join(target, "bdr_test_harness.gd"))
        cfg = open(os.path.join(SRC, "testing", "override_test.cfg"), encoding="utf-8").read()
        with open(os.path.join(target, "override.cfg"), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(cfg)
    else:
        shutil.copy2(os.path.join(DIST, "override.cfg"), os.path.join(target, "override.cfg"))
        for name, destination in (("README.txt", os.path.join(target, "DiceRushExtended", "README.txt")),
                                  ("UNINSTALL.bat", os.path.join(target, UNINSTALL_NAME))):
            source = os.path.join(DIST, name)
            if os.path.exists(source):
                shutil.copy2(source, destination)
    print("installed to", target)


MOD_VERSION = "1.1.1"


def make_release_zip():
    """dist/Dice-Rush-Extended-<version>.zip with the same layout as an installed game folder."""
    import zipfile
    path = os.path.join(DIST, "Dice-Rush-Extended-%s.zip" % MOD_VERSION)
    entries = [
        (os.path.join(DIST, "override.cfg"), "override.cfg"),
        (os.path.join(DIST, "DiceRushExtended", "boot.gd"), "DiceRushExtended/boot.gd"),
        (os.path.join(DIST, "DiceRushExtended", "DiceRushExtended.pck"), "DiceRushExtended/DiceRushExtended.pck"),
        (os.path.join(DIST, "README.txt"), "DiceRushExtended/README.txt"),
        (os.path.join(DIST, "UNINSTALL.bat"), UNINSTALL_NAME),
    ]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, name in entries:
            archive.write(source, name)
    print("release zip:", path, "(%.1f KB)" % (os.path.getsize(path) / 1024))
    return path


if __name__ == "__main__":
    import apply_patches
    apply_patches.main()
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'i18n'))
    import build_i18n
    build_i18n.main()
    files = collect()
    output = make_dist()
    pack(files, output)
    if "--release" in sys.argv:
        make_release_zip()
    if "--install-test" in sys.argv:
        install(TESTGAME, test=True)
    if "--install-game" in sys.argv:
        if not GAME or not os.path.exists(os.path.join(GAME, "Dice Rush.exe")):
            raise SystemExit("game folder not found - set DICE_RUSH_DIR or tools/local_paths.json")
        install(GAME, test=False)
