"""Sanity simulation of the Fibonacci vs random ratios test on two synthetic series.

Standard library only. Run with:  python -I tools/simulate_fib_vs_random.py

Two seeded series of 20,000 bars with open, high, low and close:

  (a) a geometric random walk without drift, the no-bias control: its pullbacks stop anywhere, so the
      Fibonacci levels should do about as well as random ratios and about half of the random sets should
      do as well as the levels or better;
  (b) a zigzag built from explicit legs, the positive control: an impulse, a retrace that stops at a
      Fibonacci depth plus a little noise (0.618 half of the time, one of the other four levels otherwise),
      then a continuation past the previous extreme. Here the levels should beat every random set.

For every bar the simulation does what the Pine script does on a confirmed bar, in the same order: it
confirms the pivot high and the pivot low of the bar LEN bars back (the high first, then the low), keeps
the pivots alternating (a pivot of the same type as the last kept one replaces it when more extreme and is
ignored otherwise), and when a kept pivot is appended as the third one it measures the pullback it ends:
depth = pullback / leg. A leg of zero or negative height or a depth <= 0 is skipped, a depth >= 1 is a full
retrace, a depth in (0, 1) is a pullback and enters the hit test against the Fibonacci levels and against K
sets of random ratios in [0.2, 0.8]. The random ratios come from the same linear congruential generator as
the Pine script, state = (1103515245 * state + 12345) % 2^31 and u = state / 2^31; the u of a set are sorted
and spread as ratio j = 0.2 + span * u_j + j * gap, with gap = 2 * TOL and span = 0.6 - (M - 1) * gap, so no
two windows of a set overlap, as no two windows of the levels do. The same seed gives the same sets here and
on the chart.

Printed for both series, with the labels of the Pine table: pullbacks, full retraces and bars counted;
Fibonacci hits, rate and 95% confidence interval; the random sets' mean, lowest and highest rate; how many
random sets did as well as the levels or better, with the verdict; the difference in percentage points and
the uniform reference; the depth distribution; the last pullback. The last lines state the expected sign of
each result and what was observed.
"""

import math
import random

SEED = 7
LEN = 10  # pivot length, bars on each side
TOL = 0.02  # tolerance of the hit test
FIB = [0.236, 0.382, 0.5, 0.618, 0.786]
SETS = 20  # K random sets
BARS = 20000
STEPS = 12  # intrabar steps that build the high and the low of a random-walk bar
WICK = 0.0002  # relative wick of a turning bar of the zigzag, so two pivot extremes never tie
# Where a zigzag retrace stops, as (level, weight): 0.618 half of the time, the other levels the rest.
LEVEL_WEIGHTS = [(0.618, 0.5), (0.5, 0.15), (0.382, 0.15), (0.786, 0.1), (0.236, 0.1)]
DEPTH_NOISE = 0.01  # standard deviation of the noise added to the target depth


def lcg_sets(seed, sets, size, tol):
    """K sets of `size` ratios in [0.2, 0.8], at least 2 * tol apart, from the Pine script's generator: same seed, same ratios."""
    state = seed
    gap = 2 * tol
    span = 0.6 - (size - 1) * gap
    out = []
    for _ in range(sets):
        u = []
        for _ in range(size):
            prev = state
            state = (1103515245 * prev + 12345) % 2147483648
            # The Pine script takes the product in two parts that stay below 2^53; both forms must agree.
            assert state == (((16838 * prev) % 32768) * 65536 + 20077 * prev + 12345) % 2147483648
            u.append(state / 2147483648.0)
        u.sort()
        out.append([0.2 + span * u[j] + j * gap for j in range(size)])
    return out


def make_walk(seed, bars):
    """(open, high, low, close) bars of a geometric random walk without drift; each bar opens at the previous close."""
    rng = random.Random(seed)
    out = []
    price = 100.0
    sigma = 0.005
    for _ in range(bars):
        o = price
        path = [o]
        for _ in range(STEPS):
            price *= math.exp(sigma / math.sqrt(STEPS) * rng.gauss(0.0, 1.0))
            path.append(price)
        out.append((o, max(path), min(path), price))
    return out


