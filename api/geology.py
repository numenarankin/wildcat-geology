"""The deterministic tool layer, as a function of this app.

This used to be a FastAPI service on a laptop that the harness reached by URL.
It is now a Python function inside the wildcat deployment: same repository, same
deploy, no second host to keep alive and no credential crossing a network to
reach it. `src/lib/ai/geology/python-tools.ts` is the only caller.

## One route, an op in the body

118 tools do not want 118 endpoints. `POST /api/geology` takes `{"op": ...}` and
everything else is that op's arguments. Three ops are the Stage 0 contract —
`las_header`, `las_curves`, `mnemonic_normalize` — shaped exactly as
`contracts.ts` declares, because the harness validates them and a rename here
would be a silent parse failure there. The fourth, `call`, reaches any tool in
the catalog by name.

## Why the LAS arrives as text

The logs live in Supabase storage. The caller has already read the file for
Orion, so posting the text keeps this function stateless and free of storage
credentials of its own.

## Refusal is not failure

A tool that declines — no unit on the depth column, a mnemonic not in the
dictionary — returns 200 with the refusal in the body. The harness renders
refusals as findings. Only an unknown tool, arguments that do not fit, or a
parse that could not run are 4xx, and each carries a plain reason rather than a
status code, because the reason is what the answer has to explain.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "_geology"))


def _corpus_root() -> str:
    """Where `knowledge-base/` and `toc/` are.

    Named by env var when the deployment sets one, and otherwise found by walking
    up from this file — which covers both the local checkout and the serverless
    bundle, where the working directory is not the repository root.
    """
    named = os.environ.get("GEOLOGY_CORPUS_ROOT")
    if named:
        return named
    for base in (_HERE, *_HERE.parents):
        candidate = base / "geology-corpus"
        if (candidate / "toc").is_dir():
            return str(candidate)
    return str(_HERE.parent / "geology-corpus")


os.environ.setdefault("GEOLOGY_CORPUS_ROOT", _corpus_root())
# The deployed filesystem is read-only outside /tmp, and the unknown-mnemonic
# register is the one thing in the catalog that writes. Point it somewhere
# writable so a register call fails as a refusal rather than a stack trace. The
# geology path never calls it; this is about what happens if something does.
os.environ.setdefault("GEOLOGY_AGENT_MNEMONIC_REGISTRY", "/tmp/unknown-mnemonics.json")

from dispatch import LAS_ALIASES, ToolError, call, plain, registry  # noqa: E402
from tools.las import parse_las_text  # noqa: E402
from tools.mnemonics import mnemonic_normalize as _normalize  # noqa: E402
from tools.result import Refusal  # noqa: E402


def _header(las: Any, key: str) -> str | None:
    got = las.header_value(key)
    if got is None:
        return None
    text = str(getattr(got, "value", got)).strip()
    return text or None


def _number(las: Any, key: str) -> float | None:
    text = _header(las, key)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse(body: dict[str, Any]) -> Any:
    text = body.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ToolError("no LAS text in the request")
    return parse_las_text(text, source_name=str(body.get("name") or "<upload>"))


def op_las_header(body: dict[str, Any]) -> dict[str, Any]:
    """The ~WELL and ~PARAMETER sections, in the shape `contracts.ts` declares.

    Separate from the curve read because Stage 1's RRC branches need location and
    elevation to start, and they should not wait on the data section.
    """
    las = _parse(body)
    kb = _number(las, "EKB")
    gl = _number(las, "EGL")
    return {
        "api": _header(las, "API") or _header(las, "UWI"),
        "name": _header(las, "WELL"),
        "operator": _header(las, "COMP"),
        "county": _header(las, "CNTY"),
        "district": _header(las, "DIST"),
        "kbFt": kb,
        "glFt": gl,
        "epdFt": _number(las, "EPD"),
        # Only claim a reference the file actually supports. Guessing KB because
        # an EKB exists is how a depth ends up on the wrong datum.
        "reference": "KB" if kb is not None else ("GL" if gl is not None else None),
        "latitude": _number(las, "LATI") or _number(las, "LAT"),
        "longitude": _number(las, "LONG") or _number(las, "LON"),
        "startFt": _number(las, "STRT"),
        "stopFt": _number(las, "STOP"),
        "stepFt": _number(las, "STEP"),
        "nullValue": _number(las, "NULL"),
        # Hole quality cannot judge a washout without the hole it was drilled
        # with: absent this, every gate on the caliper declines for the whole log
        # and the branch reports nothing at all.
        "bitSizeIn": _number(las, "BS"),
        "casingShoeFt": _number(las, "CSGD") or _number(las, "CSGL"),
        "bhtDegF": _number(las, "BHT") or _number(las, "MRT"),
        "rmfOhmm": _number(las, "RMF"),
        "rmfTempDegF": _number(las, "MRMF") or _number(las, "RMFT"),
    }


def op_las_curves(body: dict[str, Any]) -> dict[str, Any]:
    las = _parse(body)
    curves = [
        {
            "mnemonic": c.mnemonic,
            "unit": c.unit or None,
            "description": getattr(c, "description", None) or None,
        }
        for c in las.curves
    ]
    index = las.column(las.index_mnemonic)
    return {"curves": curves, "rowCount": len(index) if index is not None else 0}


def op_mnemonic_normalize(body: dict[str, Any]) -> dict[str, Any]:
    """Canonical name, or null.

    The tool refuses on an unknown mnemonic rather than guessing, and a refusal
    here is a null canonical — which the harness records as a flagged curve. The
    curve is kept and usable; it is simply unidentified, and saying so is the
    whole point.
    """
    raw = str(body.get("raw") or "")
    unit = body.get("unit")
    unit = str(unit) if isinstance(unit, str) and unit else None
    match = _normalize(raw, unit)
    if isinstance(match, Refusal):
        return {"raw": raw, "canonical": None, "unit": unit}
    return {
        "raw": raw,
        "canonical": match.canonical,
        # The dictionary's unit wins when the file did not declare one.
        "unit": unit or match.canonical_unit,
    }


def op_las_columns(body: dict[str, Any]) -> dict[str, Any]:
    """Curve values, by canonical name, over a depth window.

    `las_curves` says which curves exist; this returns what they read. Three
    harness branches — the curve suite, hole quality, net pay — are arithmetic
    over these arrays and could not be built without them.

    Decimated to `max_samples` by taking every nth sample rather than averaging:
    an averaged caliper hides the washout that the whole point is to find.
    """
    las = _parse(body)
    top = body.get("topFt")
    base = body.get("baseFt")
    want = body.get("curves")
    limit = int(body.get("maxSamples") or 400)

    index = las.column(las.index_mnemonic)
    if index is None:
        raise ToolError("the file has no depth column to read against")

    null = _number(las, "NULL")
    names = [c.mnemonic for c in las.curves]
    if isinstance(want, list) and want:
        upper = {str(w).upper() for w in want}
        names = [n for n in names if n.upper() in upper]

    rows = [
        i
        for i, d in enumerate(index)
        if d is not None
        and (top is None or d >= float(top))
        and (base is None or d <= float(base))
    ]
    if not rows:
        raise ToolError(
            f"no samples between {top} and {base} ft; the log covers "
            f"{index[0]} to {index[-1]} ft"
        )
    stride = max(1, len(rows) // limit)
    kept = rows[::stride]

    def clean(v: Any) -> float | None:
        if v is None:
            return None
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        # The declared NULL is not a reading, and neither is a NaN.
        if f != f or (null is not None and abs(f - null) < 1e-6):
            return None
        return f

    columns: dict[str, list[float | None]] = {}
    for name in names:
        col = las.column(name)
        if col is None:
            continue
        columns[name] = [clean(col[i]) if i < len(col) else None for i in kept]

    return {
        "depthFt": [clean(index[i]) for i in kept],
        "columns": columns,
        "sampled": len(kept),
        "ofRows": len(rows),
        "stride": stride,
        "nullValue": null,
    }


def op_call(body: dict[str, Any]) -> Any:
    """Any tool in the catalog, by name.

    The LAS travels with the request, so a tool that works on a parsed log gets
    one hydrated here rather than being handed a path to a disk this function
    does not share. The caller names the catalog entry either way; `LAS_ALIASES`
    is what maps it to the entry point that takes the parsed object.
    """
    requested = str(body.get("tool") or "")
    args = body.get("args")
    if args is not None and not isinstance(args, dict):
        raise ToolError("args must be an object of keyword arguments")
    args = dict(args or {})

    name = requested
    alias = LAS_ALIASES.get(requested)
    if alias:
        target, param = alias
        if not body.get("text"):
            raise ToolError(f"{requested} needs the log itself, and no LAS was in scope this turn")
        name, args[param] = target, _parse(body)
    elif body.get("text"):
        import inspect

        entry = registry().get(name)
        if entry:
            takes = inspect.signature(entry[1]).parameters
            for param in ("las_file", "las"):
                if param in takes and param not in args:
                    args[param] = _parse(body)
                    break

    return {"tool": requested, "result": call(name, args)}


def op_catalog(_body: dict[str, Any]) -> dict[str, Any]:
    """Every callable name and its signature. Used to build the model's catalog."""
    from dispatch import signature_text

    table = registry()
    return {
        "tools": [
            {"name": n, "module": m, "signature": signature_text(f), "doc": (f.__doc__ or "").strip()}
            for n, (m, f) in sorted(table.items())
        ]
    }


