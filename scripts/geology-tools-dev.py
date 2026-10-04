"""Serve `api/geology.py` locally, because `next dev` does not run Python.

In the deployment the tool layer is a Python function of this app and the
harness calls its own origin. There is no equivalent locally: the dev server is
Node, so the same code needs a host. This is that host — the identical handler,
on a port, with nothing added.

    python3 scripts/geology-tools-dev.py            # 127.0.0.1:8781

Then point the app at it, which is also the default when `VERCEL_URL` is unset:

    GEOLOGY_TOOLS_URL=http://127.0.0.1:8781 npm run dev

Single-threaded on purpose. Concurrency is the platform's job in production, and
here a serialised queue makes a slow tool obvious instead of hiding it behind
parallelism the deployment does not have.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from http.server import HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("GEOLOGY_CORPUS_ROOT", str(ROOT / "geology-corpus"))

spec = importlib.util.spec_from_file_location("geology_function", ROOT / "api" / "geology.py")
if spec is None or spec.loader is None:  # pragma: no cover - a missing file is the message
    raise SystemExit("cannot load api/geology.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Router(module.handler):  # type: ignore[misc, name-defined]
    """The deployed handler, with the path ignored.

    Vercel routes `/api/geology` to the file; here every path is that file, so a
    caller can post to `/` or to `/api/geology` and get the same answer. Keeping
    both working means the same `GEOLOGY_TOOLS_URL` shape works either way.
    """


def main() -> int:
    port = int(os.environ.get("GEOLOGY_TOOLS_PORT") or 8781)
    tools = len(module.registry())
    print(f"geology tool layer: {tools} tools, corpus {os.environ['GEOLOGY_CORPUS_ROOT']}")
    print(f"listening on http://127.0.0.1:{port}")
    try:
        HTTPServer(("127.0.0.1", port), Router).serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
