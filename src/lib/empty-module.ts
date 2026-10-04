// Stand-in for Node built-ins that browser bundles import but never call.
// workerpool (used by @webviz/subsurface-viewer) requires child_process,
// worker_threads and os behind a runtime "am I in Node" check; in the browser
// it takes the Web Worker branch. See `turbopack.resolveAlias` in next.config.ts.
export {};
