extends RefCounted
## Dice Shaker texts: res://shaker/i18n/<language>.json (flat key -> text, English fallback).
## "$" becomes the currency symbol of the language. Dice names come from the original game
## (vanilla dice) or from Dice Rush Extended (res://bdr/i18n), so they exist in every language.

const ROOT := "res://shaker/i18n/"
const BDR_ROOT := "res://bdr/i18n/"
const NumFmt := preload("res://shaker/core/numfmt.gd")
const LuckyLocalization := preload("res://scripts/localization_lucky.gd")

static var _tables: Dictionary = {}
static var _bdr_tables: Dictionary = {}


static func _load(root: String, language: String, cache: Dictionary) -> Dictionary:
	if cache.has(language):
		return cache[language]
	var data: Dictionary = {}
	var path := root + language + ".json"
	if FileAccess.file_exists(path):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
		if parsed is Dictionary:
			data = parsed
	cache[language] = data
	return data


static func language() -> String:
	return str(GameSession.language)


static func raw(key: String) -> String:
	var value = _load(ROOT, language(), _tables).get(key)
	if value == null:
		value = _load(ROOT, "en", _tables).get(key)
	if value == null:
		return key
	return str(value)


static func t(key: String) -> String:
	return GameSession.localize_currency_text(raw(key))


## "{name}" placeholders; numbers are shown short (1.5K, 2M ...).
static func f(key: String, params: Dictionary) -> String:
	return GameSession.localize_currency_text(fill(raw(key), params))


static func fill(text: String, params: Dictionary) -> String:
	for param in params:
		var value = params[param]
		var shown := ""
		if value is int or value is float:
			shown = number(value)
		else:
			shown = str(value)
		text = text.replace("{" + str(param) + "}", shown)
	return text


## Short numbers, but small fractions keep up to 2 decimals (x1.25, 0.5 %).
static func number(value: float) -> String:
	if absf(value) < 100.0 and absf(value - roundf(value)) > 0.001:
		var text := ("%.2f" % value).rstrip("0").trim_suffix(".")
		return text
	return NumFmt.compact(value)


static func money(value: float) -> String:
	return GameSession.localize_currency_text(NumFmt.compact(value) + "$")


## Upper case that respects Turkish (i -> İ) and Greek (capitals without accents).
static func upper(text: String) -> String:
	if language() == "tr":
		text = text.replace("i", "İ")
	var result := text.to_upper()
	if language() == "el":
		var plain := {"Ά": "Α", "Έ": "Ε", "Ή": "Η", "Ί": "Ι", "Ό": "Ο", "Ύ": "Υ", "Ώ": "Ω", "ΐ": "Ϊ", "ΰ": "Ϋ"}
		for accented in plain:
			result = result.replace(accented, plain[accented])
	return result


## Name of a die: name_src = ["bdr", key] | ["game", key] | ["lucky", key]
static func die_name(def: Dictionary) -> String:
	var source: Array = def.get("name_src", ["", ""])
	var key := str(source[1]) if source.size() > 1 else ""
	match str(source[0]):
		"bdr":
			var value = _load(BDR_ROOT, language(), _bdr_tables).get(key)
			if value == null:
				value = _load(BDR_ROOT, "en", _bdr_tables).get(key)
			if value != null:
				return str(value)
		"game":
			return GameSession.text(key)
		"lucky":
			return LuckyLocalization.text(language(), key)
	return str(def.get("id", "?"))


static func clear_cache() -> void:
	_tables.clear()
	_bdr_tables.clear()
