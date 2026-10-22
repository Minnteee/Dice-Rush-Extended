extends RefCounted
## Dice Shaker (copy of the Dice Rush Extended number format) - short number format: 1, 10, 100, 1K, 1.1K, 10K, 100K, 1M, 1.1M, 1B ...
## Never "e" notation. After d (10^33) the suffixes go on with two letters like idle games:
## aa = 10^36, ab = 10^39, ... az, ba, ... (enough for the 10^300 money cap).

## Octillion is a small "o": a capital "O" looks exactly like a zero in the game's pixel font.
const SUFFIXES := ["", "K", "M", "B", "T", "q", "Q", "s", "S", "o", "N", "d"]


## Suffix for 1000^group (group 1 = K, 12 = aa, 13 = ab ...).
static func suffix_for(group: int) -> String:
	if group < SUFFIXES.size():
		return SUFFIXES[maxi(0, group)]
	var index := group - SUFFIXES.size()
	return char(97 + (index / 26) % 26) + char(97 + index % 26)


static func compact(value: Variant) -> String:
	var number := 0.0
	if value is String:
		var raw := (value as String).strip_edges()
		if raw.is_empty():
			return "0"
		if not raw.is_valid_float():
			return raw
		number = raw.to_float()
	elif value is int or value is float or value is bool:
		number = float(value)
	else:
		return str(value)
	if is_nan(number):
		return "0"
	var sign := ""
	if number < 0.0:
		sign = "-"
		number = -number
	if is_inf(number) or number >= 1.0e306:
		return sign + "∞"
	if number < 1000.0:
		# small values: whole numbers; one decimal only for fractions below 100 (x1.5, 12.5)
		if number < 100.0 and absf(number - floorf(number + 0.0000001)) >= 0.05:
			return sign + ("%.1f" % (floorf(number * 10.0 + 0.0000001) / 10.0)).trim_suffix(".0")
		return sign + str(int(floorf(number + 0.0000001)))
	var group := int(floor(log(number) / log(1000.0) + 0.000000001))
	group = maxi(1, group)
	var scaled := number / pow(1000.0, group)
	if scaled < 1.0:
		# floating point edge right below a power of 1000
		group -= 1
		scaled *= 1000.0
	var text := ""
	if scaled >= 99.95:
		var whole := int(roundf(scaled))
		if whole >= 1000:
			group += 1
			text = "1"
		else:
			text = str(whole)
	else:
		text = ("%.1f" % scaled).trim_suffix(".0")
	return sign + text + suffix_for(group)
