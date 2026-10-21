# Dice Rush Extended - main.gd patch: prehistoric waves that can never get stuck.
# The game waits for "no wave work" before the tarot shrine opens (and for some saves). A wave
# counts every dice it is going to roll and waits until each one landed. In the original a target
# that could not start its roll (in the mod e.g. a racing car that was just driving) was counted but
# never finished, so the wave stayed open forever - and the tarot shrine always gave up after 30 s.

## A wave (or a batch of prehistoric dice) without any progress for this long is treated as done.
const BDR_WAVE_STALE_MSEC: = 10000

var _bdr_root_batch_msec: Dictionary = {}


func _launch_wave_target_after_delay(target: DiceActor, chain_id: int, delay: float) -> void :
	# while the tarot shrine opens or is open, wave targets do not roll (the table has to calm down)
	if delay > 0.0 and not bdr.world_frozen_for_menu():
		await get_tree().create_timer(delay).timeout
	if qa_stress_draining or bdr.world_frozen_for_menu() or not is_instance_valid(target) or target.rolling:
		_finish_wave_roll(chain_id)
		return
	_start_die_roll(target, chain_id, Vector2(-1.0, -1.0), true, true)
	if not is_instance_valid(target) or not target.rolling:
		# the roll did not start (moving vehicle, cat, menu ...): count it as finished
		_finish_wave_roll(chain_id)


func _finish_wave_roll(chain_id: int) -> void :
	if not wave_chains.has(chain_id):
		return
	var state: Dictionary = wave_chains[chain_id]
	state.active = int(state.active) - 1
	state["bdr_touch"] = Time.get_ticks_msec()
	if int(state.active) <= 0:
		state.active = 0
		wave_chains[chain_id] = state
		_expire_idle_wave_chain_after_grace(chain_id)
	else:
		wave_chains[chain_id] = state
	_finish_pending_safe_action()
	_finish_pending_autosave()


func _has_pending_wave_work() -> bool:
	var now: = Time.get_ticks_msec()
	if not prehistoric_root_batch_remaining.is_empty():
		for batch in prehistoric_root_batch_remaining.keys():
			if now - int(_bdr_root_batch_msec.get(batch, now)) > BDR_WAVE_STALE_MSEC:
				# a prehistoric dice of this batch never landed (sold, offered ...): forget the batch
				prehistoric_root_batch_remaining.erase(batch)
				prehistoric_root_batch_chains.erase(batch)
				_bdr_root_batch_msec.erase(batch)
		if not prehistoric_root_batch_remaining.is_empty():
			return true
	for chain_id in wave_chains.keys():
		var state_value = wave_chains[chain_id]
		if state_value is not Dictionary or int(state_value.get("active", 0)) <= 0:
			continue
		if now - int(state_value.get("bdr_touch", now)) > BDR_WAVE_STALE_MSEC:
			state_value["active"] = 0
			wave_chains[chain_id] = state_value
			_expire_idle_wave_chain_after_grace(chain_id)
			continue
		return true
	return false


## Tarot shrine: nothing rolls any more and wave targets do not roll while it opens, so every open
## wave and prehistoric root batch is finished right away.
func _bdr_close_open_waves() -> void:
	for chain_id in wave_chains.keys():
		var state_value = wave_chains[chain_id]
		if state_value is Dictionary and int(state_value.get("active", 0)) > 0:
			state_value["active"] = 0
			wave_chains[chain_id] = state_value
			_expire_idle_wave_chain_after_grace(chain_id)
	prehistoric_root_batch_remaining.clear()
	prehistoric_root_batch_chains.clear()
	_bdr_root_batch_msec.clear()
