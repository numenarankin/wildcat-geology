/**
 * The claim this whole figure path rests on, tested against a real model.
 *
 * `figure_fetch` exists because a map described once at ingest loses the detail a
 * screen turns on. That argument is only worth anything if the model can
 * actually read the sheet when it is handed the pixels — so this takes a real
 * figure out of the shipped corpus, reads it with the same `readFigureImage` the
 * tool bridge uses, sends it to the same model Stage 3 runs on, and checks the
 * answer against what the *index* says is on that sheet.
 *
 * The index entry is the oracle, and it is an independent one: it was written by
 * a different model in a different pass at build time, from the same page. If
 * vision were broken, or the image were the wrong page, or the attachment were
 * silently dropped, the two would not agree.
 *
 * GATED (RUN_LIVE=1 + ANTHROPIC_API_KEY) like the other exec suites, since it
 * costs tokens.
 */
import { describe, expect, it } from "vitest";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { anthropic } from "@ai-sdk/anthropic";
import { generateText } from "ai";
import { readFigureImage } from "../figure-image";
import { FABLE_MODEL } from "../stage3-reason";

const RUN_LIVE = process.env.RUN_LIVE === "1" && !!process.env.ANTHROPIC_API_KEY;
const CORPUS = process.env.GEOLOGY_CORPUS_ROOT ?? path.join(process.cwd(), "geology-corpus");

interface Figure {
  figure_id: string;
  kind: string;
  title: string;
  shows: string;
  counties: string[];
  formations: string[];
  image_path: string;
}

async function figures(): Promise<Figure[]> {
  const raw = await readFile(path.join(CORPUS, "tables", "figures.json"), "utf8");
  return (JSON.parse(raw) as { figures: Figure[] }).figures;
}

describe.skipIf(!RUN_LIVE)("a corpus figure reaches the model as an image", () => {
  it("reads a map it was never told the contents of", async () => {
    const all = await figures();
    // A contoured map with named formations: the kind of sheet the tool exists
    // for, and one whose content is checkable against the index.
    const sheet = all.find(
      (f) =>
        (f.kind === "isopach_map" || f.kind === "structure_map") &&
        f.formations.length > 0 &&
        f.title.length > 10
    );
    expect(sheet, "no contoured map with named formations in the index").toBeTruthy();

    const data = await readFigureImage({
      path: sheet!.image_path,
      mediaType: "image/jpeg",
    });
    expect(data, `could not read ${sheet!.image_path}`).toBeTruthy();

    // The same provider bridge Stage 3 streams through, so a provider-level
    // change that dropped the attachment would fail here too.
    const response = await generateText({
      model: anthropic(FABLE_MODEL),
      maxOutputTokens: 2000,
      messages: [
        {
          role: "user",
          content: [
            { type: "image", image: data!, mediaType: "image/jpeg" },
            {
              type: "text",
              // Deliberately blind: the model is told nothing about the sheet, so
              // agreement with the index cannot come from the prompt.
              text:
                "This is one page from a geological report. Say what kind of figure it is, " +
                "which stratigraphic units it names, and which counties or region it covers. " +
                "If you cannot see an image at all, say exactly: NO IMAGE RECEIVED.",
            },
          ],
        },
      ],
    });

    const answer = response.text.toLowerCase();

    expect(answer).not.toContain("no image received");
    expect(answer.length).toBeGreaterThan(80);

    // The independent-oracle check: at least one unit the build pass read off
    // this page is named by a model that was shown only the pixels.
    const named = sheet!.formations.filter((unit) => {
      const head = unit.toLowerCase().split(/[\s(]/)[0];
      return head.length > 3 && answer.includes(head);
    });
    expect(
      named.length,
      `model answer did not name any of ${JSON.stringify(sheet!.formations)}; got: ${answer.slice(0, 400)}`
    ).toBeGreaterThan(0);
  }, 180_000);
});
