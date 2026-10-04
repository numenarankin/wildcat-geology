import { describe, expect, it } from "vitest";
import {
  buildCalibration,
  checkAnchors,
  fitDepthMap,
  overviewSize,
  pickSegment,
  planCrops,
  segmentScale,
  type AnchorInput,
} from "./calibration";

/*
 * Every expected value below is worked out by hand from the anchors, not taken
 * from running the code. The running example: labels at row 1000 = 4,000 ft,
 * row 3000 = 4,100 ft, row 5000 = 4,200 ft. That is 100 ft per 2,000 rows,
 * 0.05 ft/row (20 px/ft), and depth = 3,950 + 0.05 x row.
 */
const EVEN = [
  { row: 1000, depthFt: 4000 },
  { row: 3000, depthFt: 4100 },
  { row: 5000, depthFt: 4200 },
];
const PAGE = { page: 1, width: 1000, height: 8000 };

describe("fitDepthMap", () => {
  it("recovers the scale from evenly spaced labels", () => {
    const fit = fitDepthMap(EVEN);
    expect(fit.ftPerRow).toBeCloseTo(0.05, 10);
    expect(fit.interceptFt).toBeCloseTo(3950, 8);
    fit.residualsFt.forEach((r) => expect(r).toBeCloseTo(0, 8));
  });

  it("spreads a misread label across the fit, which is why it is refused", () => {
    // 4,230 in place of 4,200. Means: row 3000, depth 4110. Slope
    // ((-2000)(-110) + (2000)(120)) / (2 x 2000^2) = 0.0575; intercept
    // 4110 - 0.0575 x 3000 = 3937.5. Fitted 3995 / 4110 / 4225, so the
    // residuals are 5, -10, 5 ft. Limit max(2, 1% of 230) = 2.3 ft.
    const fit = fitDepthMap([...EVEN.slice(0, 2), { row: 5000, depthFt: 4230 }]);
    expect(fit.ftPerRow).toBeCloseTo(0.0575, 10);
    expect(fit.interceptFt).toBeCloseTo(3937.5, 8);
    expect(fit.residualsFt.map((r) => Math.round(r * 1000) / 1000)).toEqual([5, -10, 5]);
    expect(fit.limitFt).toBeCloseTo(2.3, 10);
  });
});

describe("checkAnchors", () => {
  it("accepts a straight scale", () => {
    expect(checkAnchors(EVEN, PAGE)).toBeNull();
  });

  it("refuses a misread label and reports every mark's miss", () => {
    const problem = checkAnchors(
      [...EVEN.slice(0, 2), { row: 5000, depthFt: 4230 }],
      PAGE
    );
    expect(problem).toContain("allowed 2.3 ft");
    expect(problem).toContain("4230 ft at row 5000: 5 ft off");
    expect(problem).toContain("4100 ft at row 3000: -10 ft off");
  });

  it("allows the slop of placing a label by eye", () => {
    // 4,200.5 at row 5000: residuals +/-0.17 ft or so, under the 2 ft floor.
    expect(
      checkAnchors([...EVEN.slice(0, 2), { row: 5000, depthFt: 4200.5 }], PAGE)
    ).toBeNull();
  });

  it("needs three marks", () => {
    expect(checkAnchors(EVEN.slice(0, 2), PAGE)).toBe("needs at least 3 depth marks, has 2");
  });

  it("refuses depth that runs up the page", () => {
    expect(
      checkAnchors([...EVEN.slice(0, 2), { row: 5000, depthFt: 4050 }], PAGE)
    ).toBe(
      "depth must increase down the log: row 5000 reads 4050 ft, below row 3000 at 4100 ft"
    );
  });

  it("refuses a row off the page", () => {
    expect(checkAnchors([...EVEN, { row: 8000, depthFt: 4350 }], PAGE)).toBe(
      "row 8000 is off page 1, which has rows 0 to 7999"
    );
  });
});

