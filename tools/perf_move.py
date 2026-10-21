"""Mouse-move performance probe for the user's crowded save (test install only).

python perf_move.py [runs] [--wait N]
Prints frame time, frame phases, main._process sections and per-frame counters.
"""
import sys
import time

import bdr


def r(expr):
    return bdr.request({"cmd": "eval", "expr": expr}).get("result")


def wait_started(extra_seconds):
    for _ in range(80):
        if r("m().get('game_started')"):
            break
        time.sleep(0.5)
    if extra_seconds > 0:
        bdr.request({"cmd": "wait", "seconds": extra_seconds})


MAIN_SECTIONS = ["ui", "light_rolls", "golden_bone", "hover_roll", "hover_drain", "golden_dice", "bdr_world"]


def run(label, move=True, path=(200, 300, 950, 900), steps=150, per_frame=2, show_sections=True):
    r("m().set('bdr_prof', {})")
    r("m().set('bdr_prof_on', true)")
    r("phases_start()")
    r("reset_frames()")
    if move:
        bdr.request({"cmd": "move", "x1": path[0], "y1": path[1], "x2": path[2], "y2": path[3],
                     "steps": steps, "per_frame": per_frame})
    else:
        bdr.request({"cmd": "frames", "count": 70})
    ph = r("phases_stop()")
    fs = r("frame_stats()")
    prof = r("m().bdr_prof") or {}
    r("m().set('bdr_prof_on', false)")
    frames = max(1, fs["samples"])
    main_ms = sum(prof.get(k, 0) for k in MAIN_SECTIONS) / 1000.0 / frames
    print("%-12s avg %5.1f ms p95 %5.1f | process %5.1f (pre %.1f, callbacks %.1f [main %.1f], post %.1f) render %4.1f | landings/f %5.1f" % (
        label, fs["avg_ms"], fs["p95_ms"], ph["process_ms"], ph.get("pre_ms", 0), ph.get("callbacks_ms", 0), main_ms,
        ph.get("post_ms", 0), ph["render_ms"], prof.get("landings", 0) / frames))
    counters = {k: v / frames for k, v in prof.items() if k.startswith("c_")}
    if counters:
        print("   counters/f: " + "  ".join("%s=%.1f" % (k[2:], v) for k, v in sorted(counters.items())))
    if show_sections:
        sections = [(k, v / 1000.0 / frames) for k, v in prof.items() if not k.startswith("c_") and k != "landings"]
        sections.sort(key=lambda kv: -kv[1])
        print("   sections ms/f: " + "  ".join("%s=%.2f" % kv for kv in sections[:12]))
    return fs["avg_ms"]


if __name__ == "__main__":
    runs = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 2
    wait = 8
    if "--wait" in sys.argv:
        wait = int(sys.argv[sys.argv.index("--wait") + 1])
    wait_started(wait)
    run("idle", move=False)
    for index in range(runs):
        run("move%d" % (index + 1))
        bdr.request({"cmd": "frames", "count": 30})
    print("perf", r("perf()"))
