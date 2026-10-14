# Fibonacci vs Random Ratios

Open-source TradingView indicator (Pine Script v6) that finds swings with pivot highs and lows, measures how deep each pullback went into the leg before it, and tests whether those depths land near the Fibonacci retracement levels (0.236, 0.382, 0.5, 0.618, 0.786) more often than near sets of ratios drawn at random, with the same tolerance.

Published on TradingView: not yet. Add the script URL here after publishing (see the checklist in `TRADINGVIEW_PUBLICATION.md`).

## What it measures

Many scripts draw the Fibonacci levels or report how often each one is reached. A hit rate alone has no baseline: with five levels and a tolerance of 0.02, any depth within 0.02 of one of them is a hit, a window of 0.2 in all, so a good share of pullbacks hit even when their depths are spread evenly over the leg, and a random walk touches every level by chance. The indicator keeps that baseline inside the measurement:

1. **Finds swings.** `ta.pivothigh(high, len, len)` and `ta.pivotlow(low, len, len)` with one pivot length `len` (default 10, minimum 2). A pivot confirms `len` bars after its bar; its price is `high[len]` or `low[len]`, its bar `bar_index - len`. Pivots are kept alternating: when a new pivot has the same type as the last kept one, it replaces it if it is more extreme (higher high, lower low) and is ignored otherwise. The last three kept pivots are stored (type, price, bar).
2. **Measures the pullback.** When a kept pivot is appended as the third one, the two before it define the leg and the new one is where the pullback stopped. Up leg L0 → H1, pullback to L2: `depth = (H1 - L2) / (H1 - L0)`. Down leg H0 → L1, pullback to H2: `depth = (H2 - L1) / (H0 - L1)`. A depth of 1 or more took the whole leg back: a full retrace, counted and kept out of the hit test. Legs of zero or negative height, and depths of zero or less, are skipped.
3. **Tests the depth.** A pullback is a Fibonacci hit when `|depth - level| <= tol` for any enabled level (tolerance 0.02 by default). The same test runs against K sets (20 by default) of M random ratios, M being the number of enabled levels, drawn at random in [0.2, 0.8] at least `2 * tol` apart; a set hits when any of its ratios is within the tolerance. The spacing keeps the windows of a set from overlapping, as the windows of the levels never do (their closest pair is 0.118 apart and the tolerance is at most 0.05), so every set covers the same width of depths as the levels, `M * 2 * tol`. The hit count of every set is kept.
4. **Reports.** On the last bar: pullbacks, full retraces, Fibonacci hits and rate with a 95% confidence interval, the random sets' mean, lowest and highest rate, how many random sets did as well as the levels or better, the difference in percentage points, the distribution of depths in five bins, and the last pullback.

The random ratios are generated once, on the first bar, by a linear congruential generator seeded by the `seed` input: `state = (1103515245 * state + 12345) % 2^31`, `u = state / 2^31`. Each set takes M values of `u`, sorts them and spreads them as `ratio_j = 0.2 + span * u_j + j * gap`, with `gap = 2 * tol` and `span = 0.6 - (M - 1) * gap`: every set of ratios in [0.2, 0.8] that keeps that spacing is equally likely. The same seed and tolerance give the same ratios on every chart, and `tools/simulate_fib_vs_random.py` reproduces them exactly. In the script the product is taken in two parts that each stay below 2^53 (`1103515245 = 16838 * 65536 + 20077`), so the result is exact whatever the width of Pine's int.

Why the spacing: with M independent uniform ratios, windows often overlap (at a tolerance of 0.02, about 4 in 5 random 5-ratio sets have at least one overlap, and their union covers 0.176 of the depths on average against 0.2 for the levels), so the random sets cover less and the levels win on a series with no Fibonacci bias at all. On 30 seeded random walks of 20,000 bars, independent ratios put the levels 2.4 points ahead on average and read "borderline" or "fib ahead" on 4 of them at a tolerance of 0.02, and on 28 of them at 0.05; with the spacing the gap is -0.4 points and no walk reads either. These figures come from a one-off variant of the simulation run during review (walk seeds 1 to 30, a different generator seed per walk); they are not printed by `tools/`.

## Counting rules

The counters update only on confirmed bars (`barstate.isconfirmed`), and only when a pivot confirms, in this order:

