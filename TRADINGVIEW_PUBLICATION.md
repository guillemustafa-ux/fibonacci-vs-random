# Fibonacci vs Random Ratios: Where Pullbacks Actually Stop

Description to paste as is (between the rules):

---
WHAT IT DOES
Fibonacci retracement tools draw lines at 23.6%, 38.2%, 50%, 61.8% and 78.6% of a swing and leave the question open: do pullbacks stop near those lines more often than near any other line? This indicator counts. It finds swings with pivot highs and lows of one length, measures how deep each pullback went into the leg before it, and checks whether that depth lies within a tolerance of one of the enabled Fibonacci levels. Then it runs the same check against sets of ratios drawn at random between 0.2 and 0.8, with the same tolerance and the same number of ratios, and reports how many random sets did as well as the levels or better. The table on the last bar shows the rates, a verdict and the distribution of depths; labels mark where the last pullbacks stopped.

WHAT IS ORIGINAL HERE
Scripts that report how often each Fibonacci level is reached answer half of the question: a hit rate without a baseline reads well on any chart, since five levels with a tolerance of 0.02 cover a window of 0.2 of all depths and a random walk touches every level by chance. This script builds the baseline into the measurement. Each random set has as many ratios as there are enabled levels and is tested with the same tolerance on the same pullbacks, so the only difference between the Fibonacci rate and a random rate is where the ratios sit. If one random set in ten or more does as well as the levels, the levels are not special on this chart; if fewer than one in twenty do, they are ahead. A seeded generator draws the ratios, so they are the same on every chart; a different seed draws other sets.

HOW IT IS MEASURED
- Swings: ta.pivothigh and ta.pivotlow with the pivot length on both sides; a pivot confirms that many bars after its bar. Pivots are kept alternating: one of the same type as the last kept pivot replaces it when more extreme and is ignored otherwise.
- Pullback: every kept pivot after the second ends one. The two before it define the leg, the new one is where the pullback stopped. Up leg, pullback to a low: depth = (high - new low) / (high - first low). Down leg: depth = (new high - low) / (first high - low). A depth of 1 or more is a full retrace, counted and kept out of the test. Legs of zero height are skipped.
- Hit: |depth - ratio| <= tolerance for any ratio of the set, Fibonacci or random.
- Statistics: rate = hits / pullbacks, interval = rate +- 1.96 * sqrt(rate * (1 - rate) / pullbacks); for the random sets, the mean, lowest and highest rate and how many have at least the Fibonacci hits. Difference = Fibonacci rate minus random mean, in points.
- Counters move only when a pivot confirms, on confirmed bars. No request.security call.

HOW TO USE IT
1. Keep the default pivot length first, then try the length that matches the swings you would draw by hand; every number depends on it.
2. Read the "Random sets >= fib" row: "fib not special" means one random set in ten or more matched or beat the levels, "fib ahead" means fewer than one in twenty did, "borderline" is between. Under 30 pullbacks the verdict adds "(small sample)".
3. Compare the Fibonacci rate with the random mean and its interval: a difference inside the interval is noise.
4. Hand check a label: measure the leg and the pullback with the cursor and recompute the depth.

HOW TO READ THE TABLE
Header: symbol, timeframe, pivot length, tolerance, enabled levels.
Pullbacks: pullbacks tested, full retraces, bars counted.
Fib hits: hits, rate, 95% confidence interval.
Random ratios: sets, ratios per set, mean, lowest and highest rate.
Random sets >= fib: how many did as well or better, and the verdict.
Difference: Fibonacci rate minus random mean, and the rate a depth spread evenly over [0.2, 0.8] would give.
Depth distribution: share of pullbacks in each fifth of the leg.
Last pullback: depth, Fibonacci hit, bar time in the chart symbol's exchange time.

LIMITATIONS
- The pivot length defines the swings; a different length changes every number, the verdict included.
- The tolerance drives the base rate for the Fibonacci levels and the random ratios alike.
- The test says nothing about what price does after a touch; it measures where pullbacks stopped, not what followed.
- A random walk produces touches at every level by chance; that is exactly what the baseline measures, and the levels have to beat it.
- Only loaded bars count, so history depth, symbol and timeframe change the result. Counts, not a trading rule. Not financial advice.

The chart shows BINANCE:BTCUSDT on the 1 hour timeframe with the default settings. The table is in the bottom right.
---

## Publishing checklist

- [ ] Compile `fibonacci_vs_random.pine` in the Pine Editor with no errors or warnings.
- [ ] Set the chart: BINANCE:BTCUSDT, 1 hour, default inputs, table visible.
- [ ] Check the identities: `Fib hits <= pullbacks`; in "Random sets >= fib", `k <= K`; the five depth shares sum to 100% (up to rounding); the random mean lies between the min and the max shown.
- [ ] Hand check one labeled pullback: measure the leg (first pivot to second pivot) and the pullback (second pivot to the labeled pivot) with the cursor and recompute the depth; it must match the label at two decimals.
- [ ] Set the tolerance to 0.1 with all five levels on: the Fibonacci rate must rise toward the random rates, since both windows now cover most depths. Set it back to 0.02.
- [ ] Set K to 50 and change the seed a few times: the random mean must stay about the same while the min and max move. Set K and the seed back to the defaults.
- [ ] Check the title is at most 60 characters (it is 57).
- [ ] Publish as open source, with the MIT license text if the form allows it.
- [ ] Check that the description contains no links, contact info, or performance claims, and is between 3,000 and 4,600 characters.
- [ ] In Final touches, open Show more and fill the tags BEFORE pressing Publish; the field takes 5 tags at most, and the Tags field has to be clicked inside before each paste. Suggested tags (one word each): fibonacci, retracement, statistics, randombaseline, pullback.
- [ ] Before pressing Publish, make sure the chart has no drawings: a stray paste becomes a text drawing in the snapshot.
- [ ] Add the TradingView script URL to `README.md` after publishing.
