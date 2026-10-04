/**
 * A scripted `GathererModel`.
 *
 * The seam it stands in for is judgment — which document bears on this question,
 * which segment answers it. Everything on the harness side of that seam (opening
 * the TOC, verifying the IDs exist, slicing verbatim text, deduping, budgeting)
 * is real code running for real here.
 *
 * `pickAll` is the useful default: it selects every document and every segment,
 * which exercises the whole retrieval path. The interesting variants are the
 * dishonest ones — a model that cites a document not in the corpus, or a segment
 * ID that does not exist — because dropping those in code is the discipline
 * being tested.
 */
import type { DocumentCard, SegmentEntry } from "@/lib/ai/geology/corpus";
import type { GathererModel, ToolRequest } from "@/lib/ai/geology/gatherer";

export interface ScriptOptions {
  /** What `splitQuestion` returns. Defaults to the prompt, unsplit. */
  subQuestions?: string[];
  /** Slugs to select. Defaults to every card. */
  documents?: string[];
  /** Segment IDs to select. Defaults to every entry of the selected documents. */
  segments?: string[];
  /** Read-only tools to request per sub-question. */
  tools?: ToolRequest[];
  /** Records what the model was shown, for assertions about level 1 / level 2. */
  observed?: {
    cards: DocumentCard[][];
    entries: SegmentEntry[][];
    subQuestions: string[];
  };
  delayMs?: number;
  /** Raw reply for the conflict-noting hand-off. Defaults to "NONE". */
  conflictNotes?: string;
  /** Make the noting step throw, to prove it cannot stop a turn. */
  failConflictNotes?: boolean;
}

export function scriptedModel(opts: ScriptOptions = {}): GathererModel {
  const wait = async () => {
    if (opts.delayMs) await new Promise((r) => setTimeout(r, opts.delayMs));
  };

  return {
    async splitQuestion(prompt, max) {
      await wait();
      const out = (opts.subQuestions ?? [prompt]).slice(0, max);
      opts.observed?.subQuestions.push(...out);
      return out;
    },
    async selectDocuments(_subQuestion, cards) {
      await wait();
      opts.observed?.cards.push(cards);
      return opts.documents ?? cards.map((c) => c.slug);
    },
    async selectSegments(_subQuestion, entries) {
      await wait();
      opts.observed?.entries.push(entries);
      return opts.segments ?? entries.map((e) => e.id);
    },
    async requestTools() {
      await wait();
      return opts.tools ?? [];
    },
    async noteConflicts() {
      await wait();
      if (opts.failConflictNotes) throw new Error("note-taker unavailable");
      return opts.conflictNotes ?? "NONE";
    },
  };
}