1. **Pivot confirmation.** On every confirmed bar the pivot high and the pivot low of the bar `len` bars back are read, the high first, then the low: a wide bar can be both. Each goes through the alternation rule above. Only an appended pivot ends a pullback; a replacement moves the last kept pivot and nothing is counted.
2. **Observation.** With three kept pivots, the depth is computed and sorted: skipped, full retrace, or pullback. A pullback updates: pullbacks, Fibonacci hits, the hit count of every random set that hits, the depth bin (`0-0.2`, `0.2-0.4`, `0.4-0.6`, `0.6-0.8`, `0.8-1`), and the "Last pullback" row (depth, Fibonacci hit, open time of the pivot bar).
3. **Labels.** A label is drawn at the pivot that ended the pullback with the depth ("0.62") and an F when it is a Fibonacci hit, orange for a hit and gray otherwise. The labels of the last N pullbacks are kept in a queue, the oldest is deleted beyond N, and N is capped at 100 (`max_labels_count = 100`).

Consequences:

- The realtime bar is never in the counts until it confirms, and a pivot is counted `len` bars after its bar, so the last `len` bars of the chart carry no observation yet.
- A pullback that deepens after its first pivot, with no pivot of the other type in between, is recorded at the first pivot; the deeper one replaces it as the start of the next leg and the recorded depth is not revised.
- Ties count against the levels: a random set with as many hits as the levels is "as well".
- No `request.*` call, no look-ahead, no recalculation of a count after its bar has closed.

## Statistics

- Fibonacci rate `p = hits / n` over the `n` pullbacks; 95% interval `p ± 1.96 * sqrt(p * (1 - p) / n)`, clipped to [0, 1] for display.
- Random sets: `rate_k = hits_k / n`; mean, lowest and highest over the K sets; `k` is the number of sets with `hits_k >= hits`. Verdict: `k / K >= 0.1` reads "fib not special", `k / K < 0.05` reads "fib ahead", between reads "borderline"; with fewer than 30 pullbacks the verdict adds "(small sample)". K is at least 20: "fib ahead" then needs 0 of K, which a set of levels no better than random sets reaches with a chance of at most 1 in 21 (`1 / (K + 1)`); with K = 5 that chance would be 1 in 6.
- Difference: `(p - mean) * 100`, in percentage points.
- Uniform reference: if depths were spread evenly over [0.2, 0.8], the range the random ratios are drawn from, each ratio would catch `2 * tol / 0.6` of them and M ratios about `M * 2 * tol / 0.6` (33.3% with the defaults), slightly less since a window near 0.2 or 0.8 reaches outside that range. The actual distribution of depths is in the table; on a random walk it leans deep (see the simulation below), so actual rates differ from the reference. The reference is a sanity check, not the baseline; the baseline is the random sets.

## Settings

| Input | Default | Meaning |
| --- | --- | --- |
| Pivot length | 10 | Bars on each side a pivot must exceed; a pivot confirms this many bars after its bar. Every number depends on it. |
| Tolerance | 0.02 | `\|depth - ratio\| <= tolerance` is a hit, for the levels and the random ratios alike. Step 0.005, range 0.005 to 0.05, so the windows of two levels never overlap. |
| 0.236, 0.382, 0.5, 0.618, 0.786 | all on | Levels in the Fibonacci set. Each random set has as many ratios as there are levels on. |
| Random sets K | 20 | Sets of random ratios, 20 to 50. |
| Seed | 7 | Seed of the generator. Same seed, same ratios on every chart. |
| Label the last N pullbacks | 30 | Labels at the pivots where the last N pullbacks stopped; 0 draws none, 100 at most. |
| Table position | Bottom right | Four corners. |
| Table text size | Small | Tiny, Small or Normal. |

## How to read the table

| Row | Meaning |
| --- | --- |
| Header | Symbol, timeframe, pivot length, tolerance, levels on. |
| Pullbacks | Pullbacks tested (depth in (0, 1)), full retraces (depth >= 1), confirmed bars counted. |
| Fib hits | Hits, rate, 95% confidence interval. |
| Random ratios | Sets and ratios per set, mean rate, lowest and highest rate. |
| Random sets >= fib | `k of K` sets with at least the Fibonacci hits, and the verdict; green only when the levels are ahead. |
| Difference | Fibonacci rate minus random mean in percentage points, and the uniform reference. |
| Depth distribution | Share of pullbacks in each fifth of the leg. |
| Last pullback | Depth, Fibonacci hit, open time of the pivot bar, for a hand check against the label. |

