"use client";

import { cn } from "@/lib/utils";

/**
 * A scanner lamp passing over the document being read.
 *
 * Overlaid on the content rather than replacing it, because what is underneath
 * is the answer to the only question the user has while waiting — WHICH file is
 * being read. A spinner in the middle of an emptied panel answers neither, and
 * a read takes long enough (OCR then extraction, often 15-20s) that a static
 * screen reads as a hang.
 *
 * Purely decorative: `pointer-events-none` so it never eats a click, and
 * `aria-hidden` because the button beside it already says "Reading…". Motion is
 * dropped under `prefers-reduced-motion` (the bar stays, dimmed).
 */
export function ScanSweep({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden",
        className
      )}
    >
      <div className="animate-scan-sweep absolute inset-y-0 w-1/3">
        {/* Three layers: a soft white wash for the glow, a brighter core, and a
            hairline down the middle that gives the bar an edge. */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/70 to-transparent blur-md dark:via-white/25" />
        <div className="absolute inset-y-0 left-1/2 w-8 -translate-x-1/2 bg-gradient-to-r from-transparent via-white/90 to-transparent blur-sm dark:via-white/40" />
        <div className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-white/90 dark:bg-white/50" />
      </div>
    </div>
  );
}
