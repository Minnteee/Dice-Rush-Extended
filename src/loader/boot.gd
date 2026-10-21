extends Node
## Dice Rush Extended - loader.
## Registered as an autoload through override.cfg. It mounts DiceRushExtended.pck
## before the game scenes are loaded, so the modded scripts replace the
## original ones, and then starts the mod core.

const PACK_FILE := "DiceRushExtended.pck"
const CORE_SCRIPT := "res://bdr/core/bdr_core.gd"

var pack_loaded := false
var pack_path := ""
var core: Node


func _init() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var candidates: Array[String] = []
	var exe_dir := OS.get_executable_path().get_base_dir()
	candidates.append(exe_dir.path_join("DiceRushExtended").path_join(PACK_FILE))
	candidates.append(OS.get_environment("BDR_PACK_OVERRIDE"))
	for candidate in candidates:
		if candidate.is_empty() or not FileAccess.file_exists(candidate):
			continue
		pack_path = candidate
		pack_loaded = ProjectSettings.load_resource_pack(candidate, true)
		if pack_loaded:
			break
	if pack_loaded:
		print("BDR_BOOT=PACK_LOADED ", pack_path)
	else:
		push_error("Dice Rush Extended: mod pack not found or not loadable (%s)" % pack_path)


func _ready() -> void:
	if not pack_loaded:
		return
	var script := load(CORE_SCRIPT) as Script
	if script == null:
		push_error("Dice Rush Extended: core script missing")
		return
	core = script.new() as Node
	core.name = "BDRCore"
	add_child(core)
