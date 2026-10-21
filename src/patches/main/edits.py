# Exact in-place edits for main.gd (applied after the block replacements). Each must match once.
EDITS = [
    ('func _talent_title(key: String) -> String:\n\tif key.begins_with("workers_"):',
     'func _talent_title(key: String) -> String:\n\tif key.begins_with("bdr_"):\n\t\treturn bdr.talent_title(key)\n\tif key.begins_with("workers_"):'),
    ('func _talent_effect(key: String) -> String:\n\tif key.begins_with("workers_"):',
     'func _talent_effect(key: String) -> String:\n\tif key.begins_with("bdr_"):\n\t\treturn bdr.talent_effect(key)\n\tif key.begins_with("workers_"):'),
    ('func _talent_icon_path(key: String) -> String:\n\tif key == "achievement_god":',
     'func _talent_icon_path(key: String) -> String:\n\tif key.begins_with("bdr_"):\n\t\treturn bdr.talent_icon(key)\n\tif key == "achievement_god":'),
    ('func _talent_tint(key: String) -> Color:\n\tif key == "achievement_god":',
     'func _talent_tint(key: String) -> Color:\n\tif key.begins_with("bdr_"):\n\t\treturn Color.WHITE\n\tif key == "achievement_god":'),
    ('func _talent_tier(key: String) -> int:\n\tif key.begins_with("workers_"):',
     'func _talent_tier(key: String) -> int:\n\tif key.begins_with("bdr_"):\n\t\treturn bdr.talent_tier(key)\n\tif key.begins_with("workers_"):'),
    ('\telif key.begins_with("workers_"):\n\n\n\n\t\tvar worker_icon',
     '\telif key.begins_with("workers_") or key.begins_with("bdr_workers_"):\n\t\tvar worker_icon'),
    ('\t\tlucky_collection_signature = signature\n\t\t_rebuild_lucky_collection()\n',
     '\t\tlucky_collection_signature = signature\n\t\t_rebuild_lucky_collection()\n\tbdr.lucky.refresh_box()\n'),
    ('\tdog_shrine_controller.configure(pixel_font, display_font)\n',
     '\tdog_shrine_controller.configure(pixel_font, display_font)\n\tdog_shrine_controller.bdr_hooks = bdr.tarot\n'),
    # coop: payout / text popups are shown on the partner's screen too
    ('\tactive_payout_popups += 1\n\tvar popup_width: = 560.0',
     '\tactive_payout_popups += 1\n\tbdr.coop_popup(world_position, text, positive)\n\tvar popup_width: = 560.0'),
    # coop: tell the partner where the cubes of a golden storm wave are
    ('\t\tbutton.pressed.connect(_collect_golden_bone_storm_cube.bind(button, percent))\n\t\tadd_child(button)\n\t\tgolden_bone_storm_buttons.append(button)\n',
     '\t\tbutton.pressed.connect(_collect_golden_bone_storm_cube.bind(button, percent))\n\t\tadd_child(button)\n\t\tgolden_bone_storm_buttons.append(button)\n\t_coop_storm_wave()\n'),
    # coop: the table keeps running, so the tarot screen must not wait for a quiet table
    ('\tdog_shrine_entry_draining = not _dog_shrine_world_is_quiet()\n',
     '\tdog_shrine_entry_draining = not _dog_shrine_world_is_quiet() and not bdr.world_runs_during_menus() and not bdr.is_coop_client()\n'),
    # coop client: leaving the game needs no save
    ('func _request_safe_action(action: String) -> void :\n',
     'func _request_safe_action(action: String) -> void :\n\tif bdr.is_coop_client() and bdr.coop_leave(action):\n\t\treturn\n'),
]

# Replaced everywhere in main.gd.
GLOBAL_EDITS = [
    ("GameSession.currency_text(", "_bdr_money_text("),
]
