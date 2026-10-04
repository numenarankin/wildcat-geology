/**
 * Fixture tools for the geology harness.
 *
 * These are REAL `GeologyTool` objects — real names, real zod schemas, real
 * registry, real validation on the way in and out. Only the DATA is fixed. The
 * harness code under test is never replaced, so when the catalog lands, swapping
 * `fixtureRegistry()` for the real registry should change no harness code and no
 * assertion in these tests. If it does, the boundary in harness-implementation.md
 * §2 was drawn wrong, and that is worth finding out here rather than later.
 *
 * The wells are shaped to exercise Stage 0's decisions, not to be realistic:
 * one clean, one with no EKB in the header, one where the LAS and the RRC record
 * disagree about kelly bushing.
 */
import { z } from "zod";
import {
  TOOL,
  calculatorsSchema,
  completionRecordSchema,
  continuitySchema,
  curveSuiteSchema,
  curvesSchema,
  headerSchema,
  holeQualitySchema,
  kbLookupSchema,
  mnemonicSchema,
  noArgs,
  offsetsInputSchema,
  offsetsSchema,
  type CompletionRecord,
  type HeaderFacts,
} from "@/lib/ai/geology/contracts";
import { ToolRegistry, type GeologyTool } from "@/lib/ai/geology/registry";

export const CLEAN_API = "42-497-31234";
export const NO_EKB_API = "42-497-31235";
export const DATUM_FIGHT_API = "42-497-31236";

const HEADERS: Record<string, HeaderFacts> = {
  [CLEAN_API]: {
    api: CLEAN_API, name: "Repass 1", operator: "Test Operator", county: "Wise", district: "09",
    kbFt: 1204, glFt: 1190, epdFt: 1204, reference: "KB",
    latitude: 33.1234, longitude: -97.6543,
    startFt: 100, stopFt: 5000, stepFt: 0.5, nullValue: -999.25,
  },
  // No EKB and no EGL: the datum cannot be resolved from the file at all.
  [NO_EKB_API]: {
    api: NO_EKB_API, name: "Andrews 2", operator: "Test Operator", county: "Wise", district: "09",
    kbFt: null, glFt: null, epdFt: null, reference: null,
    latitude: 33.2, longitude: -97.6,
    startFt: 200, stopFt: 4800, stepFt: 0.5, nullValue: -999.25,
  },
  // Header says 1204, the RRC record says 1218. Fourteen feet is not rounding.
  [DATUM_FIGHT_API]: {
    api: DATUM_FIGHT_API, name: "Contested 3", operator: "Test Operator", county: "Wise", district: "09",
    kbFt: 1204, glFt: 1190, epdFt: 1204, reference: "KB",
    latitude: 33.3, longitude: -97.5,
    startFt: 150, stopFt: 4900, stepFt: 0.5, nullValue: -999.25,
  },
};

/**
 * The identity Stage 0 is handed when the log was found by file id rather than
 * by API — `subjectIdentity()` returns `file:<id>`, because the real API only
 * exists once the header has been read. Every entry-level test reaches the well
 * path this way, so without a fixture under this key the header read throws and
 * the turn degrades to the corpus, which looks like a routing bug and is not.
 *
 * Same well as CLEAN_API on purpose: the header is what supplies the real API.
 */
export const FILE_SUBJECT_ID = "file-abc";
/**
 * A second identity, because the evaluation cache is process-wide and keyed on
 * the file id. Two tests that both succeed under one id are not independent: the
 * second reads the first's cached evaluation and never calls a tool, so a test
 * whose whole point is a failing tool layer would pass on a cache hit instead.
 */
export const FILE_SUBJECT_ID_ALT = "file-style";
for (const id of [FILE_SUBJECT_ID, FILE_SUBJECT_ID_ALT]) {
  HEADERS[`file:${id}`] = HEADERS[CLEAN_API];
}

