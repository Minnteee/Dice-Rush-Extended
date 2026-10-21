func _bdr_card_name(card_id: String) -> String:
	if card_id.begins_with("m_"):
		return bdr.tarot.card_name(card_id)
	return _dog_text("dog_card_%s_name" % card_id)


func _dog_card_description(card_id: String) -> String:
	if card_id.begins_with("m_"):
		return bdr.tarot.card_description(card_id)
	return DogShrineCards.readable_description(
		GameSession.language,
		_dog_text("dog_card_%s_desc" % card_id)
	)


## Dice that can be sacrificed: only owned ones (original dice first, then the new dice by tier).
func _dog_shrine_inventory_items() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var has_offerings: = _dog_shrine_offerings_left() > 0
	var kinds: Array[String] = []
	for kind in DOG_SHRINE_DICE_KINDS:
		kinds.append(str(kind))
	kinds.append_array(bdr.tarot.offerable_custom_kinds())
	for kind in kinds:
		var count: = _owned_die_count(kind)
		if count <= 0:
			continue
		var required_count: = bdr.tarot.min_amount() + (1 if kind == "50_50" else 0)
		result.append({
			"kind": kind,
			"name": _product_name(kind),
			"icon_path": _lucky_kind_icon_path(kind),
			"count": count,
			"worth": bdr.tarot.worth(kind),
			"can_donate": not dog_shrine_entry_draining and has_offerings and count >= required_count,
		})
	return result


func _dog_shrine_grimoire_data() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for card_value in DogShrineCards.TAROT_ORDER:
		var card_id: = str(card_value)
		result.append({
			"id": card_id,
			"name": _bdr_card_name(card_id),
			"description": _dog_card_description(card_id),
			"rarity": DogShrineCards.rarity(card_id),
			"count": _dog_card_rank(card_id),
			"level": _dog_card_rank(card_id),
			"effect_power": _dog_card_effect_power(card_id),
			"max_rank": -1,
			"art_path": DogShrineCards.art_path(card_id),
		})
	return result


func _dog_shrine_pending_card_data() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var choices_value = pending_dog_shrine_offer.get("choices", [])
	if choices_value is not Array:
		return result
	for choice_value in choices_value:
		var choice: = _dog_shrine_normalize_choice(choice_value, str(pending_dog_shrine_offer.get("donated_kind", "")))
		var card_id: = str(choice.get("id", ""))
		if card_id not in DOG_SHRINE_CARD_IDS:
			continue
		var current_rank: = _dog_card_rank(card_id)
		result.append({
			"id": card_id,
			"name": _bdr_card_name(card_id),
			"description": _dog_card_description(card_id),
			"count": current_rank,
			"level": current_rank,
			"next_rank": _safe_add_int64(current_rank, 1),
			"effect_power": _dog_effect_power_for_rank(_safe_add_int64(current_rank, 1)),
			"max_rank": -1,
			"rarity": DogShrineCards.rarity(card_id),
			"art_path": DogShrineCards.art_path(card_id),
		})
	return result


func _dog_shrine_roll_offer(donated_kind: String) -> Array[Dictionary]:
	return bdr.tarot.roll_offer(donated_kind, bdr.tarot.min_amount())


func _on_dog_shrine_donation_requested(kind: String) -> void :
	var amount: int = bdr.tarot.clamp_amount(int(dog_shrine_controller.bdr_amount))
	if bdr.is_coop_client():
		bdr.coop_request("tarot_donate", [kind, amount])
		return
	var result: = _bdr_tarot_donate(kind, amount)
	if not bool(result.get("ok", false)):
		dog_shrine_controller.show_error(str(result.get("error", "")))
		return
	dog_shrine_controller.set_inventory(_dog_shrine_inventory_items(), _dog_shrine_offerings_left(), false)
	dog_shrine_controller.play_donation_success(kind, _lucky_kind_icon_path(kind), _dog_shrine_pending_card_data(), _dog_shrine_offerings_left())


