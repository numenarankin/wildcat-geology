import { test } from "vitest";
import assert from "node:assert/strict";
import {
  fitDecline,
  project,
  forward12moDecline,
  monthlyRatesFromPoints,
  latestDailyEma,
  type MonthlyRate,
  type ProductionPoint,
} from "./arps";

function pt(date: string, oil: number, gas = 0): ProductionPoint {
  return { date, oilProduction: oil, gasProduction: gas };
}

test("latestDailyEma: empty → 0, single point → its value", () => {
  assert.equal(latestDailyEma([], "oil"), 0);
  assert.equal(latestDailyEma([pt("2026-07-01", 42)], "oil"), 42);
});

test("latestDailyEma: constant series equals the constant", () => {
  const pts = ["2026-07-01", "2026-07-02", "2026-07-03"].map((d) => pt(d, 5));
  assert.ok(Math.abs(latestDailyEma(pts, "oil") - 5) < 1e-9);
});

test("latestDailyEma: weights the most recent day (span 14, α=2/15)", () => {
  // ema0=10; ema1 = (2/15)·20 + (13/15)·10 = 11.333…
  const v = latestDailyEma(
    [pt("2026-07-01", 10), pt("2026-07-02", 20)],
    "oil"
  );
  assert.ok(Math.abs(v - 34 / 3) < 1e-9, `got ${v}`);
});

test("latestDailyEma: sorts by date (input order independent) and reads the stream", () => {
  const ordered = [pt("2026-07-01", 0, 100), pt("2026-07-02", 0, 200)];
  const shuffled = [ordered[1], ordered[0]];
  assert.equal(
    latestDailyEma(shuffled, "gas"),
    latestDailyEma(ordered, "gas")
  );
  // gas stream, not oil (oil is 0 here).
  assert.ok(latestDailyEma(ordered, "gas") > 100);
  assert.equal(latestDailyEma(ordered, "oil"), 0);
});

/** Build a monthly series from a rate function of t (years since start). */
function series(
  n: number,
  rateAt: (t: number) => number,
  startMonth = 1
): MonthlyRate[] {
  const out: MonthlyRate[] = [];
  for (let i = 0; i < n; i++) {
    const month = `2026-${String(startMonth + i).padStart(2, "0")}`;
    out.push({ month, rate: rateAt(i / 12) });
  }
  return out;
}

test("fitDecline: recovers an exponential decline (b ≈ 0)", () => {
  /*
   * A known curve in, the same curve out. The tolerances are wider than the
   * arithmetic needs because the shipped despike (`HAMPEL_K` = 0.5) costs a
   * little accuracy on a CLEAN series: the first month's window is clipped by
   * the start of the series, so its median sits below the true first point, and
   * a threshold this tight flags the point rather than the neighbourhood.
   *
   * Measured on this exact series: qi 98.25 against a true 100, Di 0.462 against
   * a true 0.500. At `hampelK: 3` all four come back exact, so the error is the
   * sensitivity's, not the fit's. Kept as a bound rather than removed so it
   * fails loudly if a future change makes it worse.
   */
  const qi = 100;
  const Di = 0.5;
  const fit = fitDecline(series(12, (t) => qi * Math.exp(-Di * t)))!;
  assert.ok(fit, "fits");
  assert.ok(fit.b < 0.1, `b ≈ 0, got ${fit.b}`);
  assert.ok(Math.abs(fit.qi - qi) < 2.5, `qi ≈ 100, got ${fit.qi}`);
  assert.ok(Math.abs(fit.Di - Di) < 0.05, `Di ≈ 0.5, got ${fit.Di}`);

  // The clean-data cost is the despike's alone: turn it down and it vanishes.
  const lenient = fitDecline(series(12, (t) => qi * Math.exp(-Di * t)), {
    hampelK: 3,
  })!;
  assert.ok(Math.abs(lenient.qi - qi) < 0.01, `exact at k=3, got ${lenient.qi}`);
});