def segment(start, end, m, rng):
    """m bars that move from the close `start` to the extreme `end` with random step sizes, monotonically.

    The last bar reaches `end` as its high (up) or low (down) and closes a wick short of it, so the turning
    bar is the strict extreme and the next bar, which opens at that close, cannot tie it.
    """
    up = end > start
    last_close = end / (1 + WICK) if up else end * (1 + WICK)
    weights = [rng.uniform(0.5, 1.5) for _ in range(m)]
    total = sum(weights)
    bars = []
    prev = start
    acc = 0.0
    for i, w in enumerate(weights):
        acc += w
        c = last_close if i == m - 1 else start + (last_close - start) * acc / total
        h, l = max(prev, c), min(prev, c)
        if i == m - 1:
            if up:
                h = end
            else:
                l = end
        bars.append((prev, h, l, c))
        prev = c
    return bars


def make_zigzag(seed, bars):
    """Explicit legs: an impulse, a retrace to a Fibonacci depth of the leg, a continuation past the last extreme.

    The trend turns every few legs. On a turn the next impulse runs the other way past the start of the leg
    that just ended, so the last retrace end never becomes a pivot and the leg the next pullback is measured
    on starts at the last extreme, as the pivot logic will see it.
    """
    rng = random.Random(seed)
    levels = [lv for lv, _ in LEVEL_WEIGHTS]
    weights = [w for _, w in LEVEL_WEIGHTS]
    out = []
    price = 100.0  # current close
    leg_start = price  # the kept pivot the next leg is measured from
    prev_extreme = None  # the extreme the next impulse must pass, so the retrace before it reads as a full retrace
    direction = 1
    legs_to_turn = rng.randint(4, 9)
    while len(out) < bars:
        end = price + direction * price * rng.uniform(0.03, 0.08)
        if prev_extreme is not None:
            end = max(end, prev_extreme * 1.005) if direction == 1 else min(end, prev_extreme * 0.995)
        out += segment(price, end, rng.randint(LEN + 2, 3 * LEN), rng)
        leg = abs(end - leg_start)
        depth = min(max(rng.choices(levels, weights)[0] + rng.gauss(0.0, DEPTH_NOISE), 0.05), 0.95)
        retrace_end = end - direction * depth * leg
        out += segment(out[-1][3], retrace_end, rng.randint(LEN + 2, 2 * LEN), rng)
        price = out[-1][3]
        legs_to_turn -= 1
        if legs_to_turn == 0:
            direction = -direction
            prev_extreme = leg_start
            leg_start = end
            legs_to_turn = rng.randint(4, 9)
        else:
            prev_extreme = end
            leg_start = retrace_end
    return out[:bars]


def pivots(bars, i):
    """The pivot high and pivot low that confirm on bar i: the bar LEN back is the strict extreme on both sides."""
    c = i - LEN
    if c < LEN:
        return None, None
    window = bars[c - LEN:c + LEN + 1]
    ph = window[LEN][1] if all(b[1] < window[LEN][1] for j, b in enumerate(window) if j != LEN) else None
    pl = window[LEN][2] if all(b[2] > window[LEN][2] for j, b in enumerate(window) if j != LEN) else None
    return ph, pl


def rate(n, total):
    """Same template as fmtRate() in the Pine script ("0.0" and a percent sign)."""
    return f"{100.0 * n / total:.1f}%" if total else "n/a"


