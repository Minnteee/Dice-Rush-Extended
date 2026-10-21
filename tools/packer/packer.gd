extends Node
## Builds a PCK with the engine version of the game itself.
## Usage: "Dice Rush.exe" --headless -- --manifest=F:/path/manifest.json

func _ready() -> void:
	var manifest_path := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--manifest="):
			manifest_path = arg.trim_prefix("--manifest=")
	if manifest_path.is_empty():
		printerr("BDR_PACK_ERROR no manifest")
		get_tree().quit(2)
		return
	var manifest = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if manifest is not Dictionary:
		printerr("BDR_PACK_ERROR bad manifest")
		get_tree().quit(3)
		return
	var packer := PCKPacker.new()
	var err := packer.pck_start(str(manifest.output))
	if err != OK:
		printerr("BDR_PACK_ERROR pck_start ", err)
		get_tree().quit(4)
		return
	var count := 0
	for pair in manifest.files:
		err = packer.add_file(str(pair[0]), str(pair[1]))
		if err != OK:
			printerr("BDR_PACK_ERROR add_file ", pair, " ", err)
			get_tree().quit(5)
			return
		count += 1
	err = packer.flush(false)
	print("BDR_PACK_DONE files=%d err=%d" % [count, err])
	get_tree().quit(0 if err == OK else 6)
