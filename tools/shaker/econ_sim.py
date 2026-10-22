"""Dice Shaker balance simulation: a player who plays in sessions (clicking) with idle breaks
(auto-shake only) and spends money with simple rules. Prints when the important milestones happen.

usage: python econ_sim.py [hours] [seed]
"""
import collections
import random
import sys

import shaker_design as D
import shaker_rules as R

B = D.BALANCE
CLICK_RATE_MAX = 3.0        # a human clicks at most ~3 times per second
ACTIVE_MINUTES = 6.0        # play actively ...
IDLE_MINUTES = 4.0          # ... then look away for a while (auto-shake only)


def fmt(value):
    if value < 1000:
        return "%.0f" % value
    suffixes = ["", "K", "M", "B", "T", "q", "Q", "s", "S", "o", "N", "d"]
    group = 0
    while value >= 1000 and group < 40:
        value /= 1000.0
        group += 1
    suffix = suffixes[group] if group < len(suffixes) else "e%d" % (group * 3)
    return "%.1f%s" % (value, suffix)


def hms(seconds):
    return "%d:%02d" % (seconds // 3600, (seconds % 3600) // 60)


class Sim:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.s = R.new_state()
        self.stats = R.compute_stats(self.s)
        self.t = 0.0
        self.last_shake = -99.0
        self.earned = collections.deque()
        self.ips = 0.0
        self.events = []
        self.marks = set()
        self.next_market = 0.0
        self.spent = collections.Counter()

    def mark(self, key, text):
        if key in self.marks:
            return
        self.marks.add(key)
        self.events.append((self.t, text))

    def refresh(self):
        self.stats = R.compute_stats(self.s)

    # ---------------------------------------------------------------- spending rules
    def try_talents(self):
        bought = False
        choices = []
        for tid in R.TALENTS:
            if not R.talent_available(self.s, tid):
                continue
            tp, money = R.talent_cost(self.s, self.stats, tid)
            slot = "slots" in dict(R.TALENTS[tid]["effects"])
            choices.append((0 if slot else 1, money, tp, tid))
        choices.sort()
        for _prio, money, tp, tid in choices:
            if tp <= self.s["tp"] and money <= self.s["money"]:
                self.s["tp"] -= tp
                self.s["money"] -= money
                self.spent["talents"] += money
                self.s["talents"].add(tid)
                if "slots" in dict(R.TALENTS[tid]["effects"]):
                    die = {"id": self.rng.choice(R.DICE_BY_RARITY["common"])["id"], "level": 1, "xp": 0.0}
                    self.s["dice"].append(die)
                    self.s["discovered"].add(die["id"])
                    self.mark("dice%d" % len(self.s["dice"]), "%d dice" % len(self.s["dice"]))
                if tid == "compact":
                    self.mark("compact", "compact dice")
                if tid == "black1":
                    self.mark("black", "black market unlocked")
                if tid.startswith("auto"):
                    self.mark(tid, tid)
                self.refresh()
                bought = True
                break
        return bought

    def needed_tp(self):
        best = None
        for tid in R.TALENTS:
            if R.talent_available(self.s, tid):
                tp, money = R.talent_cost(self.s, self.stats, tid)
                if best is None or money < best[1]:
                    best = (tp, money)
        return best

    def try_gumball(self):
        price = R.gumball_price(self.s, self.stats)
        need = self.needed_tp()
        want = need is not None and need[0] > self.s["tp"] and need[1] <= self.s["money"] + self.ips * 120
        if price <= self.s["money"] and (price <= 0.30 * self.s["money"] or (want and price <= 0.8 * self.s["money"])):
            self.s["money"] -= price
            self.spent["gumball"] += price
            self.s["gumballs"] += 1
            balls = 2 if self.rng.random() * 100.0 < self.stats["double_ball"] else 1
            for _ in range(balls):
                tp, _c = R.roll_gumball(self.stats, self.rng)
                self.s["tp"] += tp
            return True
        return False

    def try_lucky(self):
        avg = {r: sum(d["pay"] for d in R.DICE_BY_RARITY[r]) / len(R.DICE_BY_RARITY[r]) for r in D.RARITIES}
        best = None
        for tier in range(5):
            odds = R.lucky_odds(self.stats, tier)
            expected = sum(o / 100.0 * avg[r] for o, r in zip(odds, D.RARITIES))
            roll = [d for d in self.s["dice"] if expected > 1.3 * R.DICE[d["id"]]["pay"]]
            if not roll:
                continue
            gain = sum((expected - R.DICE[d["id"]]["pay"]) * R.level_mult(d["level"]) for d in roll)
            price = R.lucky_price(self.s, self.stats, tier, len(roll))
            if price > 0.5 * self.s["money"]:
                continue
            score = gain / price
            if best is None or score > best[4]:
                best = (tier, roll, price, odds, score)
        if best is None:
            return False
        tier, roll, price, odds, _score = best
        self.s["money"] -= price
        self.spent["lucky"] += price
        self.s["lucky_rolled"][tier] += len(roll)
        for die in roll:
            r = self.rng.random() * 100.0
            rarity = 0
            for i, o in enumerate(odds):
                r -= o
                if r <= 0:
                    rarity = i
                    break
            new = self.rng.choice(R.DICE_BY_RARITY[D.RARITIES[rarity]])
            die["id"] = new["id"]
            die["level"] = min(B["max_level"], die["level"] + int(self.stats["reroll_levels"]))
            die["grow"] = 0
            self.s["discovered"].add(new["id"])
            self.mark("first_" + new["rarity"], "first " + new["rarity"])
        ranks = [R.RARITY_INDEX[R.DICE[d["id"]]["rarity"]] for d in self.s["dice"]]
        if len(ranks) == 12 and min(ranks) >= 3:
            self.mark("all_epic", "12 dice epic+")
        if len(ranks) == 12 and min(ranks) == 4:
            self.mark("all_legendary", "12 dice legendary")
        self.refresh()
        return True

    def try_tarot(self):
        price = R.tarot_price(self.s, self.stats)
        open_cards = [c for c in R.TAROT if self.s["tarot"].get(c, 0) < 4]
        if not open_cards or price > 0.2 * self.s["money"]:
            return False
        self.s["money"] -= price
        self.spent["tarot"] += price
        self.s["tarot_draws"] += 1
        choices = self.rng.sample(open_cards, min(len(open_cards), D.TAROT_DRAW["choices"] + int(self.stats["tarot_choices"])))
        order = ["crystal_ball", "anchor", "serpent", "raven", "phoenix", "comet", "third_eye", "tower", "open_hand",
                 "moon_moth", "lotus", "crown", "chalice", "star", "sun", "lantern", "hourglass", "candle", "bell", "dagger",
                 "mirror", "wheel", "key", "coin", "spider", "mask", "cauldron", "owl", "fox", "feather"]
        choices.sort(key=lambda c: order.index(c))
        card = choices[0]
        self.s["tarot"][card] = self.s["tarot"].get(card, 0) + 1
        if all(self.s["tarot"].get(c, 0) >= 4 for c in R.TAROT):
            self.mark("tarot_done", "all tarot legendary")
        self.refresh()
        return True

    def try_gauntlet(self):
        nxt = len(self.s["gauntlets"]) + 1
        if nxt > 30:
            return False
        price = R.gauntlet_price(self.stats, nxt)
        if price > 0.2 * self.s["money"]:
            return False
        self.s["money"] -= price
        self.spent["gauntlets"] += price
        self.s["gauntlets"].add(nxt)
        self.s["gauntlet"] = nxt
        if nxt in (10, 20, 30):
            self.mark("gauntlet%d" % nxt, "gauntlet %d" % nxt)
        self.refresh()
        return True

    def try_black(self):
        if self.stats["black_market"] <= 0:
            return False
        options = []
        for bid, b in R.BLACK.items():
            if self.s["black"].get(bid, 0) < b["cap"]:
                options.append((R.black_price(self.s, self.stats, bid), bid))
        if not options:
            self.mark("black_done", "black market complete")
            return False
        price, bid = min(options)
        if price > 0.2 * self.s["money"]:
            return False
        self.s["money"] -= price
        self.spent["black"] += price
        self.s["black"][bid] = self.s["black"].get(bid, 0) + 1
        self.refresh()
        return True

    def spend(self):
        for _ in range(60):
            if not (self.try_talents() or self.try_gumball() or self.try_lucky() or self.try_tarot()
                    or self.try_gauntlet() or self.try_black()):
                break

    # ---------------------------------------------------------------- time
    def run(self, hours):
        report_at = 0.0
        next_spend = 0.0
        while self.t < hours * 3600:
            cycle = (self.t / 60.0) % (ACTIVE_MINUTES + IDLE_MINUTES)
            active = cycle < ACTIVE_MINUTES
            st = R.shake_time(self.stats)
            auto = R.auto_interval(self.stats)
            if active:
                dt = max(st, 1.0 / CLICK_RATE_MAX)
                manual = True
            elif auto > 0:
                dt = auto
                manual = False
            else:
                self.t += 1.0
                self.s["streak"] = 0
                continue
            if self.t - self.last_shake <= B["streak_window"] + 1e-9:
                self.s["streak"] += 1
            else:
                self.s["streak"] = 0
            if self.t >= self.next_market:
                self.next_market = self.t + B["market_period"]
                for die in self.s["dice"]:
                    d = R.DICE[die["id"]]
                    if d["fx"] == "market":
                        die["market"] = self.rng.uniform(d["p"]["min"], d["p"]["max"])
            money, _info = R.shake(self.s, self.stats, self.rng, manual, self.ips)
            self.s["money"] = min(B["money_cap"], self.s["money"] + money)
            self.earned.append((self.t, money))
            while self.earned and self.earned[0][0] < self.t - 60.0:
                self.earned.popleft()
            self.ips = sum(m for _t, m in self.earned) / 60.0
            self.last_shake = self.t
            self.t += dt
            if self.t >= next_spend:
                next_spend = self.t + 2.0
                self.spend()
            if self.t >= report_at:
                report_at += 1800.0
                levels = [d["level"] for d in self.s["dice"]]
                rar = collections.Counter(R.DICE[d["id"]]["rarity"][0].upper() for d in self.s["dice"])
                print("%s  money %8s  income/s %8s  dice %2d  lv %3d-%3d  %s  tp %3d  talents %2d  tarot %3d  gaunt %2d  black %2d  gum %3d" % (
                    hms(self.t), fmt(self.s["money"]), fmt(self.ips), len(self.s["dice"]), min(levels), max(levels),
                    "".join("%s%d" % (k, rar[k]) for k in "CURE L".replace(" ", "") if rar[k]),
                    self.s["tp"], len(self.s["talents"]), sum(self.s["tarot"].values()), len(self.s["gauntlets"]),
                    sum(self.s["black"].values()), self.s["gumballs"]))
        print()
        for t, text in self.events:
            print("  %s  %s" % (hms(t), text))
        print("  spent:", {k: fmt(v) for k, v in self.spent.items()})
        print("  talents missing:", sorted(set(R.TALENTS) - self.s["talents"]))


if __name__ == "__main__":
    hours = float(sys.argv[1]) if len(sys.argv) > 1 else 12
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    Sim(seed).run(hours)