describe("planCrops", () => {
  it("fits a short range in one crop", () => {
    // 4,040 ft -> (4040 - 3950) / 0.05 = row 1800; 4,060 ft -> row 2200.
    const { rowAt } = segmentScale({ page: 1, rowStart: 0, rowEnd: 8000, anchors: EVEN });
    expect(planCrops(PAGE, rowAt(4040), rowAt(4060))).toEqual({
      crops: [{ page: 1, top: 1800, height: 400, outWidth: 1000, outHeight: 400 }],
      nextRow: null,
    });
  });

  it("splits a long range at the edge limit with a 64 px overlap", () => {
    // Rows 1000..5000 at 1000 px wide: the pixel budget allows 3,588 rows, so
    // the 2,576 edge binds. 1000..3576, then 3576 - 64 = 3512..5000.
    expect(planCrops(PAGE, 1000, 5000).crops).toEqual([
      { page: 1, top: 1000, height: 2576, outWidth: 1000, outHeight: 2576 },
      { page: 1, top: 3512, height: 1488, outWidth: 1000, outHeight: 1488 },
    ]);
  });

  it("lets the pixel budget bind on a wide log", () => {
    // 1,700 px wide: floor(3,588,000 / 1700) = 2,110 rows a crop.
    // 0..2110, 2046..4156, 4092..5000.
    const wide = { page: 1, width: 1700, height: 8000 };
    expect(planCrops(wide, 0, 5000).crops.map((c) => [c.top, c.height])).toEqual([
      [0, 2110],
      [2046, 2110],
      [4092, 908],
    ]);
  });

  it("scales a page wider than the edge limit, and overlaps in source rows", () => {
    // 5,152 px wide -> sent at 2,576 (scale 0.5). Pixel budget:
    // floor(3,588,000 / 2576) = 1,392 output rows = 2,784 source rows.
    // Overlap 64 output px = 128 source rows: 0..2784, then 2656..4000.
    const huge = { page: 1, width: 5152, height: 8000 };
    expect(planCrops(huge, 0, 4000).crops).toEqual([
      { page: 1, top: 0, height: 2784, outWidth: 2576, outHeight: 1392 },
      { page: 1, top: 2656, height: 1344, outWidth: 2576, outHeight: 672 },
    ]);
  });

  it("stops at the per-call cap and says where to continue", () => {
    // Crops start 0, 2512, 5024, 7536 (2,576 tall, 64 overlap); the fifth
    // would start at 7536 + 2576 - 64 = 10048.
    const tall = { page: 1, width: 1000, height: 30000 };
    const { crops, nextRow } = planCrops(tall, 0, 20000);
    expect(crops.map((c) => c.top)).toEqual([0, 2512, 5024, 7536]);
    expect(nextRow).toBe(10048);
  });
});

describe("buildCalibration and pickSegment", () => {
  // Section 1: the 5" detail, 20 px/ft (the running example).
  // Section 2: a 1" overview of the same interval lower on the page:
  // rows 6000/6400/6800 = 4,000/4,100/4,200 ft, 0.25 ft/row (4 px/ft),
  // depth = 2,500 + 0.25 x row.
  const anchors: AnchorInput[] = [
    ...EVEN.map((a) => ({ section: 1, page: 1, ...a })),
    { section: 2, page: 1, row: 6000, depthFt: 4000 },
    { section: 2, page: 1, row: 6400, depthFt: 4100 },
    { section: 2, page: 1, row: 6800, depthFt: 4200 },
  ];
  const built = buildCalibration(anchors, [PAGE]);

  it("extends each section a label interval and splits the overlap halfway", () => {
    // Section 1: 1000..5000, spacing 2000 -> 0..7000. Section 2: 6000..6800,
    // spacing 400 -> 5600..7200. They overlap, so they meet at
    // (5000 + 6000) / 2 = 5500.
    expect(built.ok).toBe(true);
    if (!built.ok) return;
    expect(built.calibration.segments.map((s) => [s.rowStart, s.rowEnd])).toEqual([
      [0, 5500],
      [5500, 7200],
    ]);
  });

  it("reads the detail section when both cover the range", () => {
    if (!built.ok) throw new Error("calibration refused");
    // Section 1 covers 3,950..4,225 ft; section 2 covers 3,875..4,300 ft.
    const pick = pickSegment(built.calibration, 4090, 4110);
    expect(pick?.segment.anchors[0].row).toBe(1000);
  });

  it("prefers a section that covers the whole range over a sharper partial one", () => {
    if (!built.ok) throw new Error("calibration refused");
    // 4,200..4,280: section 1 stops at 4,225, section 2 covers it all.
    expect(pickSegment(built.calibration, 4200, 4280)?.segment.anchors[0].row).toBe(6000);
  });

  it("clips the range to what the chosen section covers", () => {
    if (!built.ok) throw new Error("calibration refused");
    // Nothing covers 4,250..4,400 whole; section 2 reaches deepest (4,300).
    const pick = pickSegment(built.calibration, 4250, 4400);
    expect(pick?.segment.anchors[0].row).toBe(6000);
    expect(pick?.bottomFt).toBeCloseTo(4300, 8);
  });

  it("returns null outside every section", () => {
    if (!built.ok) throw new Error("calibration refused");
    expect(pickSegment(built.calibration, 5000, 5100)).toBeNull();
  });

  it("names the section each problem belongs to", () => {
    const bad = buildCalibration(
      [
        { section: 1, page: 1, row: 1000, depthFt: 4000 },
        { section: 1, page: 2, row: 3000, depthFt: 4100 },
        { section: 1, page: 1, row: 5000, depthFt: 4200 },
        { section: 2, page: 1, row: 6000, depthFt: 4000 },
      ],
      [PAGE]
    );
    expect(bad).toEqual({
      ok: false,
      problems: [
        "section 1: marks on more than one page (1, 2)",
        "section 2: needs at least 3 depth marks, has 1",
      ],
    });
  });
});

describe("overviewSize", () => {
  it("shrinks a tall log to the edge limit", () => {
    // 1,700 x 30,000: the edge binds (2576 / 30000 = 0.08587), well under
    // the pixel budget. 1700 x 0.08587 = 145.97 -> 145.
    expect(overviewSize({ page: 1, width: 1700, height: 30000 })).toMatchObject({
      width: 145,
      height: 2576,
    });
  });

  it("leaves a page that already fits alone", () => {
    expect(overviewSize({ page: 1, width: 1000, height: 1200 })).toEqual({
      width: 1000,
      height: 1200,
      scale: 1,
    });
  });
});