The footer reminds that the numbers are counts on confirmed pivots and names the timezone of the dates (`syminfo.timezone`). Rates are shown with one decimal, depths with two. With no level enabled the table says only "Enable at least one Fibonacci level".

## Files

- `fibonacci_vs_random.pine`: the indicator.
- `TRADINGVIEW_PUBLICATION.md`: title, description text and checklist for publishing.
- `tools/simulate_fib_vs_random.py`: standard-library Python simulation of the pivot logic, the hit test, the random sets (same generator and seed as the script) and the statistics on two seeded synthetic series of 20,000 bars (`python -I tools/simulate_fib_vs_random.py`): a geometric random walk, where the levels should do no better than random, and a zigzag built from explicit legs whose retraces stop at Fibonacci depths, where they should beat every random set.
- `LICENSE`: MIT.

## Check it yourself

1. Add the indicator to BINANCE:BTCUSDT on 1 hour from the Pine Editor and confirm it compiles without errors or warnings.
2. Check the identities: `Fib hits <= pullbacks`; `k <= K` in "Random sets >= fib"; the five depth shares sum to 100% up to rounding; the random mean lies between the min and the max shown.
3. Hand check one labeled pullback: with the cursor, read the first pivot, the second pivot and the labeled pivot; the depth is the pullback (second pivot to labeled pivot) over the leg (first pivot to second pivot) and must match the label at two decimals.
4. Set the tolerance to 0.05 with all five levels on: the Fibonacci rate and the random mean must both rise by about the same amount, since both sets of windows widen by the same width (on the simulated random walk, 23.9% and 23.4% at 0.02 become 58.4% and 57.1%).
5. Set K to 50 and change the seed a few times: the random mean must stay about the same while the min and the max move.
6. Compare with `tools/simulate_fib_vs_random.py`. The symbol differs, so the numbers will too; what should carry over on a real chart is the shape of the random walk result: a Fibonacci rate within a few points of the random mean, and a good share of the random sets doing as well or better. Output on 2026-10-14:

```
Random sets: 20 sets of 5 ratios in [0.2, 0.8], at least 0.04 apart, from the LCG with seed 7; set 0 is 0.332 0.386 0.543 0.624 0.797

Random walk  (20000 bars, seed 7, pivot length 10, tolerance 0.02, levels on 0.236 0.382 0.5 0.618 0.786)
  Pullbacks               485 pullbacks   416 full retraces   20000 bars counted
  Fib hits                116 hits   rate 23.9%   95% CI 20.1% - 27.7%
  Random ratios           20 sets of 5 ratios   mean rate 23.4%   min 18.6%   max 29.9%
  Random sets >= fib      8 of 20   fib not special
  Difference              fib - random mean +0.5 pts   uniform reference 33.3%
  Depth distribution      0-0.2 2.1%   0.2-0.4 12.2%   0.4-0.6 27.8%   0.6-0.8 32.4%   0.8-1 25.6%
  Last pullback           depth 0.81   fib hit no   bar 19986

Zigzag with Fibonacci retraces  (20000 bars, seed 7, pivot length 10, tolerance 0.02, levels on 0.236 0.382 0.5 0.618 0.786)
  Pullbacks               459 pullbacks   544 full retraces   20000 bars counted
  Fib hits                429 hits   rate 93.5%   95% CI 91.2% - 95.7%
  Random ratios           20 sets of 5 ratios   mean rate 30.7%   min 5.2%   max 68.6%
  Random sets >= fib      0 of 20   fib ahead
  Difference              fib - random mean +62.8 pts   uniform reference 33.3%
  Depth distribution      0-0.2 0.0%   0.2-0.4 24.8%   0.4-0.6 17.9%   0.6-0.8 56.6%   0.8-1 0.7%
  Last pullback           depth 0.79   fib hit yes   bar 19957

Expected sign: on the random walk the Fibonacci rate sits within a few points of the random mean and about half of the random sets do as well or better. Observed: fib 23.9% vs random mean 23.4%, 8 of 20 sets.
Expected sign: on the zigzag the Fibonacci rate beats every random set, so 0 sets do as well. Observed: fib 93.5% vs best random set 68.6%, 0 of 20 sets.
```