const RRC: Record<string, CompletionRecord> = {
  // Agrees with the header to within half a foot — reporting precision, not a
  // second opinion.
  [CLEAN_API]: { api: CLEAN_API, kbFt: 1204.5, glFt: 1190, latitude: 33.1234, longitude: -97.6543, form: "W-2" },
  // The record has what the file lacks. This is the datum being RESOLVED by the
  // cross-check rather than contradicted by it.
  [NO_EKB_API]: { api: NO_EKB_API, kbFt: 1212, glFt: 1198, latitude: 33.2, longitude: -97.6, form: "W-2" },
  [DATUM_FIGHT_API]: { api: DATUM_FIGHT_API, kbFt: 1218, glFt: 1190, latitude: 33.3, longitude: -97.5, form: "W-2" },
};

/** GR/RHOB/NPHI/RT/CALI plus one mnemonic the dictionary does not know. */
const CURVES = [
  { mnemonic: "DEPT", unit: "F", description: "Depth" },
  { mnemonic: "GR", unit: "GAPI", description: "Gamma ray" },
  { mnemonic: "RHOB", unit: "G/C3", description: "Bulk density" },
  { mnemonic: "NPHI", unit: "V/V", description: "Neutron porosity" },
  { mnemonic: "RT", unit: "OHMM", description: "True resistivity" },
  { mnemonic: "CALI", unit: "IN", description: "Caliper" },
  { mnemonic: "XZ99", unit: null, description: "Vendor-specific" },
];

const DICTIONARY: Record<string, string> = {
  DEPT: "DEPT", GR: "GR", RHOB: "RHOB", NPHI: "NPHI", RT: "RT", CALI: "CALI",
};

/** Counts calls per tool, so tests can assert a cache hit skipped the work. */
export class CallCounter {
  readonly counts = new Map<string, number>();
  bump(name: string): void {
    this.counts.set(name, (this.counts.get(name) ?? 0) + 1);
  }
  get(name: string): number {
    return this.counts.get(name) ?? 0;
  }
  get total(): number {
    return [...this.counts.values()].reduce((a, b) => a + b, 0);
  }
  reset(): void {
    this.counts.clear();
  }
}

function tool<A, R>(t: GeologyTool<A, R>): GeologyTool<A, R> {
  return t;
}

export interface FixtureOptions {
  counter?: CallCounter;
  /** Milliseconds each tool waits, so ordering assertions mean something. */
  delayMs?: number;
  /** Make `las_header` throw, to test the failure path. */
  failHeader?: boolean;
  /** Tool names that should throw, to test that one branch cannot sink Stage 1. */
  failing?: readonly string[];
  /** Report the offset search as truncated. */
  offsetsTruncated?: boolean;
}

