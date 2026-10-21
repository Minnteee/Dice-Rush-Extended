extends RefCounted
## Dice Rush Extended - logic behind the SHOP screen (selling, unlocking, designs).

const I18N := preload("res://bdr/core/i18n.gd")
const DESIGN_COUNT := 10
const BDRSettings := preload("res://bdr/core/settings.gd")

var game: Node
var main: Node
var _cursor_hotspots: Dictionary = {}


func setup(controller: Node) -> void:
	game = controller
	main = controller.main
	var path := "res://bdr/art/cursors/cursors.json"
	if FileAccess.file_exists(path):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
		if parsed is Dictionary:
			_cursor_hotspots = parsed


# ---------------------------------------------------------------- selling
## Share of the purchase price you get back. Capped below 100% so that buying and
## selling can never make money.
func sell_rate() -> float:
	return minf(0.9, 0.5 + game.sell_rate_bonus())


func max_sellable(kind: String) -> int:
	var owned: int = main._owned_die_count(kind)
	return maxi(0, owned - (1 if kind == "50_50" else 0))


func sell_value(kind: String, amount: int) -> float:
	var owned: int = main._owned_die_count(kind)
	amount = clampi(amount, 0, max_sellable(kind))
	var total := 0.0
	var rate := sell_rate()
	for index in range(amount):
		var copy_index := owned - 1 - index
		var price: float = main._next_price(kind, main._price_progress_count(kind, copy_index))
		if price > 0.0:
			total += price * rate
	return total


func sell(kind: String, amount: int) -> Dictionary:
	amount = clampi(amount, 0, max_sellable(kind))
	if amount <= 0:
		return {"ok": false, "error": "ui.sell_none_left"}
	var refund := sell_value(kind, amount)
	var actors: Array = []
	var list: Array = game.dice_of_kind(kind) if game.is_custom_die(kind) else main.dice
	for index in range(list.size() - 1, -1, -1):
		var die = list[index]
		if is_instance_valid(die) and die.die_kind == kind and not die.special_motion and not die.rolling:
			actors.append(die)
			if actors.size() >= amount:
				break
	if actors.size() < amount:
		for index in range(list.size() - 1, -1, -1):
			var die = list[index]
			if is_instance_valid(die) and die.die_kind == kind and die not in actors:
				actors.append(die)
				if actors.size() >= amount:
					break
	var sold := actors.size()
	if sold <= 0:
		return {"ok": false, "error": "ui.sell_none_left"}
	if sold < amount:
		refund = sell_value(kind, sold)
	for die in actors:
		game.remove_die_actor(die)
	main._set_owned_die_count(kind, main._owned_die_count(kind) - sold)
	if kind == "golden":
		main._refresh_gold_auras()
	main._add_money(refund)
	GameSession.play_sfx("purchase")
	game.stat("dice_sold", sold)
	main._report_achievement_snapshot()
	main._update_all_labels()
	main._save_game(true)
	return {"ok": true, "sold": sold, "refund": refund}


# ---------------------------------------------------------------- unlocking
func reveal_threshold(kind: String) -> float:
	var def: Dictionary = game.catalog.get_def(kind)
	if def.is_empty():
		return 0.0
	if int(def.tier) <= 1:
		return 0.0
	return float(def.unlock_price) * 0.2


func is_revealed(kind: String) -> bool:
	return main.total_money_earned >= reveal_threshold(kind) or game.is_unlocked(kind)


## Balance: a shop dice of tier t (t >= 2) can only be unlocked when the player owns enough
## dice of the tier below (10 for tier 2, +5 per tier, 50 for tier 10).
func tier_requirement(kind: String) -> int:
	var def: Dictionary = game.catalog.get_def(kind)
	if def.is_empty() or str(def.unlock) != "shop":
		return 0
	var tier := int(def.tier)
	if tier <= 1:
		return 0
	return 10 + 5 * (tier - 2)


## Owned dice per tier of the new dice (index = tier).
func tier_counts() -> Array[int]:
	var result: Array[int] = []
	result.resize(12)
	for kind in game.catalog.by_id:
		var owned: int = game.count(kind)
		if owned > 0:
			var tier := clampi(int(game.catalog.by_id[kind].tier), 0, 11)
			result[tier] += owned
	return result


func tier_requirement_met(kind: String, counts_by_tier: Array[int] = []) -> bool:
	var need := tier_requirement(kind)
	if need <= 0:
		return true
	var per_tier: Array[int] = counts_by_tier if not counts_by_tier.is_empty() else tier_counts()
	var tier := int(game.catalog.get_def(kind).tier)
	return per_tier[tier - 1] >= need


func unlock(kind: String) -> bool:
	var def: Dictionary = game.catalog.get_def(kind)
	if def.is_empty() or str(def.unlock) != "shop" or game.is_unlocked(kind) or not is_revealed(kind):
		return false
	if not tier_requirement_met(kind):
		GameSession.play_sfx("denied")
		return false
	if not main._spend_money(float(def.unlock_price), null):
		return false
	game.unlock(kind)
	game.stat("shop_unlocks", 1)
	main._save_game(true)
	return true


