import { NextResponse } from "next/server";
import { getSupabaseServer, hasSupabase } from "@/lib/supabase/server";
import { toPages, UnreadableLog } from "@/lib/raster-log/to-raster";
import { digitizePages, type MultipageResult } from "@/lib/raster-log/multipage/run";

/**
 * POST /api/digitize — one log file in (multipart `file`), its LAS out.
 *
 * Every page is kept: headings become the LAS header, legends name the curves,
 * curve pages are digitized and stitched, one LAS per log in the file
 * (`lib/raster-log/multipage/run.ts`).
 *
 * The proxy does not run on this path (it would buffer the upload), so the
 * session is checked here. Nothing is stored: the LAS goes back to the browser,
 * which offers it as a download.
 */

// Every page is two Gemini calls, four pages at a time; a ten-page log takes a
// few minutes.
export const maxDuration = 300;

export type DigitizeResponse = MultipageResult & { name: string };

export async function POST(request: Request) {
  if (!hasSupabase()) {
    return NextResponse.json({ error: "Sign-in is not configured." }, { status: 503 });
  }
  const sb = await getSupabaseServer();
  const {
    data: { user },
  } = await sb.auth.getUser();
  if (!user) return NextResponse.json({ error: "Sign in to digitize logs." }, { status: 401 });

  const form = await request.formData().catch(() => null);
  const file = form?.get("file");
  if (!(file instanceof File) || file.size === 0) {
    return NextResponse.json({ error: "No file was sent." }, { status: 400 });
  }

  let pageCount = 0;
  try {
    const pages = await toPages(Buffer.from(await file.arrayBuffer()), file.name);
    pageCount = pages.length;
    const result = await digitizePages(pages, file.name);
    if (result.logs.length === 0) {
      const why = result.pages.find((p) => !p.ok)?.outcome;
      return NextResponse.json(
        { error: why ? `No curves could be digitized. ${why}` : "No curve pages were found in this file." },
        { status: 422 }
      );
    }
    const body: DigitizeResponse = { ...result, name: file.name };
    return NextResponse.json(body);
  } catch (err) {
    if (err instanceof UnreadableLog) {
      return NextResponse.json({ error: err.message }, { status: 415 });
    }
    console.error("digitize failed", { name: file.name, size: file.size, pageCount, err });
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Digitizing failed." },
      { status: 500 }
    );
  }
}
