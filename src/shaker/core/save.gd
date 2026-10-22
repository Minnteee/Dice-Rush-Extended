extends RefCounted
## Dice Shaker save cards: user://shaker_slot_<n>.json - 3 cards, separate from the normal game.
## Every write goes to a .tmp file first; the previous save is kept as .bak.

const SLOT_COUNT := 3
const VERSION := 1
const MODE := "dice_shaker"


static func path(slot: int) -> String:
	return "user://shaker_slot_%d.json" % clampi(slot, 1, SLOT_COUNT)


static func _parse(file_path: String) -> Dictionary:
	if not FileAccess.file_exists(file_path):
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(file_path))
	if parsed is Dictionary and str(parsed.get("mode", "")) == MODE and parsed.get("dice") is Array:
		return parsed
	return {}


static func occupied(slot: int) -> bool:
	return FileAccess.file_exists(path(slot)) or FileAccess.file_exists(path(slot) + ".bak")


## The save of a card ({} if there is none or it cannot be read). Falls back to the backup.
static func read(slot: int) -> Dictionary:
	var data := _parse(path(slot))
	if data.is_empty():
		data = _parse(path(slot) + ".bak")
	return data


static func write(slot: int, data: Dictionary) -> bool:
	var target := path(slot)
	data["mode"] = MODE
	data["version"] = VERSION
	data["modified"] = int(Time.get_unix_time_from_system())
	var text := JSON.stringify(data)
	var temp := target + ".tmp"
	var file := FileAccess.open(temp, FileAccess.WRITE)
	if file == null:
		push_error("Dice Shaker: cannot write %s" % temp)
		return false
	file.store_string(text)
	file.close()
	if _parse(temp).is_empty():
		push_error("Dice Shaker: save check failed")
		DirAccess.remove_absolute(ProjectSettings.globalize_path(temp))
		return false
	var dir := DirAccess.open("user://")
	if dir == null:
		return false
	if FileAccess.file_exists(target):
		if FileAccess.file_exists(target + ".bak"):
			dir.remove(target.get_file() + ".bak")
		dir.rename(target.get_file(), target.get_file() + ".bak")
	return dir.rename(temp.get_file(), target.get_file()) == OK


static func delete(slot: int) -> void:
	var dir := DirAccess.open("user://")
	if dir == null:
		return
	for suffix in ["", ".bak", ".tmp"]:
		var file_name: String = path(slot).get_file() + str(suffix)
		if dir.file_exists(file_name):
			dir.remove(file_name)


## For the save card in the menu: occupied, valid, money, play time (seconds).
static func summary(slot: int) -> Dictionary:
	if not occupied(slot):
		return {"occupied": false, "valid": false, "money": 0.0, "play_time": 0}
	var data := read(slot)
	if data.is_empty():
		return {"occupied": true, "valid": false, "money": 0.0, "play_time": 0}
	return {"occupied": true, "valid": true, "money": float(data.get("money", 0.0)), "play_time": int(float(data.get("play_time", 0.0)))}


static func first_empty() -> int:
	for slot in range(1, SLOT_COUNT + 1):
		if not occupied(slot):
			return slot
	return 1


static func most_recent() -> int:
	var best := 1
	var best_time := -1
	for slot in range(1, SLOT_COUNT + 1):
		if not occupied(slot):
			continue
		var data := read(slot)
		var stamp := int(data.get("modified", 0))
		if stamp > best_time:
			best_time = stamp
			best = slot
	return best