export function fixtureRegistry(opts: FixtureOptions = {}): ToolRegistry {
  const counter = opts.counter;
  const wait = async () => {
    if (opts.delayMs) await new Promise((r) => setTimeout(r, opts.delayMs));
  };
  const seen = (name: string) => {
    counter?.bump(name);
    if (opts.failing?.includes(name)) throw new Error(`${name} is unavailable`);
  };

  const registry = new ToolRegistry();

  registry.register(
    tool({
      name: TOOL.lasHeader,
      description: "Read the ~WELL and ~PARAMETER sections of the LAS.",
      inputSchema: noArgs,
      outputSchema: headerSchema,
      readOnly: true,
      callableBy: ["harness", "gatherer", "fable"],
      async execute(_args, ctx) {
        seen(TOOL.lasHeader);
        if (opts.failHeader) throw new Error("LAS header unreadable");
        await wait();
        const header = HEADERS[ctx.api];
        if (!header) throw new Error(`no fixture header for ${ctx.api}`);
        return { value: header, provenance: { tool: TOOL.lasHeader, inputs: {}, method: "LAS ~WELL/~PARAMETER read" } };
      },
    })
  );

  registry.register(
    tool({
      name: TOOL.lasCurves,
      description: "Curve inventory for the LAS.",
      inputSchema: noArgs,
      outputSchema: curvesSchema,
      readOnly: true,
      callableBy: ["harness", "fable"],
      async execute() {
        seen(TOOL.lasCurves);
        await wait();
        return {
          value: { curves: CURVES, rowCount: 9800 },
          provenance: { tool: TOOL.lasCurves, inputs: {}, method: "LAS ~CURVE read" },
        };
      },
    })
  );

  registry.register(
    tool({
      name: TOOL.mnemonicNormalize,
      description: "Map a raw curve mnemonic to its canonical name. Returns null when unknown; never guesses.",
      inputSchema: z.object({ raw: z.string(), unit: z.string().nullable() }),
      outputSchema: mnemonicSchema,
      readOnly: true,
      callableBy: ["harness", "fable"],
      async execute(args) {
        seen(TOOL.mnemonicNormalize);
        return {
          value: { raw: args.raw, canonical: DICTIONARY[args.raw] ?? null, unit: args.unit },
          provenance: { tool: TOOL.mnemonicNormalize, inputs: args, method: "owned mnemonic dictionary" },
        };
      },
    })
  );

  registry.register(
    tool({
      name: TOOL.rrcCompletionRecord,
      description: "The RRC W-2/G-1 completion record for this well.",
      inputSchema: noArgs,
      outputSchema: completionRecordSchema,
      readOnly: true,
      callableBy: ["harness", "gatherer", "fable"],
      async execute(_args, ctx) {
        seen(TOOL.rrcCompletionRecord);
        await wait();
        return {
          value: RRC[ctx.api] ?? { api: ctx.api, kbFt: null, glFt: null, latitude: null, longitude: null, form: null },
          provenance: { tool: TOOL.rrcCompletionRecord, inputs: { api: ctx.api }, method: "RRC completion query" },
        };
      },
    })
  );

  registry.register(
    tool({
      name: TOOL.curveSuite,
      description: "Standard curve math: phiD, phiN, crossplot porosity, Vsh, Archie Sw.",
      inputSchema: z.object({ curves: z.array(z.string()) }),
      outputSchema: curveSuiteSchema,
      readOnly: true,
      callableBy: ["harness"],
      async execute() {
        seen(TOOL.curveSuite);
        await wait();
        return {
          value: {
            values: [
              {
                // phiD = (2.71 - 2.45) / (2.71 - 1.00) = 0.152046...
                field: "phiD", value: 0.152, unit: "v/v",
                inputs: [
                  { name: "rhob", value: 2.45, source: "RHOB" },
                  { name: "rhoMatrix", value: 2.71, source: "assumption:matrix_density" },
                  { name: "rhoFluid", value: 1.0, source: "assumption:fluid_density" },
                ],
                method: "density porosity", confidence: 0.8,
              },
              {
                field: "vsh", value: 0.22, unit: "v/v",
                inputs: [
                  { name: "gr", value: 62, source: "GR" },
                  { name: "grClean", value: 25, source: "assumption:gr_clean" },
                  { name: "grShale", value: 190, source: "assumption:gr_shale" },
                ],
                method: "linear GR index", confidence: 0.6,
              },
            ],
            assumptions: [
              { field: "matrix_density", value: 2.71, basis: "limestone matrix, Bend Arch default" },
              { field: "gr_clean", value: 25, basis: "log minimum over the clean interval" },
            ],
          },
          provenance: { tool: TOOL.curveSuite, inputs: {}, method: "closed-form curve math" },
        };
      },
    })
  );

  registry.register(
    tool({
      name: TOOL.holeQuality,
      description: "Caliper against bit size; per-depth washout flags.",
      inputSchema: noArgs,
      outputSchema: holeQualitySchema,
      readOnly: true,
      callableBy: ["harness"],
      async execute() {
        seen(TOOL.holeQuality);
        await wait();
        return {
          value: {
            bitSizeIn: 7.875,
            washouts: [{ topFt: 4102, baseFt: 4110, maxExcessIn: 1.8 }],
            densityPorositySuppressed: true,
          },
          provenance: { tool: TOOL.holeQuality, inputs: {}, method: "caliper vs bit size" },
        };
      },
    })
  );

  registry.register(
    tool({
      name: TOOL.kbLookup,
      description: "Keyed dictionary reads: county to basin prior, lithology to matrix constant.",
      inputSchema: z.object({ county: z.string().nullable(), district: z.string().nullable() }),
      outputSchema: kbLookupSchema,
      readOnly: true,
      callableBy: ["harness", "gatherer", "fable"],
      async execute(args) {
        seen(TOOL.kbLookup);
        await wait();
        return {
          value: {
            assumptions: [{ field: "basin", value: "Fort Worth", basis: `county ${args.county} basin prior` }],
            facts: [{ claim: "Bend Arch traps are compartmentalized; a flat regional contact is the exception", sourceId: "geolex:bend-arch" }],
          },
          provenance: { tool: TOOL.kbLookup, inputs: args, method: "keyed dictionary" },
        };
      },
    })
  );

  registry.register(
    tool({
      name: TOOL.calculators,
      description: "Closed-form engineering calculations: Turner/Coleman, coning critical rate, gas gradient.",
      inputSchema: noArgs,
      outputSchema: calculatorsSchema,
      readOnly: true,
      callableBy: ["harness"],
      async execute() {
        seen(TOOL.calculators);
        await wait();
        return {
          value: {
            values: [
              {
                // Reported as a spread across published correlations, per the
                // catalog: several correlations, no single answer.
                field: "coning_critical_rate", value: { low: 38, high: 94 }, unit: "bbl/d",
                inputs: [
                  { name: "standoffFt", value: 12, source: "computed:standoff" },
                  { name: "kvkh", value: 0.1, source: "assumption:kvkh" },
                ],
                method: "Craft & Hawkins / Chaperon / Schols spread", confidence: null,
              },
            ],
          },
          provenance: { tool: TOOL.calculators, inputs: {}, method: "closed-form correlations" },
        };
      },
    })
  );

  registry.register(
    tool({
      name: TOOL.offsetsWithinRadius,
      description: "Offset wells within a radius, with their picks, DSTs and completions.",
      inputSchema: offsetsInputSchema,
      outputSchema: offsetsSchema,
      readOnly: true,
      callableBy: ["harness", "gatherer", "fable"],
      async execute(args) {
        seen(TOOL.offsetsWithinRadius);
        await wait();
        return {
          value: {
            offsets: [
              {
                api: "42-497-30001",
                distanceFt: 2640,
                picks: [{ formation: "Caddo", depthFt: 4090, reference: "KB" as const }],
                dst: [{ interval: "4110-4118", result: "salt water, no shows" }],
                datumResolved: true,
              },
            ],
            truncated: opts.offsetsTruncated ?? false,
          },
          provenance: { tool: TOOL.offsetsWithinRadius, inputs: args, method: "PostGIS radius query" },
        };
      },
    })
  );

  registry.register(
    tool({
      name: TOOL.continuityCheck,
      description: "Depth-wise consistency, curve splice detection, implausible transitions.",
      inputSchema: noArgs,
      outputSchema: continuitySchema,
      readOnly: true,
      callableBy: ["harness"],
      async execute() {
        seen(TOOL.continuityCheck);
        await wait();
        return {
          value: {
            findings: [
              { description: "curve splice at 3,200 ft: RHOB step of 0.18 g/cc across one sample", topFt: 3200, baseFt: 3200.5, severity: "suspect" as const },
            ],
          },
          provenance: { tool: TOOL.continuityCheck, inputs: {}, method: "depth-wise continuity scan" },
        };
      },
    })
  );

  return registry;
}
