extends RefCounted
## Dice Rush Extended - mod settings (user://bdr_settings.json, shared by all save slots).

const PATH := "user://bdr_settings.json"
const DEFAULTS := {
	"anim_budget": 160,
	"hover_budget": 220,
	"spin3d_budget": 120,
	"batch": true,
	"quality": "medium",
	"coop_port": 47777,
	"coop_last_ip": "",
	"coop_name": "",
}
const QUALITY := {
	"high": {"anim_budget": 320, "hover_budget": 420, "spin3d_budget": 220},
	"medium": {"anim_budget": 160, "hover_budget": 220, "spin3d_budget": 120},
	"low": {"anim_budget": 64, "hover_budget": 96, "spin3d_budget": 40},
}


static func load_settings() -> Dictionary:
	var data: Dictionary = DEFAULTS.duplicate(true)
	if FileAccess.file_exists(PATH):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		if parsed is Dictionary:
			for key in parsed:
				data[key] = parsed[key]
	var preset: Dictionary = QUALITY.get(str(data.get("quality", "medium")), {})
	for key in preset:
		data[key] = preset[key]
	return data


static func save_settings(data: Dictionary) -> void:
	var file := FileAccess.open(PATH, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(data, "\t"))
		file.close()


static func set_value(key: String, value: Variant) -> Dictionary:
	var data := load_settings()
	data[key] = value
	save_settings(data)
	return load_settings()
