/**
 * Push the corpus's rendered figures into the `geology-figures` bucket.
 *
 * The images cannot ship in a function bundle — 161 MB of them took the geology
 * function to 249 MB against a 250 MB ceiling — so `figure-image.ts` reads disk
 * in development and this bucket in production. Run this after any
 * `build_figures.py` run, and before the deploy that depends on it.
 *
 * Keys mirror the corpus layout exactly (`figures/<section>/<slug>/pNNNN.jpg`),
 * which is the same string `figure_fetch` returns, so nothing has to translate
 * between the table and the bucket.
 *
 * Idempotent: an object whose size already matches is skipped, so a re-run after
 * a partial upload costs one HEAD per figure rather than a re-transfer.
 *
 *   SUPABASE_PROJECT_ID=... SUPABASE_SECRET_KEY=... node scripts/upload-geology-figures.mjs
 *   ... --force     re-upload everything, ignoring what is already there
 */
import { createClient } from "@supabase/supabase-js";
import { readdir, readFile, stat } from "node:fs/promises";
import { readFileSync as fsReadFileSync } from "node:fs";
import path from "node:path";

const BUCKET = "geology-figures";
const CORPUS = process.env.GEOLOGY_CORPUS_ROOT ?? path.join(process.cwd(), "geology-corpus");
const FIGURES = path.join(CORPUS, "figures");
const FORCE = process.argv.includes("--force");
const CONCURRENCY = 8;

/**
 * Read `.env` the way the rest of the repo's scripts and exec tests do.
 *
 * Without this the script only ran with the variables already exported, which is
 * not how anyone has this project set up — the first real invocation failed on
 * exactly that.
 */
function loadEnvFiles() {
  for (const file of [".env", ".env.local"]) {
    let text;
    try {
      text = fsReadFileSync(path.join(process.cwd(), file), "utf8");
    } catch {
      continue;
    }
    for (const line of text.split("\n")) {
      const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^['"]|['"]$/g, "");
    }
  }
}

function client() {
  loadEnvFiles();
  const id = process.env.SUPABASE_PROJECT_ID;
  const key = process.env.SUPABASE_SECRET_KEY;
  const url = process.env.SUPABASE_URL ?? (id ? `https://${id}.supabase.co` : null);
  if (!url || !key) {
    console.error("set SUPABASE_PROJECT_ID (or SUPABASE_URL) and SUPABASE_SECRET_KEY");
    process.exit(1);
  }
  return createClient(url, key, { auth: { persistSession: false } });
}

async function* walk(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(full);
    else if (entry.isFile() && entry.name.endsWith(".jpg")) yield full;
  }
}

async function existingSizes(sb) {
  /** One listing per leaf directory; cheaper than a HEAD per object. */
  const sizes = new Map();
  const queue = ["figures"];
  while (queue.length) {
    const prefix = queue.pop();
    const { data, error } = await sb.storage.from(BUCKET).list(prefix, { limit: 1000 });
    if (error) throw error;
    for (const item of data ?? []) {
      const key = `${prefix}/${item.name}`;
      if (item.id === null) queue.push(key);
      else sizes.set(key, item.metadata?.size ?? -1);
    }
  }
  return sizes;
}

async function main() {
  const sb = client();
  const files = [];
  for await (const file of walk(FIGURES)) files.push(file);
  if (!files.length) {
    console.error(`no figures under ${FIGURES}; run scripts/build_figures.py first`);
    process.exit(1);
  }

  const known = FORCE ? new Map() : await existingSizes(sb).catch(() => new Map());
  let uploaded = 0;
  let skipped = 0;
  let failed = 0;

  const queue = [...files];
  await Promise.all(
    Array.from({ length: CONCURRENCY }, async () => {
      for (let file = queue.pop(); file; file = queue.pop()) {
        const key = path.relative(CORPUS, file).split(path.sep).join("/");
        const size = (await stat(file)).size;
        if (known.get(key) === size) {
          skipped++;
          continue;
        }
        const { error } = await sb.storage
          .from(BUCKET)
          .upload(key, await readFile(file), {
            contentType: "image/jpeg",
            upsert: true,
          });
        if (error) {
          failed++;
          console.error(`failed ${key}: ${error.message}`);
        } else {
          uploaded++;
          if (uploaded % 25 === 0) console.log(`  ${uploaded} uploaded...`);
        }
      }
    })
  );

  console.log(
    `${files.length} figures: ${uploaded} uploaded, ${skipped} already current, ${failed} failed`
  );
  process.exit(failed ? 1 : 0);
}

await main();
