extends RefCounted
## Dice Rush Extended dice catalog (res://bdr/data/dice_catalog.json).

const PATH := "res://bdr/data/dice_catalog.json"
const ART_ROOT := "res://bdr/art/dice/"
const LANDMARKS_PATH := "res://bdr/art/dice/landmarks.json"
const I18N := preload("res://bdr/core/i18n.gd")
const NumFmt := preload("res://bdr/core/numfmt.gd")

var dice: Array = []
var by_id: Dictionary = {}
var ids: Array[String] = []
var landmarks: Dictionary = {}


func load_catalog() -> void:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if parsed is not Dictionary:
		push_error("Dice Rush Extended: dice catalog missing")
		return
	dice = parsed.get("dice", [])
	for entry in dice:
		var id := str(entry.id)
		entry["price"] = float(entry.price)
		entry["unlock_price"] = float(entry.get("unlock_price", 0))
		entry["pay"] = float(entry.pay)
		entry["tier"] = int(entry.tier)
		var face_values := PackedInt32Array()
		for face in entry.get("faces", []):
			face_values.append(int(face))
		entry["faces_packed"] = face_values
		by_id[id] = entry
		ids.append(id)
	if FileAccess.file_exists(LANDMARKS_PATH):
		var marks = JSON.parse_string(FileAccess.get_file_as_string(LANDMARKS_PATH))
		if marks is Dictionary:
			landmarks = marks


func has(kind: String) -> bool:
	return by_id.has(kind)


func get_def(kind: String) -> Dictionary:
	return by_id.get(kind, {})


func texture_path(kind: String) -> String:
	return ART_ROOT + kind + ".png"


func name_of(kind: String) -> String:
	var key := "dice.%s.name" % kind
	if I18N.has(key):
		return I18N.t(key)
	var def := get_def(kind)
	var names: Dictionary = def.get("name", {})
	return str(names.get(GameSession.language, names.get("en", kind)))


func description_of(kind: String) -> String:
	var def := get_def(kind)
	var params := {"pay": float(def.get("pay", 0))}
	var extra: Dictionary = def.get("p", {})
	for key in extra:
		params[key] = extra[key]
	var key := "dice.%s.desc" % kind
	if I18N.has(key):
		return I18N.f(key, params)
	var descs: Dictionary = def.get("desc", {})
	var text := str(descs.get(GameSession.language, descs.get("en", "")))
	for param in params:
		var value = params[param]
		text = text.replace("{" + str(param) + "}", NumFmt.compact(value) if (value is int or value is float) else str(value))
	return GameSession.localize_currency_text(text)


func by_tier(tier: int) -> Array:
	var result: Array = []
	for entry in dice:
		if int(entry.tier) == tier:
			result.append(entry)
	return result


## Price of the next copy when `owned` copies were bought before.
static func grown_price(base: float, owned: int) -> float:
	var price := maxf(1.0, base)
	for index in range(1, owned + 1):
		var factor := 1.12
		if index > 100:
			factor = 1.6
		elif index > 50:
			factor = 1.35
		elif index > 25:
			factor = 1.2
		price = ceilf(price * factor)
		if price >= 1.0e300:
			return 1.0e300
	return price