test("forward12moDecline: exponential fit matches its constant annual decline", () => {
  const Di = 0.5;
  const fit = fitDecline(series(12, (t) => 100 * Math.exp(-Di * t)))!;
  // Exponential: fraction lost over a year is 1 − exp(−Di), constant everywhere.
  const expected = 1 - Math.exp(-Di);
  // 3 points of slack for the same edge effect as the test above: the shipped
  // sensitivity reads 36.97% against a true 39.35%, i.e. it UNDERSTATES decline
  // on clean data. At `hampelK: 3` it lands on 39.35% exactly.
  assert.ok(
    Math.abs(forward12moDecline(fit) - expected) < 0.03,
    `forward ≈ ${expected}, got ${forward12moDecline(fit)}`
  );
});

test("fitDecline + forward: hyperbolic forward-12mo is distinct from the trailing rate", () => {
  const qi = 100;
  const Di = 1.2;
  const b = 0.6;
  const fit = fitDecline(
    series(15, (t) => qi / Math.pow(1 + b * Di * t, 1 / b))
  )!;
  assert.ok(fit.b > 0.2, `hyperbolic b recovered, got ${fit.b}`);

  // A hyperbolic decline SLOWS: the forward-12-month decline from the window end
  // is milder than the initial-year decline.
  const initialYear = 1 - project(fit, 1) / project(fit, 0);
  const forward = forward12moDecline(fit);
  assert.ok(
    forward < initialYear,
    `forward (${forward}) shallower than initial (${initialYear})`
  );
});

test("project: terminal-exponential switch caps the tail decline at dMin", () => {
  const fit = fitDecline(
    series(15, (t) => 100 / Math.pow(1 + 0.6 * 1.5 * t, 1 / 0.6)),
    { dMinAnnual: 0.08 }
  )!;
  assert.ok(fit.tSwitch > 0, "a switch time exists for a steep hyperbolic fit");
  // Past the switch, the year-over-year decline settles to ~dMin.
  const tPast = fit.tSwitch + 3;
  const decline = 1 - project(fit, tPast + 1) / project(fit, tPast);
  assert.ok(
    Math.abs(decline - 0.08) < 0.02,
    `terminal decline ≈ 8%, got ${decline}`
  );
});

test("fitDecline: a rising (pre-peak) well gets no curve", () => {
  // Monotonically increasing → peak is the last point → too few post-peak months.
  const rising = series(12, (t) => 50 + 100 * t);
  assert.equal(fitDecline(rising), null);
});

test("fitDecline: too little post-peak data returns null", () => {
  const short = series(4, (t) => 100 * Math.exp(-0.5 * t));
  assert.equal(fitDecline(short, { minMonths: 6 }), null);
});

// --- Outlier handling ------------------------------------------------------

/** Set one month's rate to `value`, returning a new series (spike injector). */
function withSpike(s: MonthlyRate[], idx: number, value: number): MonthlyRate[] {
  return s.map((m, i) => (i === idx ? { ...m, rate: value } : m));
}

test("fitDecline: an isolated spike is despiked — fit barely moves (robustness)", () => {
  const clean = series(15, (t) => 100 * Math.exp(-0.5 * t));
  const cleanFit = fitDecline(clean)!;
  // A single month surges 10× mid-series.
  const fit = fitDecline(withSpike(clean, 8, clean[8].rate * 10))!;
  assert.ok(
    Math.abs(forward12moDecline(fit) - forward12moDecline(cleanFit)) < 0.03,
    `forward stays ≈ clean (${forward12moDecline(cleanFit)}), got ${forward12moDecline(fit)}`
  );
  assert.ok(Math.abs(fit.Di - cleanFit.Di) < 0.1, `Di stays ≈ ${cleanFit.Di}, got ${fit.Di}`);
});

test("fitDecline: a spike does NOT hijack peak detection or truncate the window", () => {
  // A gently-declining well (2 years). Without robust peak, a big late spike
  // would become the 'peak' and throw away all history before it.
  const clean = series(24, (t) => 20 * Math.exp(-0.3 * t));
  const fit = fitDecline(withSpike(clean, 20, 300))!;
  // Window still starts at the true peak (first month) and spans all 24 months.
  assert.equal(fit.startMonth, clean[0].month, "peak stays at the real peak, not the spike");
  assert.equal(fit.months, 24, "full history kept, not just the post-spike tail");
});

