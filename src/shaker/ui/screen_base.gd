extends Control
## Base for the Dice Shaker full-screen windows (talents, lucky cube, tarot, shop, dice book, menu).

const Data := preload("res://shaker/game/data.gd")
const Rules := preload("res://shaker/game/rules.gd")
const I18N := preload("res://shaker/core/i18n.gd")
const NumFmt := preload("res://shaker/core/numfmt.gd")
const Tex := preload("res://shaker/core/tex.gd")
const Kit := preload("res://shaker/ui/kit.gd")
const ART := "res://shaker/art/"

var game
var root: Control
var money_label: Label


func build(main) -> void:
	game = main
	mouse_filter = Control.MOUSE_FILTER_STOP
	var layer := Kit.overlay(self, 0.8)
	root = Control.new()
	root.position = game.call("safe_origin")
	root.size = Vector2(1920, 1080)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(root)
	_build()


## Window frame with a title, the money display and a close button.
func frame(title: String, rect: Rect2 = Rect2(40, 28, 1840, 1024)) -> Panel:
	var panel := Kit.panel(root, rect, Kit.PANEL, Kit.GOLD, 4, 22)
	Kit.label(panel, title, Rect2(30, 14, rect.size.x - 60, 70), 40, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT, true)
	money_label = Kit.label(panel, "", Rect2(30, 22, 520, 50), 22, HORIZONTAL_ALIGNMENT_LEFT, Kit.GOLD_LIGHT)
	Kit.button(panel, I18N.t("common.close"), Rect2(rect.size.x - 250, 20, 220, 58), close, 16)
	return panel


func close() -> void:
	game.call("close_screen")


func refresh() -> void:
	if money_label:
		Kit.set_text(money_label, I18N.money(float(game.state.money)))


func _build() -> void:
	pass


## One line of text for a bonus ("Money +25%", "XP x2" ...).
static func stat_line(key: String, value: float) -> String:
	var text := I18N.raw("stat." + key)
	if value < 0.0:
		text = text.replace("+{v}", "{v}")
	if key in ["slots", "compact", "black_market", "ones_as_six"]:
		return GameSession.localize_currency_text(text.replace("{v}", str(int(value))))
	# bonuses are shown in full ("+1000%", not "+1K%")
	if absf(value) < 1.0e6 and absf(value - roundf(value)) < 0.001:
		return GameSession.localize_currency_text(text.replace("{v}", str(int(roundf(value)))))
	return GameSession.localize_currency_text(I18N.fill(text, {"v": value}))


static func effects_text(effects: Array) -> String:
	var lines: Array[String] = []
	for effect in effects:
		lines.append(stat_line(str(effect[0]), float(effect[1])))
	return "\n".join(lines)


func icon_texture(icon: String, size: int = 64) -> Texture2D:
	var parts := icon.split(":")
	match parts[0]:
		"die":
			return Tex.square(str(Data.die(parts[1]).get("art", "")), size)
		"tarot":
			return Tex.get_tex(ART + "tarot/%s.png" % parts[1])
		"black":
			return Tex.get_tex(ART + "black/%s.png" % parts[1])
		"gum":
			return Tex.get_tex(ART + "scene/gumball_ball_0.png")
		"cube":
			return Tex.square("res://assets/art/lucky_dice/lucky_cube_placeholder.webp", 128)
	return null


func tooltip(text: String) -> void:
	game.call("show_tooltip", text)


func hide_tip() -> void:
	game.call("hide_tooltip")
