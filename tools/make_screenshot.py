"""Makes the README screenshot of Dice Rush Extended (test install only).

Two game instances run in coop on the hidden test desktop: the host (harness port 47811,
1920x1080) on a fresh save in slot 3 with ~180 new dice and the "Purple Galaxy" table, and
the guest (harness port 47812). Each player uses another mouse design. The host also draws its
own cursor (a screenshot does not contain the system mouse) and saves the picture.

usage: python make_screenshot.py [output.png]
"""
import os
import subprocess
import sys
import time

import bdr

TOOLS = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(TOOLS, "..", "docs", "screenshot.png")
HOST, GUEST = 47811, 47812
SLOT = 3
BOARD_DESIGN = 3      # Purple Galaxy
HOST_CURSOR = 1       # golden gauntlet
GUEST_CURSOR = 5      # wizard wand
P1_AT = (420.0, 640.0)   # world positions of the two cursors on the table
P2_AT = (760.0, 430.0)
KINDS = ["pepe", "sixseven", "dnd", "clover", "twitch", "youtube", "pirate", "console", "slot", "fire",
         "godot", "tetris", "luckyblock", "pizza", "robot", "magic8", "dragon", "doge", "ninja", "rickroll",
         "nyan", "gigachad", "pumpkin", "skibidi", "sigma", "ufo", "bonk", "ohio", "blackhole", "phoenix",
         "galaxy", "crown", "divine", "omega", "rainbow", "elderdragon", "sun", "kraken", "bunny", "sushi"]


def ev(port, expr):
    reply = bdr.request({"cmd": "eval", "expr": expr}, port=port)
    if not reply.get("ok", True) or (isinstance(reply.get("result"), dict) and "__error" in reply["result"]):
        print("  eval failed:", expr, reply)
    return reply.get("result")


def launch(port, resolution):
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(TOOLS, "launch_test.ps1"),
                    "-Port", str(port), "-Resolution", resolution, "-GameArgs", ""], check=True, capture_output=True)
    for _ in range(120):
        try:
            bdr.request({"cmd": "ping"}, port=port, timeout=2)
            return
        except OSError:
            time.sleep(0.5)
    raise SystemExit("game on port %d did not start" % port)


def wait_for(port, expr, seconds=40):
    end = time.time() + seconds
    while time.time() < end:
        try:
            if ev(port, expr):
                return True
        except OSError:
            pass
        time.sleep(0.5)
    raise SystemExit("timeout waiting for %s" % expr)


USER_DIR = os.path.join(os.environ.get("APPDATA", ""), "Dice Rush BDR Test")


def main():
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(TOOLS, "kill_test.ps1")], capture_output=True)
    time.sleep(1.0)
    settings_path = os.path.join(USER_DIR, "settings.json")
    settings_backup = open(settings_path, "rb").read() if os.path.exists(settings_path) else None
    try:
        shoot()
    finally:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(TOOLS, "kill_test.ps1")], capture_output=True)
        time.sleep(1.0)
        # leave the test install as it was: settings (language, last slot) and no extra save
        if settings_backup is not None:
            open(settings_path, "wb").write(settings_backup)
        for name in os.listdir(USER_DIR):
            if name.startswith("savegame_slot_%d.json" % SLOT):
                os.remove(os.path.join(USER_DIR, name))


def shoot():
    # ---- host: fresh table in slot 3, English texts for the README
    launch(HOST, "1920x1080")
    time.sleep(3.0)
    ev(HOST, "n('/root/GameSession').set_language('en')")
    time.sleep(0.5)
    bdr.request({"cmd": "start_game", "slot": SLOT, "mode": "new"}, port=HOST)
    wait_for(HOST, "m().get('game_started')")
    time.sleep(2.0)
    ev(HOST, "m().set('money', 5.0e33)")
    for kind in KINDS:
        ev(HOST, "m().bdr.unlock('%s', false)" % kind)
    for index, kind in enumerate(KINDS * 4):
        ev(HOST, "m().bdr.spawn_free('%s', m()._random_roll_target(m().bdr.board_safe_rect().get_center()))" % kind)
    for _ in range(6):
        ev(HOST, "m()._buy_npc()")
    ev(HOST, "m().bdr.shop.buy('board', %d)" % BOARD_DESIGN)
    ev(HOST, "m().bdr.shop.buy('cursor', %d)" % HOST_CURSOR)
    ev(HOST, "m().set('money', 1.25e21)")
    ev(HOST, "m()._save_game(true)")
    print("host table:", ev(HOST, "m().dice.size()"), "dice, scale", ev(HOST, "m().bdr.dice_scale()"))
    ev(HOST, "m().bdr.coop_ui._host_now()")
    # ---- guest
    launch(GUEST, "1280x720")
    time.sleep(3.0)
    ev(GUEST, "get_tree().current_scene._bdr_start_client('127.0.0.1', 47777)")
    wait_for(GUEST, "m().get('game_started') and m().bdr.coop.partner_ready", 60)
    ev(GUEST, "m().bdr.design_equip('cursor', %d)" % GUEST_CURSOR)
    time.sleep(2.0)
    # ---- both cursors on the table (fixed test positions, the real mouse is not used)
    ev(HOST, "m().bdr.coop.set('test_cursor', Vector2(%f, %f))" % P1_AT)
    ev(GUEST, "m().bdr.coop.set('test_cursor', Vector2(%f, %f))" % P2_AT)
    ev(HOST, "m().bdr.coop_ui.set('show_local_cursor', true)")
    time.sleep(4.0)
    # show the first new dice in the shop (the shop layout is settled by now)
    ev(HOST, "m().shop_scroll.set('scroll_vertical', int(m().shop_card_containers['pepe'].position.y) - 12)")
    # a calm moment: no new effect lines / popups for a second, so the dice are easy to see
    ev(HOST, "n('/root/GameSession').set('visual_effects_enabled', false)")
    ev(HOST, "n('/root/GameSession').set('money_popups_enabled', false)")
    time.sleep(1.2)
    out = os.path.abspath(OUT)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print(bdr.request({"cmd": "screenshot", "path": out.replace("\\", "/")}, port=HOST))


if __name__ == "__main__":
    main()