test("fitDecline: a late spike is not chosen as the peak of a ramp-then-decline well", () => {
  // Ramp up to a genuine peak at month index 3, then decline for 20 months.
  const rates: number[] = [];
  for (let i = 0; i < 24; i++) {
    rates.push(i <= 3 ? 5 + i * 10 : 35 * Math.exp(-0.3 * ((i - 3) / 12)));
  }
  rates[18] = 250; // a spurious late spike, far bigger than the real peak (35)
  const s: MonthlyRate[] = rates.map((rate, i) => ({
    month: `2026-${String(i + 1).padStart(2, "0")}`,
    rate,
  }));
  const fit = fitDecline(s)!;
  // The window starts at the real peak (month index 3 → "2026-04"), not month 19.
  assert.equal(fit.startMonth, "2026-04");
});

test("monthlyRatesFromPoints: rolls daily points to a monthly rate, dropping zeros", () => {
  const rates = monthlyRatesFromPoints(
    [
      { date: "2026-07-01", oilProduction: 100, gasProduction: 0 },
      { date: "2026-07-15", oilProduction: 80, gasProduction: 0 },
      { date: "2026-07-20", oilProduction: 0, gasProduction: 0 },
    ],
    "oil"
  );
  assert.equal(rates.length, 1);
  assert.equal(rates[0].month, "2026-07");
  assert.equal(rates[0].rate, 90, "(100 + 80) / 2 producing days");
});

test("fitDecline: the peak is the best 90-day average, not the best month", () => {
  /*
   * A well flat at 100/mo, one month reading 130, then declining.
   *
   * The two rules disagree here, which is the point. Worked by hand from the
   * rates below (the 130 is close enough to its neighbours to survive the
   * despike pass, so it really is in the data the peak is chosen from):
   *
   *   highest MONTH          index 6, at 130
   *   highest 90-day average index 4, at (100 + 100 + 130) / 3 = 110
   *                          (index 5 = 103.3, index 6 = (130+80+80)/3 = 96.7)
   *
   * The old rule started the curve at 130 — a rate the well held for one month —
   * and every later month had to be explained as decline from it. The 90-day
   * rule starts on the plateau the well actually held.
   */
  const rates = [100, 100, 100, 100, 100, 100, 130, 80, 80, 78, 76, 74, 72, 70];
  const s: MonthlyRate[] = rates.map((rate, i) => ({
    month: `2026-${String(i + 1).padStart(2, "0")}`,
    rate,
  }));
  /*
   * Despiking is turned OFF here so this covers the averaging rule and nothing
   * else. At the shipped sensitivity the 130 never reaches the peak step at all
   * — it is flattened first, which the assertion below states directly. The
   * averaging rule still has to be covered on its own, because the peak window
   * is the knob most likely to be widened again.
   */
  const averaged = fitDecline(s, { peakSmoothDays: 90, noDespike: true })!;
  assert.equal(averaged.startMonth, "2026-05", "90 days averages the peak");
  assert.notEqual(averaged.startMonth, "2026-07", "not the single highest month");

  // The shipped tuning gets there by a different route: the despike removes the
  // 130, so even a one-month peak window cannot start the curve on it.
  const shipped = fitDecline(s)!;
  assert.notEqual(shipped.startMonth, "2026-07", "despiked before it can win");
});

/** `count` months from `2024-01`, so a long series keeps ascending month keys. */
function months(count: number, rate: (i: number) => number): MonthlyRate[] {
  return Array.from({ length: count }, (_, i) => ({
    month: `${2024 + Math.floor(i / 12)}-${String((i % 12) + 1).padStart(2, "0")}`,
    rate: rate(i),
  }));
}

