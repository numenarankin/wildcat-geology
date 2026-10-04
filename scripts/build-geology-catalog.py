"""Regenerate the petrophysics tool catalog the geology agent reads.

The 118 deterministic tools live in `api/_geology/tools/` as Python. Fable
reaches them through one dispatcher tool, so what it needs is not 118 JSON
schemas — it is a list: what each tool is called, what it takes, what it answers.
That list is this script's output, and it is generated rather than written
because a signature that drifts from the catalog is a tool the model calls wrong
every time with no way to notice.

Run after changing anything under `api/_geology/tools/`:

    python3 scripts/build-geology-catalog.py

Writes `src/lib/ai/geology/tool-catalog.json`. Commit the result — the deployed
app reads the file, not this script.
"""
from __future__ import annotations

import inspect
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "geology-corpus"
OUT = ROOT / "src" / "lib" / "ai" / "geology" / "tool-catalog.json"

os.environ.setdefault("GEOLOGY_CORPUS_ROOT", str(CORPUS))
sys.path.insert(0, str(ROOT / "api" / "_geology"))

from dispatch import LAS_ALIASES, UNAVAILABLE, registry, signature_text  # noqa: E402


def canonical_names() -> list[tuple[str, str]]:
    """The catalog's own 118, in catalog order, with their group letter.

    Read from the corpus sidecar rather than restated here: the registry file is
    what the catalog document and the build were both written against, so a tool
    renamed there is renamed here without anyone remembering to.
    """
    data = json.loads((CORPUS / "toc" / ".tool-registry.json").read_text())
    return [(name, group) for group, names in data["groups"].items() for name in names]


# Python annotations, in the shortest form that still tells a model what to send.
# The full text ("Sequence[Mapping[str, Any]] | None") costs four times as much
# and says nothing extra to something writing JSON.
_TYPES = [
    ("Sequence[Sequence[float]]", "num[][]"),
    ("Sequence[Sequence[Any]]", "any[][]"),
    ("Sequence[tuple[float, float]]", "num[][]"),
    ("Sequence[Mapping[str, Any]]", "obj[]"),
    ("Mapping[str, float]", "obj"),
    ("Mapping[str, Any]", "obj"),
    ("dict[str, str]", "obj"),
    ("dict[str, Any]", "obj"),
    ("Sequence[float]", "num[]"),
    ("Sequence[str]", "str[]"),
    ("Sequence[Any]", "any[]"),
    ("Iterable[Any]", "any[]"),
    ("tuple[str, ...]", "str[]"),
    ("float", "num"),
    ("int", "int"),
    ("str", "str"),
    ("bool", "bool"),
    ("Any", "obj"),
]


def short_type(annotation: object) -> str:
    """One token a model can act on."""
    text = str(annotation).replace("'", "").strip()
    if text in ("", "<class 'inspect._empty'>") or "empty" in text:
        return "obj"
    optional = "None" in text
    for long, short in _TYPES:
        if long in text:
            return f"{short}?" if optional else short
    return "obj"


def parameters(fn: object) -> tuple[list[str], list[str]]:
    """Required parameters with their types, then optional ones with theirs.

    Both, and typed. Names alone were the whole catalog for the first version,
    and it cost a wasted model step every time a tool took an optional argument:
    `datum_resolve` takes `header` and the model sent `las_header`;
    `subsea_convert` takes `kb` and it sent `reference_elevation_ft`. It could
    not have known — they were not on the list.
    """
    try:
        params = inspect.signature(fn).parameters.values()
    except (TypeError, ValueError):  # pragma: no cover - builtins only
        return [], []
    required, optional = [], []
    for p in params:
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        entry = f"{p.name}: {short_type(p.annotation)}"
        (optional if p.default is not p.empty else required).append(entry)
    return required, optional


def summary(fn: object) -> str:
    """The docstring's first line. Tools are documented; this is that sentence."""
    doc = inspect.getdoc(fn) or ""
    first = doc.strip().split("\n\n")[0].replace("\n", " ").strip()
    return first[:220]


def main() -> int:
    table = registry()
    entries = []
    missing = []
    for name, group in canonical_names():
        if name in UNAVAILABLE:
            # Left out of the catalog rather than listed as broken. A tool the
            # model can see is a tool it will try, and every attempt costs a
            # round trip to learn what the catalog could have said by omission.
            continue
        # A tool specified against a file path is reached through the entry point
        # that takes the parsed log, so the catalog has to describe *that*
        # signature — the injected parameter dropped, since the caller never
        # supplies it. Advertising the path-taking one would make every call wrong.
        alias = LAS_ALIASES.get(name)
        found = table.get(alias[0] if alias else name)
        if not found:
            missing.append(name)
            continue
        module, fn = found
        required, optional = parameters(fn)
        if alias:
            # Entries carry types now ("las_file: obj"), so match on the name.
            drop = alias[1]
            required = [p for p in required if p.split(":")[0].strip() != drop]
            optional = [p for p in optional if p.split(":")[0].strip() != drop]
        entries.append(
            {
                "name": name,
                "group": group,
                "module": module,
                "signature": signature_text(fn),
                "required": required,
                "optional": optional,
                "summary": summary(fn),
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"tools": entries}, indent=1) + "\n")
    print(f"{len(entries)} tools -> {OUT.relative_to(ROOT)}")
    if missing:
        # Loud, not fatal: a name in the registry with no function behind it is a
        # tool the model would be told about and could never call.
        print(f"WARNING: {len(missing)} catalog names have no function: {', '.join(missing)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
