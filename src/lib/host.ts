/**
 * What this package needs from the app it runs inside.
 *
 * Geology is part of the Wildcat ecosystem: an interpretation reads the user's
 * own LAS files and wells, the RRC tools gate on a signed-in user, and Fable can
 * call the host's read tools. None of that lives here. The host hands it in
 * once, at startup, through `setGeologyHost`, and every module reads it through
 * `geologyHost()`.
 *
 * A port carries DATA, never a database client. Org scoping and RLS stay on the
 * host's side; this package never learns the host's schema.
 *
 * Unset, the host is `UNWIRED`: no files, no linked wells, no host tools, and an
 * auth check that refuses. That makes a forgotten `setGeologyHost` fail loudly on
 * the first gated tool instead of serving the RRC mirror to anyone. Tests and the
 * dev harness install `devHost()` from `./host-dev` explicitly.
 */

export interface LasFileRef {
  id: string;
  name: string;
}

export interface RrcLeaseKey {
  oilGasCode: "O" | "G";
  districtNo: string;
  leaseNo: string;
}

export interface GeologyHost {
  auth: {
    /** Throws when there is no signed-in user. Gates every RRC tool. */
    assertSignedIn(): Promise<void>;
  };
  files: {
    /** LAS files the current user can see, by filename. */
    listLas(): Promise<LasFileRef[]>;
    /** One file's text, or null when it does not exist for this user. */
    loadText(fileId: string): Promise<{ name: string; text: string } | null>;
  };
  wells: {
    /** The 8-digit RRC API number stored on one of the user's wells, or null. */
    rrcApi(wellId: string): Promise<string | null>;
    /** The dominant RRC lease record one of the user's leases sits on, or null. */
    rrcLeaseKey(leaseId: string): Promise<RrcLeaseKey | null>;
  };
  /**
   * The host's own tools (Wildcat: Orion's), offered to Fable read-only.
   * Anything marked `needsApproval` is refused by `orion-bridge.ts`.
   */
  hostTools?(): Record<string, unknown>;
  /** Figure bytes from the host's storage, when they are not on disk. */
  figures?: { read(key: string): Promise<Buffer | null> };
  /** Host tool names that take a LAS `fileId`, for finding the turn's subject in history. */
  lasToolNames?: readonly string[];
  /** Timing hook for RRC queries; the host's request timeline. */
  timed?<T>(source: "rrc", label: string, fn: () => Promise<T>): Promise<T>;
}

const UNWIRED: GeologyHost = {
  auth: {
    async assertSignedIn() {
      throw new Error("geology: no host configured; call setGeologyHost() at startup");
    },
  },
  files: {
    listLas: async () => [],
    loadText: async () => null,
  },
  wells: {
    rrcApi: async () => null,
    rrcLeaseKey: async () => null,
  },
};

const KEY = Symbol.for("geology.host");
type Slot = { [KEY]?: GeologyHost };

/*
 * Held on globalThis rather than a module variable: Next can instantiate a
 * module more than once across server bundles, and a host set in one copy would
 * be invisible to the other.
 */
export function setGeologyHost(host: GeologyHost): void {
  (globalThis as Slot)[KEY] = host;
}

export function geologyHost(): GeologyHost {
  return (globalThis as Slot)[KEY] ?? UNWIRED;
}