test("fitDecline: every knob in FitOpts changes the fit it governs", () => {
  /*
   * The decline lab is only useful if turning a knob moves the curve, so each
   * knob is asserted against a series built to make ITS branch matter. The
   * assertion is that the result differs from the shipped tuning — not that it
   * moves in a particular direction, which is the judgement the lab exists for.
   */
  const wobble = (i: number) => (i % 4 === 0 ? 1.35 : i % 3 === 0 ? 0.72 : 1);

  // Declines from the first month, so the outlier gates have plenty to chew on.
  const noisy = months(30, (i) => 100 * Math.exp(-0.4 * (i / 12)) * wobble(i));
  // Ramps for a year BEFORE declining. The peak window only decides where the
  // curve starts, so it can only matter on a well that has a start to find.
  const ramped = months(36, (i) =>
    i < 12 ? (20 + i * 8) * wobble(i) : 116 * Math.exp(-0.4 * ((i - 11) / 12))
  );

  const differs = (
    a: NonNullable<ReturnType<typeof fitDecline>>,
    b: NonNullable<ReturnType<typeof fitDecline>>
  ) =>
    a.qi !== b.qi ||
    a.Di !== b.Di ||
    a.b !== b.b ||
    a.startMonth !== b.startMonth ||
    a.months !== b.months ||
    a.dMin !== b.dMin;

  const moves = (
    series: MonthlyRate[],
    opts: Parameters<typeof fitDecline>[1],
    what: string
  ) => {
    const base = fitDecline(series)!;
    const tuned = fitDecline(series, opts);
    assert.ok(tuned, `${what}: still fits`);
    assert.ok(differs(base, tuned), `${what} changes the fit`);
  };

  moves(ramped, { peakSmoothDays: 360 }, "peak window");
  moves(noisy, { hampelK: 6 }, "outlier sensitivity");
  moves(noisy, { hampelWindow: 15 }, "outlier window");
  moves(noisy, { residK: 0.5 }, "refit rejection");
  moves(noisy, { dMinAnnual: 0.3 }, "terminal decline");
  moves(noisy, { noDespike: true }, "skipping the despike");

  // minMonths gates whether a curve exists at all rather than reshaping one.
  assert.equal(fitDecline(noisy, { minMonths: 999 }), null, "minMonths gates");
});

test("fitDecline: the peak window cannot move a well that only ever declines", () => {
  /*
   * Worth pinning, because it is the first thing that looks broken in the lab:
   * on a well whose highest 90 days are its first 90 days — every well with a
   * long filing history behind it — the start month is already month one, and
   * widening the window has nothing left to move it to. The knob is not dead,
   * it is satisfied.
   */
  const declining = months(36, (i) => 100 * Math.exp(-0.35 * (i / 12)));
  const narrow = fitDecline(declining, { peakSmoothDays: 30 })!;
  const wide = fitDecline(declining, { peakSmoothDays: 540 })!;
  assert.equal(narrow.startMonth, declining[0].month);
  assert.equal(wide.startMonth, declining[0].month);
  assert.equal(narrow.months, wide.months);
});

test("despike is blind to a bump wider than half its window, at any sensitivity", () => {
  /*
   * Why turning outlier sensitivity up does nothing to Roy Corbett's oil.
   *
   * The despike replaces a month with its window's MEDIAN when it sits too far
   * from it. With a 5-month window, three consecutive high months make the high
   * value the median — the middle of [normal, B, B, B, normal] is B — so the
   * bump is zero distance from "typical" and no threshold can flag it. Turning
   * `hampelK` down to 0.5 changes nothing, because the comparison itself is
   * already satisfied.
   *
   * The knob that works on this is the WINDOW, not the sensitivity: widen it
   * until the bump is a minority of it.
   */
  const rates = months(40, (i) =>
    i >= 30 && i <= 32 ? 260 : 100 * Math.exp(-0.2 * (i / 12))
  );

  const shipped = fitDecline(rates)!;
  const sensitive = fitDecline(rates, { hampelK: 0.5 })!;
  assert.equal(
    sensitive.startMonth,
    shipped.startMonth,
    "sensitivity cannot reach a three-month bump"
  );

  // Widening the window past the bump does reach it.
  const wider = fitDecline(rates, { hampelWindow: 11 })!;
  assert.notEqual(
    wider.startMonth,
    shipped.startMonth,
    "a window the bump is a minority of does reach it"
  );
});

test("fitDecline: a peak in the last few months can't start the curve", () => {
  /*
   * A surge at the very end used to become the peak, leaving too few months
   * behind it to fit — so the chart drew a rate line and no curve at all. The
   * peak search now stops `minMonths` short of the end, because a peak with no
   * data after it is the end of the series, not the start of a decline.
   */
  const rates = months(30, (i) => (i >= 27 ? 400 : 100 * Math.exp(-0.3 * (i / 12))));
  const fit = fitDecline(rates);
  assert.ok(fit, "still fits, rather than being killed by the tail");
  assert.ok(
    fit.startMonth < rates[rates.length - 6].month,
    `peak leaves room to fit, got ${fit.startMonth}`
  );
});