## Sacrifices dice and rolls the tarot offer (used by the tarot screen and by the coop partner).
func _bdr_tarot_donate(kind: String, requested_amount: int) -> Dictionary:
	var amount: int = bdr.tarot.clamp_amount(requested_amount)
	if dog_shrine_entry_draining:
		return {"ok": false, "error": _dog_text("wait_rolls")}
	if not DiceRushEdition.is_full() or not _is_offerable_kind(kind) or pending_dog_shrine_offer.size() > 0 or _dog_shrine_offerings_left() <= 0:
		return {"ok": false, "error": _dog_text("no_dice")}
	var owned_before: = _owned_die_count(kind)
	var required_count: = amount + (1 if kind == "50_50" else 0)
	if owned_before < required_count:
		return {"ok": false, "error": bdr.tarot.need_text(required_count)}
	var offering_actors: = _find_dog_shrine_actors(kind, amount)
	if offering_actors.size() != amount:
		return {"ok": false, "error": _dog_text("wait_rolls")}
	var choices: = bdr.tarot.roll_offer(kind, amount)
	if choices.is_empty():
		return {"ok": false, "error": _dog_text("no_dice")}
	var old_donated: = int(dog_shrine_donated_counts.get(kind, 0))
	var old_offerings_made: = dog_shrine_offerings_made
	var old_transaction_id: = dog_shrine_transaction_id
	var old_pending: = pending_dog_shrine_offer.duplicate(true)
	var actor_states: Array[Dictionary] = []
	for actor in offering_actors:
		var actor_id: = actor.get_instance_id()
		actor_states.append({
			"actor": actor,
			"index": dice.find(actor),
			"visible": actor.visible,
			"input_pickable": actor.input_pickable,
			"process_mode": actor.process_mode,
			"reserved_by": actor.reserved_by,
			"had_golden_timer": golden_timers.has(actor_id),
			"golden_timer": golden_timers.get(actor_id, 0.0),
		})
		_release_npc_targeting(actor)
	_set_owned_die_count(kind, owned_before - amount)
	dog_shrine_donated_counts[kind] = _safe_add_int64(old_donated, amount)
	dog_shrine_offerings_made = _safe_add_int64(old_offerings_made, 1)
	dog_shrine_transaction_id = _safe_add_int64(dog_shrine_transaction_id, 1)
	pending_dog_shrine_offer = {
		"transaction_id": str(dog_shrine_transaction_id),
		"donated_kind": kind,
		"amount": amount,
		"choices": choices.duplicate(),
	}
	for actor in offering_actors:
		dice.erase(actor)
		golden_dice.erase(actor)
		golden_timers.erase(actor.get_instance_id())
		actor.visible = false
		actor.input_pickable = false
		actor.process_mode = Node.PROCESS_MODE_DISABLED
	if not _save_game(true):
		_set_owned_die_count(kind, owned_before)
		dog_shrine_donated_counts[kind] = old_donated
		dog_shrine_offerings_made = old_offerings_made
		dog_shrine_transaction_id = old_transaction_id
		pending_dog_shrine_offer = old_pending
		for state in actor_states:
			var restored_actor: = state.get("actor") as DiceActor
			if not is_instance_valid(restored_actor):
				continue
			dice.insert(clampi(int(state.get("index", dice.size())), 0, dice.size()), restored_actor)
			restored_actor.visible = bool(state.get("visible", true))
			restored_actor.input_pickable = bool(state.get("input_pickable", true))
			restored_actor.process_mode = int(state.get("process_mode", Node.PROCESS_MODE_INHERIT))
			restored_actor.reserved_by = int(state.get("reserved_by", 0))
			if bool(state.get("had_golden_timer", false)):
				golden_dice.append(restored_actor)
				golden_timers[restored_actor.get_instance_id()] = float(state.get("golden_timer", 0.0))
		_update_all_labels()
		return {"ok": false, "error": ""}
	for actor in offering_actors:
		actor.queue_free()
	if kind == "golden":
		_refresh_gold_auras()
	bdr.stat("tarot_offerings", 1)
	bdr.stat("tarot_dice_sacrificed", amount)
	if amount >= 100:
		bdr.stat("tarot_big_offer", 1)
	if amount >= 250:
		bdr.stat("tarot_huge_offer", 1)
	_report_achievement_snapshot()
	_update_all_labels()
	return {"ok": true, "kind": kind, "amount": amount, "cards": _dog_shrine_pending_card_data()}


