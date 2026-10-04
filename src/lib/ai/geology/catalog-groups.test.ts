import { describe, it, expect } from "vitest";
import { CATALOG_ENTRIES, PETROPHYSICS_CATALOG, catalogNames } from "./tool-catalog";

/**
 * The generated catalog, checked as a whole.
 *
 * `tool-catalog.json` is regenerated from live Python signatures by
 * `scripts/build-geology-catalog.py`, and the group letters come from a corpus
 * sidecar rather than from the code. That is two places a new tool can fall
 * through: written and registered but absent from the sidecar, so the model is
 * never told it exists. These assertions are what makes that loud.
 */

/** Groups M through R, added for the catalog expansion. See docs/plans. */
const NEW_GROUPS: Record<string, string[]> = {
  M: [
    "hcpv_thickness",
    "volumetrics",
    "recovery_factor",
    "volumetrics_probabilistic",
    "archie_sensitivity",
    "propagate_uncertainty",
  ],
  N: [
    "permeability_estimate",
    "kv_kh_ratio",
    "relative_permeability",
    "fractional_flow",
    "capillary_pressure",
    "saturation_height",
    "free_water_level",
  ],
  O: ["curve_normalize", "depth_shift", "auto_correlate", "isopach", "structure_map", "offset_consistency"],
  P: [
    "bulk_volume_water",
    "movable_hydrocarbon_index",
    "rwa_method",
    "mn_plot",
    "mid_plot",
    "multimineral_solve",
    "thomas_stieber",
  ],
  Q: ["thin_bed_correction", "low_resistivity_screen", "rock_typing"],
  R: [
    "vogel_ipr",
    "nodal_analysis",
    "buildup_kh_skin",
    "chan_diagnostic",
    "wor_xplot",
    "material_balance",
    "artificial_lift_screen",
  ],
};

describe("the generated petrophysics catalog", () => {
  it("carries every tool of the new groups", () => {
    const names = catalogNames();
    const absent = Object.values(NEW_GROUPS)
      .flat()
      .filter((n) => !names.has(n));
    expect(absent).toEqual([]);
  });

  it("files each new tool under the group it belongs to", () => {
    // A tool in the catalog under the wrong letter still reaches the model, so
    // this is about the document staying legible rather than about dispatch.
    for (const [group, tools] of Object.entries(NEW_GROUPS)) {
      for (const name of tools) {
        const entry = CATALOG_ENTRIES.find((t) => t.name === name);
        expect(entry?.group, name).toBe(group);
      }
    }
  });

  it("gives every entry a summary and a real module", () => {
    // The summary IS the description the model gets. An entry without one is a
    // tool it can see and cannot judge whether to call.
    const thin = CATALOG_ENTRIES.filter((t) => !t.summary || !t.module).map((t) => t.name);
    expect(thin).toEqual([]);
  });

  it("has no duplicate names", () => {
    const names = CATALOG_ENTRIES.map((t) => t.name);
    expect(new Set(names).size).toBe(names.length);
  });

  it("renders every entry into the prompt block", () => {
    for (const entry of CATALOG_ENTRIES) {
      expect(PETROPHYSICS_CATALOG).toContain(entry.name);
    }
  });
});