# ---------------------------------------------------------------- designs
func _cosmetics() -> Dictionary:
	var data: Dictionary = game.extra.get("cosmetics", {})
	if data.is_empty():
		data = {"cursor": 0, "board": 0, "cursors": [0], "boards": [0]}
		game.extra["cosmetics"] = data
	return data


func price(design_type: String, index: int) -> float:
	if index <= 0:
		return 0.0
	if design_type == "cursor":
		return pow(10.0, 3.0 * index + 1.0)
	return 5.0 * pow(10.0, 3.0 * index + 2.0)


func owned(design_type: String, index: int) -> bool:
	if index <= 0:
		return true
	var list: Array = _cosmetics().get(design_type + "s", [0])
	return index in list or float(index) in list


func equipped(design_type: String) -> int:
	return int(_cosmetics().get(design_type, 0))


func buy(design_type: String, index: int) -> bool:
	if owned(design_type, index) or index < 1 or index > DESIGN_COUNT:
		return false
	if not main._spend_money(price(design_type, index), null):
		return false
	var data := _cosmetics()
	var list: Array = data.get(design_type + "s", [0])
	list.append(index)
	data[design_type + "s"] = list
	game.stat("designs_bought", 1)
	equip(design_type, index)
	main._save_game(true)
	return true


func equip(design_type: String, index: int) -> void:
	if not owned(design_type, index):
		return
	_cosmetics()[design_type] = index
	if design_type == "cursor":
		remember_cursor(index)
	apply()


## The mouse design of THIS player. The host (and single player) uses the design of the save;
## a coop guest keeps their own design - it follows the player (saved in the mod settings).
func local_cursor_design() -> int:
	if game.is_coop_client():
		return clampi(int(game.settings.get("my_cursor", equipped("cursor"))), 0, DESIGN_COUNT)
	return equipped("cursor")


func remember_cursor(index: int) -> void:
	if int(game.settings.get("my_cursor", -1)) == index:
		return
	game.settings["my_cursor"] = index
	game.settings = BDRSettings.set_value("my_cursor", index)


## Click point of a mouse design in its 128x128 image.
func cursor_hotspot(index: int) -> Vector2:
	var info = _cursor_hotspots.get("cursor_%d" % index)
	if info is Dictionary and info.get("hotspot") is Array:
		return Vector2(float(info.hotspot[0]), float(info.hotspot[1]))
	return Vector2(4, 4)


## Texture of a mouse design (for the cursor of the other player in coop), null = default arrow.
func cursor_texture(index: int) -> Texture2D:
	if index <= 0 or index > DESIGN_COUNT:
		return null
	return CleanTextureLoader.load_texture("res://bdr/art/cursors/cursor_%d.png" % index)


func preview_path(design_type: String, index: int) -> String:
	if design_type == "cursor":
		return "res://assets/art/cursor_hand.png" if index <= 0 else "res://bdr/art/cursors/cursor_%d.png" % index
	return "res://assets/art/сукно.png" if index <= 0 else "res://bdr/art/boards/board_%d_thumb.png" % index


func display_name(design_type: String, index: int) -> String:
	return I18N.t("design.%s_%d" % [design_type, index])


func apply() -> void:
	_apply_cursor()
	_apply_board()


func _apply_cursor() -> void:
	var index := local_cursor_design()
	if index <= 0:
		GameSession._apply_custom_cursor()
		return
	var path := "res://bdr/art/cursors/cursor_%d.png" % index
	if not FileAccess.file_exists(path):
		GameSession._apply_custom_cursor()
		return
	var image := Image.load_from_file(path)
	if image == null or image.is_empty():
		return
	var used := image.get_used_rect()
	var hotspot := Vector2(used.position)
	var info = _cursor_hotspots.get("cursor_%d" % index)
	if info is Dictionary and info.get("hotspot") is Array:
		hotspot = Vector2(float(info.hotspot[0]), float(info.hotspot[1]))
	var target_height := 68
	var scale := float(target_height) / float(image.get_height())
	image.resize(maxi(1, int(round(image.get_width() * scale))), target_height, Image.INTERPOLATE_NEAREST)
	var texture := ImageTexture.create_from_image(image)
	hotspot *= scale
	hotspot = hotspot.clamp(Vector2.ZERO, Vector2(image.get_width() - 1, image.get_height() - 1))
	for shape in [Input.CURSOR_ARROW, Input.CURSOR_POINTING_HAND, Input.CURSOR_DRAG, Input.CURSOR_CAN_DROP, Input.CURSOR_MOVE]:
		Input.set_custom_mouse_cursor(texture, shape, hotspot)


func _apply_board() -> void:
	var felt = main.get("bdr_felt")
	if felt == null or not is_instance_valid(felt):
		return
	var index := equipped("board")
	var path := "res://assets/art/сукно.png" if index <= 0 else "res://bdr/art/boards/board_%d.png" % index
	if index > 0 and not FileAccess.file_exists(path):
		path = "res://assets/art/сукно.png"
	(felt as TextureRect).texture = CleanTextureLoader.load_texture(path)
