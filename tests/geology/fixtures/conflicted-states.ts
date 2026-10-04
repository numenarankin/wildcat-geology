/**
 * The labelled set: well evaluations that are contradictory, and ones that are not.
 *
 * Stage 2 is a model call now, so its metric is RECALL over this set, not
 * rule-by-rule firing. The set is small and hand-built, and each conflicted case
 * is a shape that actually produced a wrong answer in one of the two sample
 * analyses or is a direct analogue of one.
 *
 * The harness tests use these to prove the agent is SHOWN what it needs. The
 * live test uses them to measure whether it finds it.
 */
import {
  createZoneEvaluation,
  type ZoneEvaluationStore,
} from "@/lib/ai/geology/state";

export interface LabelledCase {
  name: string;
  /** True when a reasonable reviewer would say these facts contradict. */
  conflicted: boolean;
  /** What a correct detector should notice. Used to explain a miss. */
  signal: string;
  build(): ZoneEvaluationStore;
}

const S0 = { stage: "stage0" as const };
const S1 = (branch: string) => ({ stage: "stage1" as const, branch });

function well(api = "42-497-31234") {
  return createZoneEvaluation({
    api, name: "Test 1", operator: "Test Operator", county: "Wise", district: "09",
  });
}

function resolvedDatum(s: ZoneEvaluationStore) {
  s.setDatum(S0, { kbFt: 1204, glFt: 1190, reference: "KB", source: "LAS ~PARAMETER", resolved: true });
}

export const CASES: LabelledCase[] = [
  {
    name: "datum disagreement between the LAS and the RRC record",
    conflicted: true,
    signal: "datum.resolved is false and two sources give different KB",
    build() {
      const s = well();
      resolvedDatum(s);
      s.setDatum(S1("rrc"), { kbFt: 1218, glFt: 1190, reference: "KB", source: "RRC W-2", resolved: true });
      return s;
    },
  },
  {
    name: "Sw reported as a point value with no Rw provenance",
    conflicted: true,
    signal: "a computed sw whose rw input has source null",
    build() {
      const s = well();
      resolvedDatum(s);
      s.addComputed(S1("calculators"), {
        field: "sw", value: 0.38, unit: "v/v",
        inputs: [
          { name: "rt", value: 22, source: "RT" },
          { name: "rw", value: 0.05, source: null },
          { name: "phi", value: 0.15, source: "computed:phiD" },
        ],
        method: "Archie a=1 m=2 n=2", confidence: null,
      });
      return s;
    },
  },
  {
    name: "an offset pick projected onto a well whose datum is unresolved",
    conflicted: true,
    signal: "offset.datumResolved false while a structural comparison is implied",
    build() {
      const s = well();
      s.setDatum(S0, { kbFt: null, glFt: 1190, reference: "GL", source: "LAS ~PARAMETER", resolved: false });
      s.addOffset(S1("offsets"), {
        api: "42-497-30001", distanceFt: 1320,
        picks: [{ formation: "Caddo", depth: s.depth(4090, "KB", { api: "42-497-30001" }) }],
        dst: [], datumResolved: false,
      });
      s.addComputed(S1("calculators"), {
        field: "standoff", value: 12, unit: "ft",
        inputs: [
          { name: "perfTop", value: 4110, source: "user" },
          { name: "contact", value: 4122, source: "offset:42-497-30001" },
        ],
        method: "subsea difference", confidence: null,
      });
      return s;
    },
  },
  {
    name: "a stated recollection contradicting a documented DST result",
    conflicted: true,
    signal: "evidence with kind stated and kind documented that cannot both hold",
    build() {
      const s = well();
      resolvedDatum(s);
      s.addEvidence(S1("user"), {
        claim: "4110-18 tested oil, they just never completed it",
        sourceId: "operator-call-2026-03", kind: "stated",
      });
      s.addEvidence(S1("offsets"), {
        claim: "DST 4110-4118 recovered salt water, no shows",
        sourceId: "rrc-dst-1954", kind: "documented",
      });
      return s;
    },
  },
  {
    name: "a porosity above the physical limit for the stated matrix",
    conflicted: true,
    signal: "computed phiD of 0.46 against a 2.71 matrix assumption",
    build() {
      const s = well();
      resolvedDatum(s);
      s.addAssumption(S0, {
        field: "matrix_density", value: 2.71, source: "default",
        basis: "limestone matrix", overridable: true,
      });
      s.addComputed(S0, {
        field: "phiD", value: 0.46, unit: "v/v",
        inputs: [
          { name: "rhob", value: 1.92, source: "RHOB" },
          { name: "rhoMatrix", value: 2.71, source: "assumption:matrix_density" },
        ],
        method: "density porosity", confidence: null,
      });
      return s;
    },
  },
  {
    name: "a clean well: resolved datum, sourced Rw, consistent offsets",
    conflicted: false,
    signal: "nothing disagrees",
    build() {
      const s = well();
      resolvedDatum(s);
      s.addAssumption(S0, {
        field: "matrix_density", value: 2.71, source: "default",
        basis: "limestone matrix", overridable: true,
      });
      s.addComputed(S0, {
        field: "phiD", value: 0.152, unit: "v/v",
        inputs: [
          { name: "rhob", value: 2.45, source: "RHOB" },
          { name: "rhoMatrix", value: 2.71, source: "assumption:matrix_density" },
        ],
        method: "density porosity", confidence: 0.8,
      });
      s.addComputed(S0, {
        field: "sw", value: 0.41, unit: "v/v",
        inputs: [
          { name: "rw", value: 0.048, source: "Pickett plot, this well" },
          { name: "rt", value: 22, source: "RT" },
          { name: "phi", value: 0.152, source: "computed:phiD" },
        ],
        method: "Archie a=1 m=2 n=2", confidence: 0.7,
      });
      s.addOffset(S1("offsets"), {
        api: "42-497-30001", distanceFt: 2640,
        picks: [{ formation: "Caddo", depth: s.depth(4090, "KB", { api: "42-497-30001" }) }],
        dst: [], datumResolved: true,
      });
      return s;
    },
  },
  {
    name: "a clean well with an open item that is not a contradiction",
    conflicted: false,
    signal: "an unanswered question is not two facts disagreeing",
    build() {
      const s = well();
      resolvedDatum(s);
      s.addOpen(S1("offsets"), {
        question: "No DSTs within a mile; the nearest control is 1.8 miles east",
        blocking: false,
      });
      return s;
    },
  },
  {
    name: "a thin well: curves read, nothing computed yet",
    conflicted: false,
    signal: "too little to disagree about",
    build() {
      const s = well();
      resolvedDatum(s);
      for (const m of ["GR", "RHOB", "NPHI", "RT"]) {
        s.addCurve(S0, { mnemonicRaw: m, mnemonicCanonical: m, unit: null, source: "las", flagged: false });
      }
      return s;
    },
  },
];

export const CONFLICTED = CASES.filter((c) => c.conflicted);
export const CLEAN = CASES.filter((c) => !c.conflicted);
