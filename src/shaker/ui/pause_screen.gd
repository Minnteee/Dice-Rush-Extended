extends "res://shaker/ui/screen_base.gd"
## Pause menu: continue, or save and go back to the main menu. Shows a few statistics.


func _build() -> void:
	var rect := Rect2(560, 230, 800, 600)
	var panel := Kit.panel(root, rect, Kit.PANEL, Kit.GOLD, 4, 22)
	Kit.label(panel, I18N.t("pause.title"), Rect2(20, 20, 760, 80), 44, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT, true)
	Kit.button(panel, I18N.t("pause.resume"), Rect2(150, 130, 500, 86), close, 20, Color("2f6a3c"))
	Kit.button(panel, I18N.t("pause.save_quit"), Rect2(150, 236, 500, 86), _quit, 18)
	Kit.label(panel, I18N.t("pause.stats_title"), Rect2(20, 350, 760, 40), 18, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD)
	var state: Dictionary = game.state
	var seconds := int(float(state.get("play_time", 0.0)))
	var time := "%d:%02d:%02d" % [seconds / 3600, (seconds / 60) % 60, seconds % 60]
	var stats_text := I18N.f("pause.stats", {"a": int(state.get("shakes", 0)), "b": float(state.get("total_earned", 0.0)), "c": time})
	Kit.paragraph(panel, stats_text.replace("  ·  ", "\n"), Rect2(60, 392, 680, 120), 15, HORIZONTAL_ALIGNMENT_CENTER, Kit.TEXT)
	var combo_help := I18N.f("combo.help", {
		"p2": float(Data.b("combo_group", {}).get("2", 1.25)), "p3": float(Data.b("combo_group", {}).get("3", 1.6)),
		"p4": float(Data.b("combo_group", {}).get("4", 2.2)), "p5": float(Data.b("combo_group", {}).get("5", 3.0)),
		"p6": float(Data.b("combo_group", {}).get("6", 4.5)), "st": float(Data.b("combo_straight", 2.0)), "as": float(Data.b("combo_all_same", 4.0)),
	})
	Kit.paragraph(panel, combo_help, Rect2(40, 516, 720, 70), 11, HORIZONTAL_ALIGNMENT_CENTER, Kit.MUTED)


func _quit() -> void:
	game.call("exit_to_menu")