def simulate(name, bars, rand_sets):
    kept = []  # [type, price, bar] of the last three kept pivots, oldest first
    n_bars = pullbacks = full = fib_hits = 0
    rand_hits = [0] * len(rand_sets)
    bins = [0] * 5
    last = None  # (depth, fib hit, bar) of the last pullback

    def add_pivot(typ, price, bar):
        if kept and kept[-1][0] == typ:
            if (typ == 1 and price > kept[-1][1]) or (typ == -1 and price < kept[-1][1]):
                kept[-1][1:] = [price, bar]
            return False
        kept.append([typ, price, bar])
        if len(kept) > 3:
            del kept[0]
        return True

    for i in range(len(bars)):
        n_bars += 1
        ph, pl = pivots(bars, i)
        for typ, pv in ((1, ph), (-1, pl)):
            if pv is None or not add_pivot(typ, pv, i - LEN) or len(kept) < 3:
                continue
            up_leg = kept[0][0] == -1
            p0, p1, p2 = kept[0][1], kept[1][1], kept[2][1]
            leg = p1 - p0 if up_leg else p0 - p1
            pull = p1 - p2 if up_leg else p2 - p1
            if leg <= 0:
                continue
            depth = pull / leg
            if depth >= 1:
                full += 1
            elif depth > 0:
                pullbacks += 1
                fib = any(abs(depth - lv) <= TOL for lv in FIB)
                fib_hits += fib
                for k, ratios in enumerate(rand_sets):
                    rand_hits[k] += any(abs(depth - r) <= TOL for r in ratios)
                bins[min(int(depth * 5), 4)] += 1
                last = (depth, fib, i - LEN)

    n = pullbacks
    fib_rate = fib_hits / n
    half = 1.96 * math.sqrt(fib_rate * (1 - fib_rate) / n)
    rates = [h / n for h in rand_hits]
    mean_rate = sum(rates) / len(rates)
    sets_ge = sum(h >= fib_hits for h in rand_hits)
    share_ge = sets_ge / len(rand_sets)
    verdict = "fib not special" if share_ge >= 0.1 else "fib ahead" if share_ge < 0.05 else "borderline"
    if n < 30:
        verdict += " (small sample)"
    uniform_ref = min(len(FIB) * 2 * TOL / 0.6, 1.0)
    print(f"{name}  ({n_bars} bars, seed {SEED}, pivot length {LEN}, tolerance {TOL}, levels on {' '.join(str(lv) for lv in FIB)})")
    print(f"  Pullbacks               {n} pullbacks   {full} full retraces   {n_bars} bars counted")
    print(f"  Fib hits                {fib_hits} hits   rate {rate(fib_hits, n)}   "
          f"95% CI {100 * max(fib_rate - half, 0):.1f}% - {100 * min(fib_rate + half, 1):.1f}%")
    print(f"  Random ratios           {len(rand_sets)} sets of {len(FIB)} ratios   mean rate {100 * mean_rate:.1f}%   "
          f"min {100 * min(rates):.1f}%   max {100 * max(rates):.1f}%")
    print(f"  Random sets >= fib      {sets_ge} of {len(rand_sets)}   {verdict}")
    print(f"  Difference              fib - random mean {100 * (fib_rate - mean_rate):+.1f} pts   uniform reference {100 * uniform_ref:.1f}%")
    print(f"  Depth distribution      0-0.2 {rate(bins[0], n)}   0.2-0.4 {rate(bins[1], n)}   0.4-0.6 {rate(bins[2], n)}   "
          f"0.6-0.8 {rate(bins[3], n)}   0.8-1 {rate(bins[4], n)}")
    print(f"  Last pullback           depth {last[0]:.2f}   fib hit {'yes' if last[1] else 'no'}   bar {last[2]}")
    print()
    return fib_rate, mean_rate, max(rates), sets_ge


def main():
    rand_sets = lcg_sets(SEED, SETS, len(FIB), TOL)
    print(f"Random sets: {SETS} sets of {len(FIB)} ratios in [0.2, 0.8], at least {2 * TOL:g} apart, from the LCG with seed {SEED}; "
          f"set 0 is {' '.join(f'{r:.3f}' for r in rand_sets[0])}\n")
    walk = simulate("Random walk", make_walk(SEED, BARS), rand_sets)
    zig = simulate("Zigzag with Fibonacci retraces", make_zigzag(SEED, BARS), rand_sets)
    print("Expected sign: on the random walk the Fibonacci rate sits within a few points of the random mean and "
          "about half of the random sets do as well or better. "
          f"Observed: fib {100 * walk[0]:.1f}% vs random mean {100 * walk[1]:.1f}%, {walk[3]} of {SETS} sets.")
    print("Expected sign: on the zigzag the Fibonacci rate beats every random set, so 0 sets do as well. "
          f"Observed: fib {100 * zig[0]:.1f}% vs best random set {100 * zig[2]:.1f}%, {zig[3]} of {SETS} sets.")


if __name__ == "__main__":
    main()
