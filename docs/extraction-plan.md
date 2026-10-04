# Geology extraction plan

Move Wildcat's geology agent, its knowledge base, its Python tools, and the RRC data layer into
this repo, so collaborators can work on geology without access to the rest of Wildcat.
Application wiring (chat routes, UI, billing) is out of scope for now.

## Principle: isolated code, connected runtime

Geology is not a standalone product. In production it must see the user's wells and files and
the RRC mirror, and Orion must see geology. The repo boundary isolates **code**, not **data**:

- This repo owns the subsurface domain: the engine, prompts, corpus, Python tools, and RRC
  queries and tools.
- Anything that belongs to Wildcat (org files, wells, auth, Orion's tools) is reached through
  **ports**: typed interfaces declared here and implemented by Wildcat.
- Collaborators run the same engine against a **dev adapter**: local fixtures, stub auth, and a
  read-only RRC connection.
- After cutover, each moved module has exactly one copy, here. Wildcat imports it and keeps
  nothing in parallel.

## Status (2026-10-04)

Phases 0-4 are done. Phase 5 (Wildcat cutover) has not started, and Wildcat is unchanged.

- **Python:** `npm run test:py` passes (230 tests). `scripts/geology-tools-dev.py` answers
  `las_header` on a real log.
- **TS:** `npm test` runs vitest (672 pass, 29 skip themselves without a key or service) plus
  the Node runner suite in `tests/geology/` (255 pass, 3 fail).
  - The 3 failures fail identically in Wildcat today, so they predate the extraction. They are
    stale expectations: an RRC tool count of 16 vs 22, and a read-only list that predates
    `get_well_rrc_record` / `get_lease_rrc_record`.
- **Typecheck and lint:** `tsc --noEmit` and eslint on the moved code are clean.
- **Catalog:** `npm run build:catalog` regenerates a `tool-catalog.json` byte-identical to
  Wildcat's.
- **Live RRC:** `rrc_well` through `devHost` returns Sky Heighten #1 from Tiger.
- **Still owner actions:**
  - Create the `geology_ro` role on Tiger. The remote DB is off limits to the agent; until the
    role exists, the local `.env` uses Wildcat's credential.
  - Decide on Git LFS for figures. `git-lfs` is not installed on this VPS, so
    `geology-corpus/figures/` is gitignored for now.

## Layout as built

Wildcat's paths are kept wherever possible, so the Python, the corpus defaults, the build
scripts and the eventual cutover diff need no path changes.

```
geology/
  package.json, tsconfig.json, vitest.config.ts, vercel.json, .npmrc (legacy-peer-deps)
  .env.example            .env is local only, gitignored
  api/geology.py          Python tool service (Vercel function; dev: npm run dev:tools)
  api/_geology/**         stdlib-only tools + build_toc.py + test_*.py
  geology-corpus/         knowledge-base, toc (+ dot files), tables, figures (gitignored)
  data/nicknames.csv      source for src/lib/rrc/nicknames.generated.ts
  scripts/                catalog, figures upload, nicknames, corpus/table builders
  src/lib/host.ts         the ports (GeologyHost, setGeologyHost, geologyHost)
  src/lib/host-dev.ts     dev host: LAS from a directory, signed in, no user data
  src/lib/ai/geology/**   engine, prompts, tool-catalog.json
  src/lib/ai/geology-kb-tools.ts, rrc-tools.ts, rrc/**, tool-args.ts, catalog-tool.ts
  src/lib/scout/          rrc-*.ts, cad*.ts, counties, allocate-months, injection-series,
                          county-api-range.ts (moved out of Wildcat's focus-where.ts)
  src/lib/rrc/            well-share, record-split, operator-match, lease-history-series,
                          nicknames.generated
  src/lib/wells/arps.ts, src/lib/analytics/ema.ts
  tests/geology/          Node-runner suite + real LAS fixtures
```

**Imports.** Library code under `src/lib` uses relative imports only. Wildcat will compile it
as a package, and there `@/` resolves to Wildcat's own `src`. The `@/` alias is for this repo's
app and tests.

**Removed from the copy (they test Wildcat, not geology; they stay there):**
- `las-subject.db.test.ts` (Wildcat's files table).
- `rrc/__tests__/analyze-model-in-loop.exec.test.ts` (Orion's model loop).
- The Orion-registration cases in the two `geology-kb-tools` tests (Orion's catalog and system
  prompt). Their tool-behaviour cases remain here.

## Phase 0: scaffold

> Phases 0-4 are the original plan, kept for the record. Where their paths differ, **Layout as
> built** wins: `python/` is `api/`, `corpus/` is `geology-corpus/`, `src/engine` and `src/rrc` are
> `src/lib/ai/geology` and `src/lib/ai/rrc`, and `ports.x` is `geologyHost().x`.

1. Create `package.json` with the same major versions as Wildcat: `ai@^6`, `@ai-sdk/anthropic@^3`,
   `zod@^4`, `pg@^8`, `vitest@^3`, `tsx`, `typescript`.
2. Set up `tsconfig.json` (strict, `moduleResolution: bundler`) and `vitest.config.ts`.
3. Write `.gitignore`: `.env*` except `.env.example`, `node_modules`, `corpus/figures/` until
   LFS is decided, and `/tmp` artifacts.
4. Run `git lfs track "corpus/figures/**/*.jpg"` if figures go in the repo (Phase 1, step 4).

## Phase 1: corpus and Python tools (copy, no code changes)

**Sources.** The source of truth is Wildcat's copy, which has drifted ahead of
`~/dev/geology-agent/`: it adds the `classic`, `missedpay`, `multiwell` and `rockfluid` tool
modules and a revised `kb.py`. The upstream copy is still needed for the table build scripts,
which exist only there.

1. Copy `wildcat/geology-corpus/{knowledge-base,toc,tables}` to `corpus/`, including the dot
   files in `toc/` (`.doc-hashes.json`, `.segments.jsonl`, `.cards.jsonl`, `.kb-index.json`,
   `.tool-registry.json`). `corpus.ts` hash-checks documents against `.doc-hashes.json`.
2. Copy `wildcat/api/_geology/**` and `api/geology.py` to `python/`, and
   `scripts/geology-tools-dev.py` to `python/dev_server.py`. The tools are stdlib-only (see
   `requirements.txt`).
3. Copy the build scripts to `scripts/`:
   - From Wildcat: `build-geology-catalog.py`, `upload-geology-figures.mjs`.
   - From `geology-agent/scripts/`: `build_toc.py`, `build_formation_aliases.py`,
     `pull_rrc_formations.py`, `pull_rrc_reservoirs.py`, `build_strat_column.py`,
     `build_basin_priors.py`, `build_figures.py`.
   - Fix their paths to the new layout.
4. Figures (161M, 319 JPGs) are gitignored in Wildcat today. Decision: commit them via Git LFS
   so a fresh clone works offline. The `geology-figures` storage bucket stays the production
   source.
5. Decide what happens to the raw upstream material (`geology-agent/knowledge-base` is 610M with
   PDFs, OCR and originals). Recommendation: leave it out of this repo. Only the derived corpus
   ships. Document where the originals live in `corpus/README.md`.
6. Verify:
   - `python -m pytest python/_geology` (the 7 `test_*.py` files) passes.
   - `python python/dev_server.py` answers a `las_header` POST on `127.0.0.1:8781`.
   - `python scripts/build-geology-catalog.py` regenerates a `tool-catalog.json` identical to
     Wildcat's committed one, which proves the copied registry matches.

## Phase 2: RRC layer

Move the whole RRC toolset, not only `rrc/tools/geology.ts`. The geology prompt interpolates
`RRC_CATALOG`, which pulls in all 15 tool modules, and Orion uses the same tools.

**Move as-is (pure, or depend only on `pg` / each other):**

| Wildcat path | Notes |
|---|---|
| `src/lib/ai/rrc/**` (incl. `tools/*`, tests) | 15 tool modules + datum, offsets, series, math, registry |
| `src/lib/scout/rrc-db.ts` | `pg` pool on `RRC_DATABASE_URL`; replace the `perf/timeline` `timed()` wrapper with an optional hook |
| `src/lib/scout/rrc-queries.ts`, `rrc-types.ts`, `rrc-districts.ts`, `rrc-uic.ts`, `rrc-people.ts` | 3,993 + 1,077 lines of queries/types |
| `src/lib/scout/cad.ts`, `cad-queries.ts`, `counties.ts`, `allocate-months.ts`, `injection-series.ts` | no `@/` imports |
| `src/lib/rrc/well-share.ts`, `record-split.ts`, `operator-match.ts` | `record-split` depends only on rrc-db/districts |
| `src/lib/wells/arps.ts`, `src/lib/analytics/ema.ts` | `arps` imports only a **type** from `wells/wells`; inline `ProductionPoint` |
| `src/lib/ai/tool-args.ts`, `catalog-tool.ts` | no `@/` imports |

**Cut at a port (these touch Wildcat's data or UI):**

| Coupling | Where | Treatment |
|---|---|---|
| `assertSignedIn` | `rrc-tools.ts:5`, `rrc/dispatch.ts:4` | `ports.auth.assertSignedIn()` |
| `getRrcLease` / `getRrcWell` (`rrc/link.ts`) | `rrc-tools.ts:6` | links RRC records to the org's own wells via Supabase, so it is user data. Expose as `ports.wells.linkRrc*`; `link.ts` stays in Wildcat |
| `scout-view-spec` + `MapMode` from `components/scout/map-filters` | `rrc-tools.ts:51` | UI map-view tools. They stay in Wildcat as host tools; this repo exports the rest of `rrcTools()` |

Verify: all moved `*.test.ts` pass here (`rrc/**`, `rrc-uic.test.ts`) with no `@/lib/` import
left that resolves outside this repo (`grep -r '"@/' src` must be empty).

## Phase 3: geology engine

1. Copy `src/lib/ai/geology/**` to `src/engine/` (37 files, `tool-catalog.json`, tests), and
   `geology-kb-tools.ts` (+ its two tests) to `src/kb-tools.ts`.
2. Rewire imports. The core stages already import only each other plus `ai`,
   `@ai-sdk/anthropic` and `zod`. The cuts:

| File | Coupling | Treatment |
|---|---|---|
| `orion-bridge.ts:21` | `orionTools()` from Wildcat | becomes `ports.hostTools()`: Wildcat hands in Orion's tools, dev adapter returns `{}` |
| `rrc-bridge.ts:34-35`, `tool-registry.ts:19` | `rrcTools`, `rrcAnalysisTool` | import from `src/rrc/` (now local) |
| `contract-tools.ts:46` | `offsetWellbores` | local after Phase 2 |
| `fable-prompt.ts:22` | `RRC_CATALOG` | local after Phase 2 |
| `python-tools.ts:47` | `loadText` from `kb/structured` (org `files` table) | `ports.files.loadText(id)`; the `ReadLas` param already exists |
| `entry.ts:114` | lazy `getLasFiles` from `kb/files` | `ports.files.listLas()`; the `lasFiles` input already exists |
| `figure-image.ts:23` | `getSupabaseAdmin` for the `geology-figures` bucket | `ports.figures?.read(key)`, disk first as today |
| `geology-kb-tools.ts:58-59` | `scout/counties` | local after Phase 2 |
| `subject.ts:49` | hardcoded Orion tool names `read_las_full`, `get_curves_data`, `get_curve_data` | `ports.lasToolNames` with these as defaults |

3. The Python service URL resolution in `python-tools.ts:64-80` (`GEOLOGY_TOOLS_URL`, else
   `VERCEL_URL`, else `127.0.0.1:8781`) is kept unchanged.

## Ports (as built: `src/lib/host.ts`)

The host is installed once at startup with `setGeologyHost(host)` and read with `geologyHost()`.
It is held on `globalThis` so duplicate Next bundles share it. Unset, it is `UNWIRED`: no files,
no linked wells, and an auth gate that throws, so a forgotten wiring cannot expose the RRC
mirror.

```ts
interface GeologyHost {
  auth: { assertSignedIn(): Promise<void> };                 // gates every RRC tool
  files: {
    listLas(): Promise<{ id: string; name: string }[]>;      // was kb/files getLasFiles
    loadText(id): Promise<{ name; text } | null>;            // was kb/structured loadText
  };
  wells: {
    rrcApi(wellId): Promise<string | null>;                  // was rrc/link storedApi
    rrcLeaseKey(leaseId): Promise<RrcLeaseKey | null>;       // was rrc/link resolveLeaseKey
  };
  hostTools?(): Record<string, unknown>;                     // was orionTools()
  figures?: { read(key): Promise<Buffer | null> };           // was the geology-figures bucket
  lasToolNames?: readonly string[];                          // default: Orion's LAS tool names
  timed?(source, label, fn): Promise<T>;                     // was perf/timeline timed()
}
```

`wells` returns only identifiers. The dossiers are built here from the RRC queries, so the
host never needs to know RRC and this repo never learns the host's schema. `scout_set_view`
(the Recon map tool) and `scoutMapOnScreen` were removed from `rrc-tools.ts`. They stay in
Wildcat as its own tool.

## Phase 4: dev adapter and tests

1. Write `src/dev/adapter.ts`:
   - `auth`: no-op.
   - `files`: reads `tests/fixtures/*.las`.
   - `wells`: returns null.
   - `hostTools`: `{}`.
2. Port the exec tests (`harness-e2e`, `regional-screening`, `figure-vision`) to the dev adapter.
   `las-subject.db.test.ts` depends on Wildcat's files table and stays in Wildcat as an adapter
   contract test.
3. Fixtures must be real field logs, not invented clean ones. Take them from the LAS files the
   existing tests already use.

## RRC database access

Collaborators get their own read-only role on the Tiger RRC mirror, never Wildcat's
`RRC_DATABASE_URL`. The code reads the `rrc` and `cad` schemas (`wildcat.well_rate` is used only
by Recon map code, which does not move).

```sql
create role geology_ro login password '...';
grant usage on schema rrc, cad to geology_ro;
grant select on all tables in schema rrc, cad to geology_ro;
alter default privileges in schema rrc, cad grant select on tables to geology_ro;
```

Use one role per collaborator if access needs to be revoked individually. The RRC pipeline
(`~/dev/rrc-data`, cron 13:00 UTC) creates new tables; the default-privileges line covers them
only for tables created by the role that ran it, so run it as the pipeline's owner role.

## Environment

`.env.example` (no Wildcat secrets):

```
ANTHROPIC_API_KEY=          # collaborator's own key
GEOLOGY_HARNESS=1
GEOLOGY_CORPUS_ROOT=        # optional; defaults to ./corpus
GEOLOGY_TOOLS_URL=http://127.0.0.1:8781
RRC_DATABASE_URL=           # geology_ro role, read-only
```

Not copied: `SUPABASE_*`, `ARCHON_*`, and everything else in Wildcat's `.env`.
`upload-geology-figures.mjs` needs `SUPABASE_URL` and `SUPABASE_SECRET_KEY`. Only the owner runs
it, so these stay out of `.env.example`.

## Phase 5: Wildcat cutover (after this repo is green)

Listed so the extraction is shaped for it; executed later.

1. Wildcat adds `"geology": "github:numenarankin/wildcat-geology#vX.Y.Z"` and
   `transpilePackages: ["geology"]`. Use `npm link` for side-by-side development.
2. Wildcat implements `GeologyHost` once (Supabase files, `rrc/link`, `assertSignedIn`,
   `orionTools`) and passes it at the call sites: `api/chat/route.ts`,
   `api/voice-chat/route.ts`, `ai/tools.ts:1274`, `pipeline/rrc-gather.ts`.
3. Repoint about 40 Wildcat files that import `@/lib/ai/rrc*` or `@/lib/scout/rrc-*` (Recon
   pages, scout API routes, modals, `disposal/permit.ts`, `settings/rrc-operators.ts`,
   onboarding) to the package. Then delete the moved files from Wildcat.
4. Corpus tracing: update `next.config.ts` `outputFileTracingIncludes` for `/api/chat` to the
   package's `corpus/` path.
5. Python: deploy this repo's `api/geology.py` (with `vercel.json`) as its own Vercel project and set Wildcat's `GEOLOGY_TOOLS_URL` to
   it. Then remove `api/geology.py`, `api/_geology/`, and the `functions` entry in `vercel.json`.
   This works because the service is already HTTP-only, and LAS text is posted inline.
6. Remove `wildcat/geology-corpus/` and `scripts/*geology*`.

## Freeze during extraction

From Phase 1 until cutover, geology and RRC changes land **here only**. Any urgent Wildcat-side
fix in a moved file is ported here the same day, otherwise the two copies drift and the cutover
silently reverts it.

## Open decisions

- Figures in Git LFS (recommended) or fetched from the bucket on first run.
- Whether the Recon map-view tools (`scout-view-spec`) should eventually move too, if the
  geology repo later grows a frontend.