func _on_dog_shrine_blessing_requested(blessing_id: String) -> void :
	if bdr.is_coop_client():
		bdr.coop_request("tarot_bless", [blessing_id])
		return
	var result: = _bdr_tarot_bless(blessing_id)
	if not bool(result.get("ok", false)):
		dog_shrine_controller.show_error(str(result.get("error", "")))
		return
	dog_shrine_controller.set_grimoire_cards(_dog_shrine_grimoire_data())
	dog_shrine_controller.play_blessing_success(blessing_id, _dog_shrine_inventory_items(), _dog_shrine_offerings_left())


## Takes a tarot card of the pending offer (used by the tarot screen and by the coop partner).
func _bdr_tarot_bless(blessing_id: String) -> Dictionary:
	if dog_shrine_entry_draining:
		return {"ok": false, "error": _dog_text("wait_rolls")}
	var choice: = _dog_shrine_pending_choice(blessing_id)
	if choice.is_empty() or blessing_id not in DOG_SHRINE_CARD_IDS:
		return {"ok": false, "error": _dog_text("save_failed")}
	var old_rank: = int(dog_shrine_blessing_ranks.get(blessing_id, 0))
	if old_rank >= MAX_INT64:
		return {"ok": false, "error": _dog_text("save_failed")}
	var old_pending: = pending_dog_shrine_offer.duplicate(true)
	var granted_rank: = _safe_add_int64(old_rank, 1)
	dog_shrine_blessing_ranks[blessing_id] = granted_rank
	pending_dog_shrine_offer.clear()
	if not _save_game(true):
		dog_shrine_blessing_ranks[blessing_id] = old_rank
		pending_dog_shrine_offer = old_pending
		return {"ok": false, "error": ""}
	_apply_dog_card_side_effect(blessing_id, old_rank)
	bdr.tarot.on_card_gained(blessing_id, old_rank)
	_save_game(true)
	_report_achievement_snapshot()
	_update_all_labels()
	return {"ok": true, "id": blessing_id}


func _dog_shrine_save_data() -> Dictionary:
	var donated: = {}
	for kind in DOG_SHRINE_DICE_KINDS:
		donated[kind] = str(maxi(0, int(dog_shrine_donated_counts.get(kind, 0))))
	for kind in dog_shrine_donated_counts:
		if bdr.is_custom(str(kind)) and int(dog_shrine_donated_counts[kind]) > 0:
			donated[str(kind)] = str(int(dog_shrine_donated_counts[kind]))
	var ranks: = {}
	for card_id in DOG_SHRINE_CARD_IDS:
		ranks[card_id] = str(maxi(0, int(dog_shrine_blessing_ranks.get(card_id, 0))))
	var die_bonuses: = {}
	for kind in DOG_SHRINE_DICE_KINDS:
		die_bonuses[kind] = clampi(int(dog_shrine_die_bonus_percent.get(kind, 0)), 0, DogShrineCards.COMMON_DIE_BONUS_CAP)
	return {
		"schema_version": 4,
		"transaction_id": str(dog_shrine_transaction_id),
		"donated_counts": donated,
		"offerings_made": str(maxi(0, dog_shrine_offerings_made)),
		"blessing_ranks": ranks,
		"die_bonus_percent": die_bonuses,
		"legacy_talents_migrated": dog_shrine_legacy_talents_migrated,
		"pending_offer": pending_dog_shrine_offer.duplicate(true),
	}


