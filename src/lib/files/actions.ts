"use server";

import { getSupabaseServer } from "@/lib/supabase/server";

/** Wildcat's private file bucket. */
const BUCKET = "files";

export type FileUrlResult =
  | { ok: true; url: string | null }
  | { ok: false; error: string };

/**
 * A short-lived URL for one of the user's stored files.
 *
 * Trimmed from Wildcat's `getFileUrl` (`lib/files/actions.ts`). Wildcat signs
 * with its service key after an RLS read; geology has no service key, so both
 * the row read and the signing run as the signed-in user. Dropbox files, run
 * ticket photos and TIFF/HEIC conversion are Wildcat-only and not handled here.
 */
export async function getFileUrl(
  fileId: string,
  opts: { download?: boolean } = {}
): Promise<FileUrlResult> {
  const sb = await getSupabaseServer();
  const { data: file, error: readErr } = await sb
    .from("files")
    .select("name, storage_key")
    .eq("id", fileId)
    .maybeSingle();
  if (readErr) {
    console.error("getFileUrl (read)", fileId, readErr.message);
    return { ok: false, error: "Couldn't open this file." };
  }
  if (!file?.storage_key) return { ok: true, url: null };
  const { data, error } = await sb.storage
    .from(BUCKET)
    .createSignedUrl(
      file.storage_key as string,
      60 * 60,
      opts.download ? { download: (file.name as string) ?? true } : undefined
    );
  if (error || !data) {
    console.error("getFileUrl (sign)", fileId, error?.message);
    return { ok: false, error: "Couldn't open this file." };
  }
  return { ok: true, url: data.signedUrl };
}
