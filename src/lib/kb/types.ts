/**
 * Knowledge-base types shared by the file tree and editor.
 *
 * Prototype scope: these describe the shape the UI renders against. The real
 * data source (Supabase / GitHub) gets wired up later.
 */

export type KBFileType =
  | "pdf"
  | "doc"
  | "md"
  | "transcript"
  | "note"
  | "url"
  | "image"
  | "las";

export interface KBFile {
  id: string;
  name: string;
  /** Full path within the folder, e.g. "geology/structure-map.md". */
  path: string;
  type: KBFileType;
  /** Owning folder id; "" means the repo root. */
  folder_id: string;
  /** `dropbox` for a synced file: it opens and downloads, but is not edited, renamed or deleted here. */
  source?: FileSource;
  /** The cloud connection a synced file comes through. */
  connectionId?: string | null;
}

export interface KBFolder {
  id: string;
  name: string;
}

export interface KBTreeNode {
  folder: KBFolder;
  subfolders: KBTreeNode[];
  files: KBFile[];
}

/**
 * Where a file or folder comes from. `dropbox` rows are mirrored from a
 * connected Dropbox and read-only here: Dropbox is their source of truth.
 */
export type FileSource = "upload" | "dropbox";

/** A file in the company knowledge base, available to add to a project. */
export interface RepoFile extends KBFile {
  size: string;
  modified: string;
  /** When the file was added, ISO. `modified` is the display form; this sorts. */
  createdAt?: string | null;
  /** When its bytes last changed, ISO. Sorts the Digitized Logs folder. */
  updatedAt?: string | null;
  /** Pinned within its current folder (floats to the top). */
  pinned?: boolean;
  /**
   * Listed here because a domain row points at it (an invoice filed against
   * the well, a service entry's source, a run ticket's photo), not because it
   * was placed in this folder. It can be opened and downloaded; it cannot be
   * moved, pinned, renamed or deleted from here, since there is no placement
   * to act on. See `lib/files/attached-pure.ts`.
   */
  attached?: boolean;
}

/** A folder in the company knowledge base — may hold subfolders and files. */
export interface RepoFolder {
  id: string;
  name: string;
  /**
   * `dropbox` for a synced folder and for the Dropbox root above them. Nothing
   * is uploaded into, created in, renamed or deleted from one here.
   */
  source?: FileSource;
  /** The cloud connection a synced folder comes through; null on the Dropbox root. */
  connectionId?: string | null;
  folders: RepoFolder[];
  files: RepoFile[];
  modified: string;
}