Two things to notice in the output. The random walk's depths lean deep (58% of the pullbacks are deeper than 0.6), so both the Fibonacci rate and the random rates sit below the uniform reference of 33.3%; the baseline absorbs that, the reference does not. On the zigzag the best random set reaches 68.6% because it happens to hold ratios near 0.618 and 0.5, where most of the shaped retraces stop; it still falls short of the five levels together, which is what "0 of 20" records.

Result on TradingView: not yet run. Add the figures here after the first compile, as the publishing checklist says.

## Limitations

- The pivot length defines the swings, and a different length changes every number, the verdict included. There is no right length; the test is conditional on the one chosen.
- The tolerance drives the base rate for the levels and the random ratios alike; a wide tolerance makes almost everything a hit for both.
- The random sets are spaced so their windows never overlap, which gives them the same coverage as the levels. With a wide tolerance that spacing leaves the ratios little room (at 0.05, five ratios at least 0.1 apart in a range of 0.6), so the random sets come close to evenly spaced lines and the test compares the levels with those.
- The test says nothing about what price does after a touch; it measures where pullbacks stopped, not what followed.
- A random walk produces touches at every level by chance; that is exactly what the random baseline measures, and the levels have to beat it.
- Only bars loaded on the chart are counted, so history depth, symbol and timeframe change every number.
- The simulation's zigzag is a constructed positive control, not a market: its retraces stop at 0.618 half of the time and at one of the other four levels otherwise, with a little noise, so the levels are meant to win there. The random walk is the honest control.
- The simulation detects pivots with strict inequalities on both sides; how `ta.pivothigh` and `ta.pivotlow` treat equal highs or lows is not stated in the reference. Ties are rare on a synthetic series and the rule, whatever it is, applies to the levels and the random ratios alike.
- It reports counts, not a trading rule. Not financial advice.
- The script has not been compiled outside TradingView; compile it in the Pine Editor before relying on it.

## Pine API notes

What the Pine Script v6 reference and user manual say about the built-ins the script relies on, read on 2026-10-14 through the context7 documentation index:

- `ta.pivothigh(source, leftbars, rightbars) → series float` (also a two-argument overload on `high`): "returns price of the pivot high point. It returns 'NaN', if there was no pivot high point." Parameters `leftbars` and `rightbars` are "series int/float". Remarks: "If parameters 'leftbars' or 'rightbars' are series you should use max_bars_back() function for the 'source' variable." The script passes an input int, not a series, and sets no `max_bars_back`.
- `ta.pivotlow(source, leftbars, rightbars) → series float`: the same for pivot lows, on `low` here.
- `label.new(x, y, text, xloc, yloc, color, style, textcolor, size, textalign, tooltip, text_font_family, force_overlay, text_formatting) → series label`: `xloc` defaults to `xloc.bar_index` and `yloc` to `yloc.price`, which is how the script places a label at `bar_index - len` and the pivot price; styles include `label.style_label_up` and `label.style_label_down`; `size.small` is a listed size.
- Arithmetic operators (user manual): "If both operands are of int type, the result will also be an int", and in v6 "dividing two 'int' values that are not evenly divisible always results in a number with a fractional value, e.g., 5/2 = 2.5". The script casts counts to float before dividing anyway, as the template it mirrors does. "The % operator calculates the modulo by rounding down the quotient", i.e. a floor modulo, the same as Python's; the generator's states are never negative, so both agree in any case.
- `for` loops (user manual): "If the to_num value is below the from_num value, the loop counts downward instead." This is why the loops over the random ratios are guarded when no level is enabled, where `numLevels - 1` would be -1. Loops support `break` and `continue`.
- `array.sort(id, order) → void`: sorts in place, `order.ascending` by default; the script sorts the M uniforms of each random set before spacing them.
- `indicator()` parameter `max_labels_count`: the label limit of the script, set to 100 here; the label queue keeps at most N <= 100 labels in any case.

## License

MIT. See `LICENSE`.
