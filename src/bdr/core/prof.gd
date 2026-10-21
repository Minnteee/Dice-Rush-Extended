extends RefCounted
## Lightweight profiling accumulators (enabled only when BDR_PROFILE is set).

static var enabled := OS.get_environment("BDR_PROFILE") == "1"
static var totals: Dictionary = {}
static var counts: Dictionary = {}
static var _starts: Dictionary = {}


static func begin(key: String) -> int:
	return Time.get_ticks_usec() if enabled else 0


static func end(key: String, started: int) -> void:
	if not enabled:
		return
	totals[key] = int(totals.get(key, 0)) + (Time.get_ticks_usec() - started)
	counts[key] = int(counts.get(key, 0)) + 1


static func snapshot_and_reset() -> Dictionary:
	var out := {}
	for key in totals:
		out[key] = {"ms": float(totals[key]) / 1000.0, "n": counts.get(key, 0)}
	totals.clear()
	counts.clear()
	return out