func _load_dog_shrine_save_data(value: Variant) -> void :
	dog_shrine_legacy_talents_migrated = false
	pending_dog_shrine_offer.clear()
	if value is not Dictionary:
		return
	var shrine_data: Dictionary = value
	var schema_version: = maxi(1, int(shrine_data.get("schema_version", 1)))
	dog_shrine_legacy_talents_migrated = bool(shrine_data.get("legacy_talents_migrated", false))
	dog_shrine_transaction_id = maxi(0, int(str(shrine_data.get("transaction_id", "0"))))
	dog_shrine_blessing_ranks = DogShrineCards.empty_ranks()
	for alias_id in dog_shrine_legacy_alias_ranks:
		dog_shrine_legacy_alias_ranks[alias_id] = 0
	var ranks_value = shrine_data.get("blessing_ranks", {})
	if ranks_value is Dictionary:
		for card_id in DOG_SHRINE_CARD_IDS:
			dog_shrine_blessing_ranks[card_id] = _dog_parse_nonnegative_int64(ranks_value.get(card_id, 0))
		for legacy_id in DogShrineCards.LEGACY_DOG_ALIASES:
			if not ranks_value.has(legacy_id):
				continue
			var old_rank: = _dog_parse_nonnegative_int64(ranks_value.get(legacy_id, 0))
			if legacy_id in dog_shrine_legacy_alias_ranks:
				dog_shrine_legacy_alias_ranks[legacy_id] = old_rank
			if old_rank <= 0:
				continue
			var target_id: = str(DogShrineCards.LEGACY_DOG_ALIASES[legacy_id])
			if target_id in DOG_SHRINE_CARD_IDS:
				dog_shrine_blessing_ranks[target_id] = _safe_add_int64(int(dog_shrine_blessing_ranks.get(target_id, 0)), old_rank)
	var die_bonus_value = shrine_data.get("die_bonus_percent", {})
	for kind in DOG_SHRINE_DICE_KINDS:
		var bonus: = int(die_bonus_value.get(kind, 0)) if die_bonus_value is Dictionary else 0
		dog_shrine_die_bonus_percent[kind] = clampi(bonus, 0, DogShrineCards.COMMON_DIE_BONUS_CAP)
	var donated_value = shrine_data.get("donated_counts", {})
	var migrated_offerings: = 0
	for kind in DOG_SHRINE_DICE_KINDS:
		var donated_count: = _dog_parse_nonnegative_int64(donated_value.get(kind, "0")) if donated_value is Dictionary else 0
		dog_shrine_donated_counts[kind] = donated_count
		if schema_version < 3:
			migrated_offerings = _safe_add_int64(migrated_offerings, donated_count)
	if donated_value is Dictionary:
		for kind in donated_value:
			if bdr.is_custom(str(kind)):
				dog_shrine_donated_counts[str(kind)] = _dog_parse_nonnegative_int64(donated_value.get(kind, "0"))
	dog_shrine_offerings_made = migrated_offerings if schema_version < 3 else _dog_parse_nonnegative_int64(shrine_data.get("offerings_made", "0"))
	bdr.tarot.invalidate()
	var pending_value = shrine_data.get("pending_offer", {})
	if pending_value is not Dictionary or pending_value.is_empty():
		return
	var choices_value = pending_value.get("choices", [])
	if choices_value is not Array or choices_value.is_empty():
		return
	var donated_kind: = str(pending_value.get("donated_kind", ""))
	var choices: Array[Dictionary] = []
	var used_ids: Array[String] = []
	for choice_value in choices_value:
		var choice: = _dog_shrine_normalize_choice(choice_value, donated_kind)
		var card_id: = str(choice.get("id", ""))
		if card_id in DOG_SHRINE_CARD_IDS and card_id not in used_ids:
			choices.append(choice)
			used_ids.append(card_id)
	for candidate_value in DogShrineCards.TAROT_ORDER:
		if choices.size() >= 3:
			break
		var candidate: = str(candidate_value)
		if candidate in used_ids:
			continue
		choices.append({"id": candidate})
		used_ids.append(candidate)
	if choices.is_empty():
		return
	pending_dog_shrine_offer = {
		"transaction_id": str(pending_value.get("transaction_id", dog_shrine_transaction_id)),
		"donated_kind": donated_kind,
		"amount": int(pending_value.get("amount", 10)),
		"choices": choices,
	}


## Tarot shrine: the original game waits until no dice is rolling before the shrine can be used
## (and gives up after 30 s). On a crowded table something always rolls, so the running rolls are
## finished right away (they pay out normally) - the shrine opens within a frame or two.
func _bdr_drain_world_for_menu() -> void:
	var budget: = 500
	for die_value in active_roll_ids.values():
		if budget <= 0:
			return
		if is_instance_valid(die_value) and die_value.rolling:
			die_value.complete_roll_now()
			budget -= 1
	if active_roll_ids.is_empty() and active_roll_count > 0:
		_synchronize_active_roll_count()
