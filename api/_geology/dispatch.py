"""Name-to-callable dispatch over the deterministic tool layer.

The harness is TypeScript and the 118 tools are Python, so something has to
translate. This is that, and it holds no domain logic of its own: it finds the
function a name refers to, checks the arguments against its real signature, calls
it, and flattens whatever comes back into JSON.

## Why a lookup and not 118 endpoints

The catalog changes. A tool gains a keyword argument, a module splits into a
package, a name moves group. Any of those breaks a hand-written endpoint and none
of them breaks a lookup — the registry is built by walking the package at import,
so a tool that exists is callable and a tool that does not is a clean error
naming the ones that do.

## Refusals are values

Half these tools return `Refusal` where the source does not support an answer,
and that is the answer: "the file declares no unit on STRT, so the depth column
cannot be read" is what the operator needs to hear. It is flattened like any
other result and returned with HTTP 200. Only a genuinely broken call — unknown
name, arguments that do not fit the signature, an exception out of the tool — is
an error.

## Nothing here writes

The geology path is read-only, and the two tools that would write (the unknown
mnemonic register) are pointed at a scratch path by the handler, because the
deployed filesystem is read-only anyway and a write attempt should fail as a
refusal rather than a stack trace.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import asdict, is_dataclass
from typing import Any, Callable

import tools as _tools_pkg


class ToolError(Exception):
    """A call that cannot be made. Distinct from a tool that refuses to answer."""


_REGISTRY: dict[str, tuple[str, Callable[..., Any]]] | None = None

# Not callable over HTTP, each for its own reason.
#
#   sensitivity_sweep, uncertainty_propagate — take a function to evaluate, and a
#     function is not a JSON value. Call the tool they would sweep, once per case.
#   las_parse — reads a path off a disk this function does not share, and returns
#     a parsed object rather than a value. The `las_header` and `las_curves` ops
#     are the same read, in the shape the harness declares.
#   export_las, export_sheet — write files. The geology path is read-only.
UNAVAILABLE = {
    "sensitivity_sweep": "takes a function to evaluate; call the swept tool once per case instead",
    "uncertainty_propagate": "takes a function to evaluate; call the swept tool once per case instead",
    "las_parse": "reads a file path; use the las_header and las_curves operations instead",
    "export_las": "writes a file, and this path is read-only",
    "export_sheet": "writes a file, and this path is read-only",
}

# Tools specified against a file path, reachable through the sibling that takes
# the already-parsed LAS. The parsed object is hydrated from the posted text, so
# the caller asks for the catalog name and gets the tool it names.
#
#   catalog name -> (function actually called, parameter the parsed LAS goes in)
LAS_ALIASES = {
    "las_validate": ("validate_parsed", "parsed"),
    "curve_inventory": ("curve_inventory_from_las", "las_file"),
}


def _modules() -> list[Any]:
    found = [_tools_pkg]
    for info in pkgutil.walk_packages(_tools_pkg.__path__, prefix="tools."):
        try:
            found.append(importlib.import_module(info.name))
        except Exception:  # noqa: BLE001 - a module that will not import has no tools
            continue
    return found


def registry() -> dict[str, tuple[str, Callable[..., Any]]]:
    """Every public tool function in the package, by name.

    Built once per process. The first module to define a name wins, which is
    well-defined because the package has no duplicate tool names — the catalog's
    "118 entries, 118 distinct" is the property this relies on.
    """
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY

    table: dict[str, tuple[str, Callable[..., Any]]] = {}
    for module in _modules():
        name = module.__name__
        for attr in dir(module):
            if attr.startswith("_"):
                continue
            fn = getattr(module, attr)
            if not callable(fn) or isinstance(fn, type):
                continue
            # Only functions this package defines. Without this, every `math`
            # and `json` symbol a module imported would enter the registry.
            if not getattr(fn, "__module__", "").startswith("tools"):
                continue
            table.setdefault(attr, (name, fn))
    _REGISTRY = table
    return table


def plain(value: Any) -> Any:
    """Dataclasses, tuples and sets out of the tool layer; JSON in.

    `Refusal` and `Quantity` are dataclasses, so this is the one place their
    shape crosses the language boundary.
    """
    if is_dataclass(value) and not isinstance(value, type):
        out = {k: plain(v) for k, v in asdict(value).items()}
        # The caller has to be able to tell a refusal from an answer without
        # knowing the dataclass names, so the kind travels with it.
        out["kind"] = type(value).__name__
        return out
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [plain(v) for v in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        # JSON has no NaN or Infinity. A null reads as "no value", which is what
        # a NaN out of a log calculation means.
        return value if value == value and value not in (float("inf"), float("-inf")) else None
    return str(value)


def signature_text(fn: Callable[..., Any]) -> str:
    try:
        return str(inspect.signature(fn))
    except (TypeError, ValueError):  # pragma: no cover - builtins only
        return "(...)"


def call(name: str, args: dict[str, Any] | None = None) -> Any:
    """Call one tool by name with keyword arguments.

    Raises `ToolError` for an unknown name or arguments that do not fit; returns
    the flattened result otherwise, refusals included.
    """
    table = registry()
    entry = table.get(name)
    if entry is None:
        near = sorted(n for n in table if name and (name in n or n in name))[:8]
        raise ToolError(
            f"no tool named {name!r}"
            + (f"; did you mean one of {', '.join(near)}?" if near else "")
        )
    if name in UNAVAILABLE:
        raise ToolError(f"{name} is not callable here: {UNAVAILABLE[name]}")

    _, fn = entry
    kwargs, repairs = _repair(fn, dict(args or {}))
    try:
        inspect.signature(fn).bind(**kwargs)
    except TypeError as exc:
        raise ToolError(f"{name}{signature_text(fn)} rejected these arguments: {exc}") from None

    try:
        out = plain(fn(**kwargs))
    except Exception as exc:  # noqa: BLE001 - the caller renders the reason
        raise ToolError(f"{name} failed: {type(exc).__name__}: {exc}") from None
    if repairs and isinstance(out, dict):
        # Reported, not hidden: a silently renamed argument is a call that did
        # something other than what was asked for.
        out["_repaired_arguments"] = repairs
    return out


def _params(fn: Callable[..., Any]) -> list[str]:
    try:
        return [
            p.name
            for p in inspect.signature(fn).parameters.values()
            if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        ]
    except (TypeError, ValueError):  # pragma: no cover - builtins only
        return []


def _canon(name: str) -> str:
    """Collapse the ways the same argument gets spelled.

    Units are noise: `bht_degf` and `bht` are one idea. So is the `las_` prefix.

    What is NOT stripped is any word that could name a DIFFERENT parameter.
    Stripping `_elevation` looked harmless and was not: it turned
    `reference_elevation_ft` into `reference`, a real parameter of the same
    function taking a string like "KB". The elevation would have been written
    into it, the tool would have returned something, and nothing downstream
    could have told. Keep this list boring.
    """
    text = name.lower()
    for unit in ("_ft", "_in", "_degf", "_ohmm", "_mv", "_gcc", "_psi", "_frac", "_pct"):
        if text.endswith(unit):
            text = text[: -len(unit)]
    for prefix in ("las_", "log_"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text.strip("_")


# What a JSON value may be written into. A repair that changes the TYPE is not a
# spelling correction, it is a different call.
_JSON_KINDS = {
    "str": (str,),
    "float": (int, float),
    "int": (int,),
    "bool": (bool,),
}


def _type_ok(fn: Callable[..., Any], param: str, value: Any) -> bool:
    """Whether `value` could plausibly be what `param` takes.

    Annotations are strings here (the modules use `from __future__ import
    annotations`), so this is a substring test rather than real type checking —
    enough to stop a number being written into a string parameter, which is the
    mistake that returns a wrong answer instead of an error.
    """
    try:
        annotation = str(inspect.signature(fn).parameters[param].annotation).strip("'\"")
    except (TypeError, ValueError, KeyError):  # pragma: no cover
        return True
    if not annotation or "Any" in annotation or "empty" in annotation:
        return True
    for token, kinds in _JSON_KINDS.items():
        if annotation.startswith(token):
            if token != "bool" and isinstance(value, bool):
                return False
            return isinstance(value, kinds)
    if any(w in annotation for w in ("Sequence", "Iterable", "list", "tuple")):
        return isinstance(value, (list, tuple))
    if any(w in annotation for w in ("Mapping", "dict")):
        return isinstance(value, dict)
    return True


def _repair(fn: Callable[..., Any], kwargs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Map near-miss argument names onto the ones the function actually has.

    A caller writing `las_header` for `header`, or `reference_elevation_ft` for
    `kb`, has understood the tool perfectly and spelled one word differently.
    Rejecting that costs a whole model step to learn something the signature
    could have resolved here — and it happened four times in a single measured
    turn.

    Deliberately conservative: only an unknown argument is touched, only a
    parameter the caller did not already supply is filled, and only when exactly
    ONE candidate matches after canonicalisation. Two candidates is ambiguity,
    and guessing between them would put a value in the wrong slot — which is
    worse than the error, because it returns a plausible number.
    """
    params = _params(fn)
    if not params:
        return kwargs, {}
    unknown = [k for k in kwargs if k not in params]
    if not unknown:
        return kwargs, {}

    free = [p for p in params if p not in kwargs]
    by_canon: dict[str, list[str]] = {}
    for p in free:
        by_canon.setdefault(_canon(p), []).append(p)

    repairs: dict[str, str] = {}
    for key in unknown:
        candidates = by_canon.get(_canon(key), [])
        if len(candidates) != 1:
            continue
        target = candidates[0]
        if target in kwargs or not _type_ok(fn, target, kwargs[key]):
            continue
        kwargs[target] = kwargs.pop(key)
        repairs[key] = target
        by_canon[_canon(key)] = []
    return kwargs, repairs