OPS = {
    "health": lambda _b: {"status": "ok", "tools": len(registry())},
    "catalog": op_catalog,
    "las_header": op_las_header,
    "las_curves": op_las_curves,
    "las_columns": op_las_columns,
    "mnemonic_normalize": op_mnemonic_normalize,
    "call": op_call,
}


def run(body: dict[str, Any]) -> tuple[int, Any]:
    op = str(body.get("op") or "")
    fn = OPS.get(op)
    if fn is None:
        return 400, {"error": f"unknown op {op!r}; expected one of {', '.join(sorted(OPS))}"}
    try:
        return 200, plain(fn(body))
    except ToolError as exc:
        return 422, {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - the caller renders the reason
        return 422, {"error": f"{type(exc).__name__}: {exc}"}


class handler(BaseHTTPRequestHandler):  # noqa: N801 - the name Vercel looks for
    def _send(self, status: int, payload: Any) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's naming
        status, payload = run({"op": "health"})
        self._send(status, payload)

    def do_POST(self) -> None:  # noqa: N802
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": f"body is not JSON: {exc}"})
            return
        if not isinstance(body, dict):
            self._send(400, {"error": "body must be a JSON object"})
            return
        status, payload = run(body)
        self._send(status, payload)

    def log_message(self, *_args: Any) -> None:
        """Silence per-request logging; the platform logs requests already."""
