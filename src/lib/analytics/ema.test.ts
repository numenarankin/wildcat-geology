import { describe, it, expect } from "vitest";
import { latestEma, ownDateSeries } from "./ema";

describe("latestEma", () => {
  it("returns null until there are `period` points", () => {
    expect(latestEma([], 14)).toBeNull();
    expect(latestEma([1, 2, 3], 14)).toBeNull();
    expect(latestEma(Array(13).fill(10), 14)).toBeNull();
  });

  it("seeds with the simple average of the first `period` points", () => {
    // Exactly `period` points → SMA of them, no EMA step yet.
    expect(latestEma([10, 20, 30], 3)).toBeCloseTo(20);
    expect(latestEma(Array(14).fill(100), 14)).toBeCloseTo(100);
  });

  it("applies the v·k + prev·(1−k) recurrence after seeding", () => {
    // period 3 → k = 2/4 = 0.5. Seed = avg(2,4,6) = 4. Next value 10:
    // 10·0.5 + 4·0.5 = 7. Then value 0: 0·0.5 + 7·0.5 = 3.5.
    expect(latestEma([2, 4, 6, 10], 3)).toBeCloseTo(7);
    expect(latestEma([2, 4, 6, 10, 0], 3)).toBeCloseTo(3.5);
  });

  it("is not skewed by a single trailing spike the way the last value is", () => {
    const flat = Array(20).fill(50);
    const withSpike = [...flat, 500];
    // The latest raw value jumps to 500; the 14-day EMA barely moves.
    expect(latestEma(withSpike, 14)!).toBeLessThan(140);
  });

  it("guards a non-positive period", () => {
    expect(latestEma([1, 2, 3], 0)).toBeNull();
  });
});

describe("ownDateSeries", () => {
  /** `n` consecutive days from 2026-01-01, each carrying `rate`. */
  const days = (n: number, rate: number, from = 1) =>
    Array.from({ length: n }, (_, i) => ({
      date: `2026-01-${String(from + i).padStart(2, "0")}`,
      rate,
    }));

  it("keeps each stream on its own dates, inventing nothing", () => {
    const own = ownDateSeries({
      oil: days(3, 10),
      gas: [{ date: "2026-01-01", rate: 400 }],
    });
    expect(own.oil.values).toEqual([10, 10, 10]);
    // One reading, one value. The 2nd and 3rd are days nobody read the meter,
    // and a zero there is a measurement nobody took.
    expect(own.gas.values).toEqual([400]);
  });

  it("reports each stream's own last day", () => {
    const own = ownDateSeries({
      oil: days(3, 10),
      gas: [{ date: "2026-01-01", rate: 400 }],
    });
    expect(own.oil.lastDate).toBe("2026-01-03");
    expect(own.gas.lastDate).toBe("2026-01-01");
  });

  it("orders by date however the caller supplied the points", () => {
    const own = ownDateSeries({
      oil: [
        { date: "2026-01-03", rate: 3 },
        { date: "2026-01-01", rate: 1 },
        { date: "2026-01-02", rate: 2 },
      ],
    });
    expect(own.oil.values).toEqual([1, 2, 3]);
  });

  it("lets a later entry win a duplicate date, so a measurement beats an estimate", () => {
    const own = ownDateSeries({
      oil: [
        { date: "2026-01-01", rate: 99 }, // state's estimate
        { date: "2026-01-01", rate: 12 }, // the operator's own reading
      ],
    });
    expect(own.oil.values).toEqual([12]);
  });

  it("an unread meter does not drag the rate down while its sibling reports", () => {
    /*
     * The lease made 400 mcf/d over the 14 days its meter was read, and its
     * tanks were gauged for 14 days after that. Oracle: the gas EMA sees only
     * the 400s, so it reads 400 — the meter was not read, which is not the same
     * as the well making no gas. A stream that genuinely stopped is decayed by
     * `emaAsOf` against the record's horizon instead, which is where the state's
     * silence (evidence) is separated from the pumper's (not evidence).
     */
    const gas = days(14, 400);
    const oil = days(28, 10);
    const own = ownDateSeries({ oil, gas });
    expect(latestEma(own.gas.values, 14)!).toBeCloseTo(400);
    expect(own.gas.values).toHaveLength(14);
  });

  it("an explicit zero reading still counts", () => {
    // A meter read at nothing IS a measurement and belongs in the average.
    const own = ownDateSeries({ gas: [...days(7, 400), ...days(7, 0, 8)] });
    expect(own.gas.values).toHaveLength(14);
    expect(latestEma(own.gas.values, 14)!).toBeLessThan(400);
  });
});

