/**
 * The host for working on geology outside Wildcat.
 *
 * Signed in, always. LAS files come from a local directory, so the same engine
 * runs on real logs without the host's file store. No linked wells and no host
 * tools: those are the user's own data, which only exists inside Wildcat.
 */
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import type { GeologyHost } from "./host";

export function devHost(lasDir: string): GeologyHost {
  const list = async () => {
    const names = await readdir(lasDir).catch(() => [] as string[]);
    return names
      .filter((n) => n.toLowerCase().endsWith(".las"))
      .sort()
      .map((name) => ({ id: name, name }));
  };
  return {
    auth: { assertSignedIn: async () => {} },
    files: {
      listLas: list,
      async loadText(fileId) {
        // The id is the filename. Refuse anything that would leave the directory.
        if (path.basename(fileId) !== fileId) return null;
        const text = await readFile(path.join(lasDir, fileId), "utf8").catch(() => null);
        return text === null ? null : { name: fileId, text: text.trim() };
      },
    },
    wells: {
      rrcApi: async () => null,
      rrcLeaseKey: async () => null,
    },
  };
}
