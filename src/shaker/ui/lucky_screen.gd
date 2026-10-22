extends "res://shaker/ui/screen_base.gd"
## Lucky Cube: rerolls the unlocked dice into new dice (their levels stay).
## Left: your dice (click = lock). Middle: ROLL and the 5 tiers. Right: the chances of the tier.

const CUBE := "res://assets/art/lucky_dice/lucky_cube_placeholder.webp"

var tier := 0
var rows: Array = []
var tier_buttons: Array = []
var roll_button: Button
var status_label: Label
var cube: TextureRect
var odds_rows: Array = []
var fresh: Dictionary = {}          # die index -> true (just rolled into a new kind)
var signature := ""


func _build() -> void:
	var panel := frame(I18N.t("lucky.title"))
	tier = clampi(int(game.state.get("lucky_tier", 0)), 0, 4)
	# left: your dice
	var left := Kit.panel(panel, Rect2(24, 100, 540, 900), Kit.PANEL_LIGHT, Kit.GOLD, 3, 16)
	Kit.label(left, I18N.t("lucky.your_dice"), Rect2(16, 8, 508, 44), 20, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT)
	for i in range(12):
		var row := Button.new()
		row.position = Vector2(14, 58 + i * 69)
		row.size = Vector2(512, 64)
		row.focus_mode = Control.FOCUS_ALL
		row.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		row.pressed.connect(_toggle.bind(i))
		row.mouse_entered.connect(_row_tip.bind(i))
		row.mouse_exited.connect(hide_tip)
		left.add_child(row)
		var icon := Kit.texture(row, null, Rect2(6, 4, 56, 56), false)
		var name_label := Kit.label(row, "", Rect2(70, 2, 300, 34), 14, HORIZONTAL_ALIGNMENT_LEFT, Kit.TEXT)
		var info := Kit.label(row, "", Rect2(70, 32, 300, 28), 11, HORIZONTAL_ALIGNMENT_LEFT, Kit.MUTED)
		var lock := Kit.label(row, "", Rect2(370, 4, 136, 56), 12, HORIZONTAL_ALIGNMENT_CENTER, Kit.BAD)
		rows.append({"row": row, "icon": icon, "name": name_label, "info": info, "lock": lock})
	# middle: the cube, ROLL and the tiers
	var middle := Kit.panel(panel, Rect2(584, 100, 672, 900), Kit.PANEL_LIGHT, Kit.GOLD, 3, 16)
	cube = Kit.texture(middle, Tex.square(CUBE, 256), Rect2(216, 10, 240, 240), false)
	cube.pivot_offset = Vector2(120, 120)
	status_label = Kit.paragraph(middle, I18N.t("lucky.hint"), Rect2(24, 252, 624, 84), 12, HORIZONTAL_ALIGNMENT_CENTER, Kit.MUTED)
	roll_button = Kit.button(middle, I18N.t("lucky.roll"), Rect2(76, 340, 520, 96), _roll, 24, Color("2f6a3c"), Kit.GOLD_LIGHT)
	for t in range(5):
		var button := Kit.button(middle, "", Rect2(76, 456 + t * 86, 520, 76), _select_tier.bind(t), 15)
		tier_buttons.append(button)
	# right: chances
	var right := Kit.panel(panel, Rect2(1276, 100, 540, 900), Kit.PANEL_LIGHT, Kit.GOLD, 3, 16)
	Kit.label(right, I18N.t("lucky.odds"), Rect2(16, 8, 508, 44), 20, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT)
	for r in range(5):
		var rarity := str(Data.rarities[r])
		var y := 80 + r * 130
		Kit.label(right, I18N.upper(I18N.t("rarity." + rarity)), Rect2(30, y, 300, 40), 18, HORIZONTAL_ALIGNMENT_LEFT, Data.rarity_color(rarity))
		var percent := Kit.label(right, "", Rect2(330, y, 180, 40), 20, HORIZONTAL_ALIGNMENT_RIGHT, Kit.TEXT)
		var bar := Kit.bar(right, Rect2(30, y + 50, 480, 26), Data.rarity_color(rarity))
		odds_rows.append({"percent": percent, "bar": bar})
	Kit.paragraph(right, I18N.t("lucky.tier_hint"), Rect2(30, 740, 480, 120), 12, HORIZONTAL_ALIGNMENT_CENTER, Kit.MUTED)
	refresh()


