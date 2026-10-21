extends RefCounted
## Dice Rush Extended translations. Strings live in res://bdr/i18n/<language>.json
## (flat key -> text). "$" is replaced with the language's currency symbol.

const ROOT := "res://bdr/i18n/"
const NumFmt := preload("res://bdr/core/numfmt.gd")
static var _tables: Dictionary = {}


static func table(language: String) -> Dictionary:
	if _tables.has(language):
		return _tables[language]
	var path := ROOT + language + ".json"
	var data: Dictionary = {}
	if FileAccess.file_exists(path):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
		if parsed is Dictionary:
			data = parsed
	_tables[language] = data
	return data


static func has(key: String) -> bool:
	return table(GameSession.language).has(key) or table("en").has(key)


static func raw(key: String) -> String:
	var value = table(GameSession.language).get(key)
	if value == null:
		value = table("en").get(key)
	if value == null:
		return key
	return str(value)


static func t(key: String) -> String:
	return GameSession.localize_currency_text(raw(key))


## Upper case that respects Turkish (i -> İ) and Greek (capitals without accents).
static func upper(text: String) -> String:
	var language := str(GameSession.language)
	if language == "tr":
		text = text.replace("i", "İ")
	var result := text.to_upper()
	if language == "el":
		var plain := {"Ά": "Α", "Έ": "Ε", "Ή": "Η", "Ί": "Ι", "Ό": "Ο", "Ύ": "Υ", "Ώ": "Ω", "ΐ": "Ϊ", "ΰ": "Ϋ"}
		for accented in plain:
			result = result.replace(accented, plain[accented])
	return result


## Formats "{name}" placeholders. Numbers are shown in the game's compact format.
static func f(key: String, params: Dictionary) -> String:
	var text := raw(key)
	for param in params:
		var value = params[param]
		var shown := ""
		if value is int or value is float:
			shown = NumFmt.compact(value)
		else:
			shown = str(value)
		text = text.replace("{" + str(param) + "}", shown)
	return GameSession.localize_currency_text(text)
