"use client";

import { useRef, useState } from "react";
import {
  AlertTriangleIcon,
  ArrowRightIcon,
  DownloadIcon,
  FileTextIcon,
  UploadCloudIcon,
  XIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScanSweep } from "@/components/scan/scan-sweep";
import type { DigitizeResponse } from "@/app/api/digitize/route";

/** From Wildcat's `lib/files/limits.ts`. */
function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}

/** Two at a time: each one is a Gemini redraw, and a dozen dropped at once should not all wait on one. */
const CONCURRENCY = 2;

type Job = {
  id: string;
  file: File;
  state:
    | { kind: "ready" }
    | { kind: "queued" }
    | { kind: "working" }
    | { kind: "done"; result: DigitizeResponse }
    | { kind: "failed"; error: string };
};

type LogResult = DigitizeResponse["logs"][number];

function download(log: LogResult) {
  const url = URL.createObjectURL(new Blob([log.las], { type: "text/plain" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = log.fileName;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * The Log Digitizer: Wildcat's Data Entry drop zone (dot field, heading,
 * drag-and-drop). Added files wait in the list until Digitize is pressed,
 * because every one is a paid Gemini redraw. While a file is being digitized,
 * Wildcat's scanner sweep (the statement upload's) passes over its row, and
 * the row turns into a LAS download when it is done.
 *
 * Any image or document goes: the server converts what the digitizer cannot
 * read directly (`lib/raster-log/to-raster.ts`), so there is no accept filter
 * to get wrong here.
 */
export function LogDigitizer() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const queue = useRef<Job[]>([]);
  const running = useRef(0);

  function update(id: string, state: Job["state"]) {
    setJobs((all) => all.map((j) => (j.id === id ? { ...j, state } : j)));
  }

  async function run(job: Job) {
    running.current++;
    update(job.id, { kind: "working" });
    try {
      const body = new FormData();
      body.append("file", job.file);
      const res = await fetch("/api/digitize", { method: "POST", body });
      const json = (await res.json().catch(() => null)) as
        | (DigitizeResponse & { error?: undefined })
        | { error: string }
        | null;
      if (!res.ok || !json || "error" in json && json.error) {
        const error =
          json && "error" in json && json.error
            ? json.error
            : res.status === 413
              ? "This file is too large to upload."
              : "Digitizing failed.";
        update(job.id, { kind: "failed", error });
      } else {
        update(job.id, { kind: "done", result: json as DigitizeResponse });
      }
    } catch {
      update(job.id, { kind: "failed", error: "Couldn't reach the server." });
    } finally {
      running.current--;
      pump();
    }
  }

  function pump() {
    while (running.current < CONCURRENCY && queue.current.length > 0) {
      void run(queue.current.shift()!);
    }
  }

  function add(list: FileList | File[]) {
    const added: Job[] = Array.from(list).map((file) => ({
      id: crypto.randomUUID(),
      file,
      state: { kind: "ready" },
    }));
    if (added.length > 0) setJobs((all) => [...all, ...added]);
  }

  /** Everything still waiting goes to the queue; finished rows stay as they are. */
  function digitizeAll() {
    const ready = jobs.filter((j) => j.state.kind === "ready");
    if (ready.length === 0) return;
    setJobs((all) =>
      all.map((j) => (j.state.kind === "ready" ? { ...j, state: { kind: "queued" } } : j))
    );
    queue.current.push(...ready);
    pump();
  }

  const readyCount = jobs.filter((j) => j.state.kind === "ready").length;

  function remove(id: string) {
    queue.current = queue.current.filter((j) => j.id !== id);
    setJobs((all) => all.filter((j) => j.id !== id));
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files?.length) add(e.dataTransfer.files);
  }

  return (
    <div className="relative flex flex-1 items-center justify-center overflow-y-auto py-10">
      {/* Decorative dot field, densest at center and fading out — mirrors Home. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 [background-image:radial-gradient(circle,_color-mix(in_oklch,_var(--foreground)_24%,_transparent)_1.25px,_transparent_1.75px)] [background-size:18px_18px] [mask-image:radial-gradient(ellipse_58%_48%_at_50%_50%,_black,_transparent_78%)]"
      />

      <div className="relative flex w-full max-w-2xl flex-col items-center px-4">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <h1 className="font-heading text-4xl font-medium tracking-tight">
            Digitize a well log
          </h1>
        </div>

        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={cn(
            "flex w-full flex-col items-center justify-center gap-3 rounded-2xl border-2 px-6 py-12 text-center transition-colors",
            dragging
              ? "border-primary bg-primary/5"
              : "border-foreground/20 bg-background hover:border-foreground/40 hover:bg-background-subtle/40"
          )}
        >
          <span
            className={cn(
              "flex size-12 items-center justify-center rounded-full transition-colors",
              dragging ? "bg-primary/10 text-primary" : "bg-background-subtle text-tertiary-text"
            )}
          >
            <UploadCloudIcon className="size-6" />
          </span>
          <span className="ty-body-1 font-medium text-primary-text">
            {dragging ? "Drop to add files" : "Drag & drop files here"}
          </span>
          <span className="ty-caption text-tertiary-text">or click to browse</span>
        </button>

        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files) add(e.target.files);
            e.target.value = "";
          }}
        />

        {jobs.length > 0 && (
          <ul className="mt-5 flex w-full flex-col gap-1.5">
            {jobs.map((job) => (
              <li
                key={job.id}
                className="relative overflow-hidden rounded-[0.15rem] border border-border bg-background"
              >
                {/* The scanner lamp passes over the row being read, so its name
                    stays legible underneath. */}
                {job.state.kind === "working" ? <ScanSweep /> : null}
                <div className="flex items-center gap-2.5 px-3 py-2">
                <FileTextIcon className="size-4 shrink-0 text-tertiary-text" />
                <span className="ty-body-2 min-w-0 flex-1 truncate text-primary-text">
                  {job.file.name}
                </span>
                {job.state.kind === "failed" ? (
                  <span className="ty-caption flex min-w-0 shrink items-center gap-1.5 text-destructive">
                    <AlertTriangleIcon className="size-3.5 shrink-0" />
                    <span className="truncate">{job.state.error}</span>
                  </span>
                ) : job.state.kind === "working" || job.state.kind === "queued" ? (
                  <span className="ty-caption shrink-0 text-tertiary-text">
                    {job.state.kind === "working" ? "Digitizing…" : "Queued"}
                  </span>
                ) : null}
                <span className="ty-caption shrink-0 tabular-nums text-tertiary-text">
                  {formatBytes(job.file.size)}
                </span>
                {job.state.kind !== "working" && job.state.kind !== "queued" && (
                  <button
                    type="button"
                    aria-label={`Remove ${job.file.name}`}
                    onClick={() => remove(job.id)}
                    className="rounded p-0.5 text-tertiary-text hover:bg-background-hover hover:text-primary-text"
                  >
                    <XIcon className="size-3.5" />
                  </button>
                )}
                </div>
                {job.state.kind === "done" ? <Result result={job.state.result} /> : null}
              </li>
            ))}
          </ul>
        )}

        <div className="mt-2 flex w-full items-center justify-end">
          <Button
            type="button"
            size="lg"
            className="gap-2"
            disabled={readyCount === 0}
            onClick={digitizeAll}
          >
            Digitize{readyCount > 0 ? ` ${readyCount}` : ""} file
            {readyCount === 1 ? "" : "s"}
            <ArrowRightIcon className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

