"use client";

import { useEffect, useState } from "react";
import { DownloadIcon } from "lucide-react";
import { toast } from "sonner";

import { Skeleton } from "@/components/ui/skeleton";
import type { ImageBlock } from "@/lib/ai/image-blocks";
import { getFileUrl } from "@/lib/files/actions";

/** Tallest a picture sits in the chat; a tall one narrows rather than grows. */
const MAX_HEIGHT_PX = 480;

/**
 * A picture Orion drew, in the chat. While it draws (and until the bytes have
 * loaded) it is the same gray square the TIFF viewer shows while a log
 * digitizes (`file-preview.tsx`), cut to the picture's shape so nothing moves
 * when it lands. Click to open it in a new tab (geology has no file viewer yet).
 */
export function OrionImage({ block }: { block: ImageBlock }) {
  const [url, setUrl] = useState<string | null>(null);
  const [gone, setGone] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (block.state !== "done" || !block.fileId) return;
    let active = true;
    getFileUrl(block.fileId)
      .then((result) => {
        if (!active) return;
        if (result.ok && result.url) setUrl(result.url);
        else setGone(true);
      })
      .catch(() => {
        if (active) setGone(true);
      });
    return () => {
      active = false;
    };
  }, [block.state, block.fileId]);

  // The tool's reason reaches Orion, which says it; an empty slot adds nothing.
  if (block.state === "failed") return null;

  if (gone) {
    return <p className="ty-caption text-tertiary-text">This image was deleted.</p>;
  }

  const [w, h] = block.aspectRatio.split(":").map(Number);
  const name = block.name ?? "Image";

  async function download() {
    if (!block.fileId) return;
    const result = await getFileUrl(block.fileId, { download: true });
    if (result.ok && result.url) window.open(result.url, "_blank");
    else toast.error(result.ok ? "Couldn't download this image." : result.error);
  }

  return (
    <div
      className="relative bg-neutral-100 p-4"
      style={{ width: `min(100%, ${Math.round((MAX_HEIGHT_PX * w) / h)}px)` }}
    >
      <div className="group/image relative w-full" style={{ aspectRatio: `${w} / ${h}` }}>
        {!loaded && <Skeleton className="absolute inset-0 h-full w-full rounded-md" />}
        {url && (
          <button
            type="button"
            className="absolute inset-0 cursor-zoom-in"
            onClick={() => window.open(url, "_blank", "noopener")}
            aria-label={`Open ${name}`}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={url}
              alt={name}
              onLoad={() => setLoaded(true)}
              onError={() => setGone(true)}
              className={`h-full w-full rounded-md object-contain ${loaded ? "" : "invisible"}`}
            />
          </button>
        )}
        {url && loaded && (
          <button
            type="button"
            onClick={() => void download()}
            aria-label={`Download ${name}`}
            className="absolute right-2 top-2 rounded-md bg-background/90 p-1.5 text-secondary-text opacity-0 shadow-sm transition-opacity hover:text-primary-text focus-visible:opacity-100 group-hover/image:opacity-100"
          >
            <DownloadIcon className="size-4" />
          </button>
        )}
      </div>
    </div>
  );
}
