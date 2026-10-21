# Exact in-place edits for start_menu.gd (each must match once).
EDITS = [
    ('\t_apply_settings()\n\t_show_main()\n\t_fit_all_ui_text.call_deferred()\n',
     '\t_apply_settings()\n\t_show_main()\n\t_fit_all_ui_text.call_deferred()\n\t_bdr_after_ready.call_deferred()\n'),
    ('func _close_save_slots_to_main() -> void :\n',
     'func _close_save_slots_to_main() -> void :\n\t_bdr_host_pending = false\n'),
]