/**
 * What came out of one file: a LAS per log it held, then every page and what
 * happened to it, so a page that was not digitized says why instead of
 * silently missing from the LAS.
 */
function Result({ result }: { result: DigitizeResponse }) {
  return (
    <div className="flex flex-col gap-2 border-t border-border px-3 py-2">
      <ul className="flex flex-col gap-1.5">
        {result.logs.map((log) => (
          <li key={log.fileName} className="flex items-center gap-2.5">
            <span className="ty-body-2 min-w-0 flex-1 truncate text-primary-text">
              {log.title.replace(/\s+/g, " ")}
            </span>
            <span className="ty-caption shrink-0 tabular-nums text-tertiary-text">
              {Math.round(log.topDepth).toLocaleString("en-US")}–
              {Math.round(log.bottomDepth).toLocaleString("en-US")} ft · {log.curves.join(", ")}
            </span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="gap-1.5"
              onClick={() => download(log)}
            >
              <DownloadIcon className="size-3.5" />
              LAS
            </Button>
          </li>
        ))}
      </ul>
      <ol className="ty-caption flex flex-col gap-0.5 text-tertiary-text">
        {result.pages.map((page) => (
          <li key={page.page} className={cn("flex gap-2", !page.ok && "text-destructive")}>
            <span className="w-14 shrink-0 tabular-nums">Page {page.page}</span>
            <span className="min-w-0">{page.outcome}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