func _unlocked_count() -> int:
	var count := 0
	for die in game.state.dice:
		if not bool(die.get("locked", false)):
			count += 1
	return count


func refresh() -> void:
	super.refresh()
	var state: Dictionary = game.state
	var dice: Array = state.dice
	var sig := ""
	for die in dice:
		sig += "%s:%d:%s|" % [die.id, int(die.level), str(die.get("locked", false))]
	if sig != signature:
		signature = sig
		for i in rows.size():
			var widgets: Dictionary = rows[i]
			var row: Button = widgets.row
			row.visible = i < dice.size()
			if i >= dice.size():
				continue
			var die: Dictionary = dice[i]
			var def := Data.die(str(die.id))
			var color := Data.rarity_color(str(def.rarity))
			var locked := bool(die.get("locked", false))
			(widgets.icon as TextureRect).texture = Tex.square(str(def.art), 64)
			Kit.set_text(widgets.name, I18N.upper(game.call("die_name", str(die.id))))
			(widgets.name as Label).add_theme_color_override("font_color", color)
			var level_text: String = I18N.t("die.max") if int(die.level) >= int(Data.b("max_level", 100)) else I18N.f("die.level", {"v": int(die.level)})
			Kit.set_text(widgets.info, "%s · %s" % [I18N.t("rarity." + str(def.rarity)), level_text])
			Kit.set_text(widgets.lock, I18N.t("die.locked") if locked else (I18N.t("lucky.new") if fresh.has(i) else ""))
			(widgets.lock as Label).add_theme_color_override("font_color", Kit.BAD if locked else Kit.GOOD)
			for style_name in ["normal", "hover", "pressed", "focus"]:
				var fill := Color("3a1420") if locked else Color("1d1030")
				var box := Kit.style(fill.lightened(0.12) if style_name == "hover" else fill, color if style_name != "focus" else Kit.GOLD_LIGHT, 3 if not locked else 4, 12)
				row.add_theme_stylebox_override(style_name, box)
	var count := _unlocked_count()
	for t in tier_buttons.size():
		var button: Button = tier_buttons[t]
		var price: float = Rules.lucky_price(state, game.stats, t, maxi(1, count))
		Kit.set_button_text(button, "%s   ·   %s" % [I18N.f("lucky.tier", {"v": t + 1}), I18N.money(price)])
		var selected := t == tier
		var best_rarity := 0
		var odds := Rules.lucky_odds(game.stats, t)
		for r in range(5):
			if odds[r] > 0.0:
				best_rarity = r
		var color := Data.rarity_color(str(Data.rarities[best_rarity]))
		button.add_theme_stylebox_override("normal", Kit.style(Color("4a2a70") if selected else Kit.BUTTON, color if selected else color.darkened(0.35), 5 if selected else 3, 12))
	var total: float = Rules.lucky_price(state, game.stats, tier, count)
	if count <= 0:
		Kit.set_button_text(roll_button, I18N.t("lucky.all_locked"))
		roll_button.disabled = true
	else:
		Kit.set_button_text(roll_button, "%s  ·  %s" % [I18N.t("lucky.roll"), I18N.f("lucky.cost", {"v": total, "n": count}).replace("$$", "$")])
		roll_button.disabled = float(state.money) < total
	var odds := Rules.lucky_odds(game.stats, tier)
	for r in odds_rows.size():
		Kit.set_text(odds_rows[r].percent, "%s%%" % I18N.number(snappedf(odds[r], 0.1)))
		(odds_rows[r].bar as ProgressBar).value = odds[r] / 100.0


func _select_tier(t: int) -> void:
	tier = t
	game.state["lucky_tier"] = t
	refresh()


func _toggle(index: int) -> void:
	game.call("toggle_lock", index)
	fresh.erase(index)
	refresh()
	_row_tip(index)


func _row_tip(index: int) -> void:
	var dice: Array = game.state.dice
	if index < dice.size():
		tooltip(game.call("die_info", str(dice[index].id), dice[index]))


func _roll() -> void:
	var results: Array = game.call("lucky_roll", tier)
	if results.is_empty():
		return
	fresh.clear()
	for result in results:
		if bool(result.first):
			fresh[int(result.index)] = true
	signature = ""
	var tween := cube.create_tween()
	tween.tween_property(cube, "rotation", deg_to_rad(-12.0), 0.08)
	tween.tween_property(cube, "rotation", deg_to_rad(10.0), 0.12)
	tween.tween_property(cube, "rotation", 0.0, 0.1)
	refresh()
