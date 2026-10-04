"""Curve mnemonics: normalization against an owned dictionary, and the log of
what it could not map.

The dictionary here is an **owned artefact, not a sourced one**, and the module
says so in every rule it carries. The KGS curve-mnemonic table was never
ingested; `beg-boonsville-secondary-gas-recovery#34` supplies an era ordering of
tool types and the one sentence that justifies keying on vendor at all — "other
logging companies had different tool mnemonics, but the tools provided similar
measurements" — and no source in the corpus lists a vendor's mnemonics. Entries
marked `cited` name a segment that states the meaning while using the curve;
entries marked `owned` carry no anchor and say what would source them.

Two consequences that look like fussiness and are not:

- A declared unit that contradicts the rule **refuses** rather than downgrading to
  a match with a caveat. `DRHO` in kg/m3 read as g/cm3 silently disables the
  `DRHO_SUSPECT = 0.20` gate in `petrophysics`, which is the one numeric
  log-quality threshold the corpus states.
- A missing unit is always a conditional match, never a clean one. The unit is
  part of the key because the same mnemonic under a different unit can be a
  different measurement.

Unknown mnemonics are logged, never guessed. The register keys on mnemonic+unit
and deliberately not on vendor or era: keying on vendor would split the same
unknown mnemonic seen from two service companies into two rows, halving each
count so neither ranks for review and hiding the most useful fact available.
Vendor and era vary within an entry, one per occurrence, side by side.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from typing import Any, Iterator, Sequence
import json
import math
import os
import tempfile
import time

from .result import Quantity, Range, Refusal  # noqa: F401  (Range is used by the module this merges into)
from .result import Quantity, Range, Refusal  # noqa: F401  (house import contract)

# ---------------------------------------------------------------------------
# 10_mnemonic_unknown_register
# The unknown-mnemonic register: what `mnemonic_normalize` writes when it will
# ---------------------------------------------------------------------------

try:  # POSIX; the kernel releases the lock if the process dies, so no stale locks
    import fcntl
except ImportError:  # pragma: no cover - portability fallback
    fcntl = None  # type: ignore[assignment]


# `tool-catalog.md:205` reads "Source: not applicable - plumbing, no citation
# owed." `Quantity` refuses to construct without a source string, so the honest
# value is one naming the line that declares none is owed - never a fabricated
# corpus anchor. See the spec's "Why no citation is owed".
NO_CITATION = "not applicable - plumbing, no citation owed (tool-catalog.md:205)"

# `beg-boonsville#34` is not this tool's source. It is quoted in the two
# missing-context flags because it is the reason vendor and era are the fields a
# reviewer cannot do without.
VENDOR_ERA_ANCHOR = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#34"

SCHEMA = "geology-agent/unknown-mnemonic-register"
SCHEMA_VERSION = 1

# Follows the package rather than the process's working directory. Once merged
# into `tools/mnemonics.py` this resolves to `<geology-agent>/data/`.
DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "unknown-mnemonics.json"
REGISTRY_ENV_VAR = "GEOLOGY_AGENT_MNEMONIC_REGISTRY"

MAX_SAMPLE_VALUES = 10
LOCK_TIMEOUT_SECONDS = 10.0
LOCK_POLL_SECONDS = 0.02
LOCK_STALE_SECONDS = 60.0  # only used by the no-fcntl fallback

# Occurrence fields that come from the caller's context and are merged fill-only.
CONTEXT_FIELDS = (
    "well_name",
    "api",
    "mnemonic_as_written",
    "unit_as_written",
    "description",
    "service_company",
    "log_date",
    # `era_year` is the caller's assertion of the logging era, not a date parsed
    # out of `log_date` - this tool stores dates verbatim and parses none. It
    # exists because vendor and era are what disambiguate a mnemonic
    # (`beg-boonsville#34`) and a reviewer cannot sort or range on a string.
    "era_year",
    # Why `mnemonic_normalize` could not map it: unknown_mnemonic | ambiguous |
    # unit_conflict | conditional_match. Bookkeeping, not interpretation.
    "unmapped_reason",
    "depth_start",
    "depth_stop",
    "depth_unit",
    "value_min",
    "value_max",
    "value_count",
    "sample_values",
)


class _RegistryCorrupt(Exception):
    """Internal: the registry file is not this schema. Converted to a Refusal."""


class _LockBusy(Exception):
    """Internal: another process holds the register. Converted to a Refusal."""


# --------------------------------------------------------------------------
# paths, time, locking, atomic IO
# --------------------------------------------------------------------------


def _resolve_path(registry_path: str | Path | None) -> Path:
    """Explicit argument, then $GEOLOGY_AGENT_MNEMONIC_REGISTRY, then the default."""
    if registry_path is not None:
        return Path(registry_path).expanduser()
    env = os.environ.get(REGISTRY_ENV_VAR)
    if env:
        return Path(env).expanduser()
    return DEFAULT_REGISTRY_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@contextmanager
def _registry_lock(path: Path) -> Iterator[None]:
    """Serialise the whole read-modify-write against a sibling lock file.

    Atomic replace stops a reader seeing a half-written file; it does nothing
    about two processes both reading v1 and each writing their own v2. That
    lost update is what this lock prevents.
    """
    lock_path = path.with_name(path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS

    if fcntl is not None:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise _LockBusy(str(lock_path))
                    time.sleep(LOCK_POLL_SECONDS)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:  # pragma: no cover
                pass
            os.close(fd)
        return

    # pragma: no cover - non-POSIX fallback
    while True:  # O_EXCL create is atomic on every filesystem worth using
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o644)
            break
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
            except OSError:
                age = 0.0
            if age > LOCK_STALE_SECONDS:
                try:
                    lock_path.unlink()
                except OSError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise _LockBusy(str(lock_path))
            time.sleep(LOCK_POLL_SECONDS)
    try:
        yield
    finally:
        os.close(fd)
        try:
            lock_path.unlink()
        except OSError:
            pass


def _empty_registry() -> dict[str, Any]:
    return {"schema": SCHEMA, "version": SCHEMA_VERSION, "entries": []}


def _load_registry(path: Path) -> dict[str, Any]:
    """Missing or empty is an empty registry. Anything else that is not this
    schema raises `_RegistryCorrupt` - it is never silently replaced."""
    if not path.exists():
        return _empty_registry()
    raw = path.read_text(encoding="utf-8")  # OSError propagates to the boundary
    if not raw.strip():
        return _empty_registry()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise _RegistryCorrupt(f"not valid JSON ({exc.msg} at line {exc.lineno})") from exc
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise _RegistryCorrupt(f"not a {SCHEMA!r} file")
    if not isinstance(data.get("entries"), list):
        raise _RegistryCorrupt("'entries' is missing or is not a list")
    return data


def _write_registry(path: Path, data: dict[str, Any]) -> None:
    """Temp file in the SAME directory, fsync, then os.replace - atomic on POSIX,
    so a concurrent reader sees either the whole old file or the whole new one."""
    _sort_registry(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, str(path))
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _sort_registry(data: dict[str, Any]) -> None:
    """Deterministic order, so identical content serialises to identical bytes.
    That is what makes 'a repeat writes nothing' checkable and the file diffable."""
    for entry in data["entries"]:
        entry["occurrences"].sort(key=lambda o: (o.get("well_id") or "", o.get("source_file") or ""))
        entry["occurrence_count"] = len(entry["occurrences"])
        entry["well_count"] = len({o.get("well_id") for o in entry["occurrences"]})
    data["entries"].sort(key=lambda e: e["key"])


# --------------------------------------------------------------------------
# normalisation and sampling - the only two derived things in the module
# --------------------------------------------------------------------------


def _entry_key(mnemonic: str, unit: str | None) -> str:
    """Case-folding, not interpretation. Both as-written spellings are stored."""
    return f"{mnemonic.strip().upper()}|{(unit or '').strip().lower()}"


def _is_null(v: Any, null_value: float | None) -> bool:
    if v is None:
        return True
    try:
        f = float(v)
    except (TypeError, ValueError):
        return True  # a non-numeric cell is not a value; it is recorded as absent
    if math.isnan(f) or math.isinf(f):
        return True
    if null_value is not None and math.isclose(f, null_value, rel_tol=0.0, abs_tol=1e-9):
        return True
    return False


def _summarise_values(
    values: Sequence[Any] | None, null_value: float | None
) -> tuple[float | None, float | None, int | None, list[float]]:
    """min, max, non-null count, and an evenly spaced sample of at most
    MAX_SAMPLE_VALUES. Evenly spaced rather than the first ten, so the sample
    spans the log instead of showing ten values off the top of the hole."""
    if values is None:
        return None, None, None, []
    clean = [float(v) for v in values if not _is_null(v, null_value)]
    if not clean:
        return None, None, 0, []
    n = len(clean)
    if n <= MAX_SAMPLE_VALUES:
        sample = list(clean)
    else:
        idx = [round(i * (n - 1) / (MAX_SAMPLE_VALUES - 1)) for i in range(MAX_SAMPLE_VALUES)]
        sample = [clean[i] for i in idx]
    return min(clean), max(clean), n, sample


def _blank(s: Any) -> bool:
    return s is None or (isinstance(s, str) and not s.strip())


def _clean(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.strip()
    return s or None


# --------------------------------------------------------------------------
# the three public operations
# --------------------------------------------------------------------------


def mnemonic_unknown_register(
    mnemonic: str,
    well_id: str,
    *,
    unit: str | None = None,
    description: str | None = None,
    service_company: str | None = None,
    log_date: str | None = None,
    era: int | None = None,
    reason: str = "",
    depth_start: float | None = None,
    depth_stop: float | None = None,
    depth_unit: str | None = None,
    values: Sequence[Any] | None = None,
    null_value: float | None = None,
    source_file: str | None = None,
    well_name: str | None = None,
    api: str | None = None,
    registry_path: str | Path | None = None,
) -> Quantity | Refusal:
    """Record one unmapped mnemonic with its context. Idempotent per (well, file).

    Called by `mnemonic_normalize` for every mnemonic its dictionary misses.
    Returns a `Quantity` whose value is the entry's occurrence count after the
    call, or a `Refusal`. Writes the registry only when its content changes.
    """
    if _blank(mnemonic):
        return Refusal(
            reason="no mnemonic to record; the mnemonic is blank",
            needed=("a non-blank mnemonic from the LAS ~C section",),
            source=NO_CITATION,
        )
    if _blank(well_id):
        # The refusal this tool exists for. Without a well identity the
        # occurrence grain is undefined: a re-ingest cannot be told from a
        # second well, so the record would either inflate on every re-parse or
        # merge into another well's evidence. Both are worse than no record.
        return Refusal(
            reason=f"cannot record unknown mnemonic {mnemonic.strip()!r} without a well identity; "
            "re-ingest and a second well would be indistinguishable",
            needed=("well_id - the API number, or another stable well identity",),
            source=NO_CITATION,
        )

    path = _resolve_path(registry_path)
    key = _entry_key(mnemonic, unit)
    well = well_id.strip()
    src = (source_file or "").strip()
    now = _now()

    v_min, v_max, v_count, sample = _summarise_values(values, null_value)
    incoming = {
        "well_id": well,
        "source_file": src,
        "well_name": _clean(well_name),
        "api": _clean(api),
        "mnemonic_as_written": mnemonic.strip(),
        "unit_as_written": _clean(unit),
        "description": _clean(description),
        "service_company": _clean(service_company),
        "log_date": _clean(log_date),
        "era_year": None if era is None else int(era),
        "unmapped_reason": _clean(reason),
        "depth_start": None if depth_start is None else float(depth_start),
        "depth_stop": None if depth_stop is None else float(depth_stop),
        "depth_unit": _clean(depth_unit),
        "value_min": v_min,
        "value_max": v_max,
        "value_count": v_count,
        "sample_values": sample,
        "recorded_at": now,
    }

    flags: list[str] = []
    try:
        with _registry_lock(path):
            data = _load_registry(path)
            entries = {e["key"]: e for e in data["entries"]}
            entry = entries.get(key)
            changed = False

            final_occ: dict[str, Any]

            if entry is None:
                entry = {
                    "key": key,
                    "mnemonic": incoming["mnemonic_as_written"],
                    "unit": incoming["unit_as_written"],
                    "spellings": [incoming["mnemonic_as_written"]],
                    "units_seen": [incoming["unit_as_written"]] if incoming["unit_as_written"] else [],
                    "first_recorded": now,
                    "last_recorded": now,
                    "occurrence_count": 0,
                    "well_count": 0,
                    "resolved": False,
                    "resolution": None,
                    "occurrences": [dict(incoming)],
                }
                data["entries"].append(entry)
                final_occ = entry["occurrences"][0]
                action = "created"
                changed = True
            else:
                existing = next(
                    (
                        o
                        for o in entry["occurrences"]
                        if o.get("well_id") == well and (o.get("source_file") or "") == src
                    ),
                    None,
                )
                if existing is None:
                    entry["occurrences"].append(dict(incoming))
                    final_occ = entry["occurrences"][-1]
                    action = "occurrence_added"
                    changed = True
                else:
                    final_occ = existing
                    filled, conflicts = _merge_fill_only(existing, incoming)
                    action = "enriched" if filled else "unchanged"
                    changed = bool(filled)
                    if conflicts:
                        flags.append(
                            "context differs from the recorded occurrence; original kept: "
                            + ", ".join(sorted(conflicts))
                        )

                # spellings / units_seen accumulate at entry level regardless
                if incoming["mnemonic_as_written"] not in entry["spellings"]:
                    entry["spellings"].append(incoming["mnemonic_as_written"])
                    entry["spellings"].sort()
                    changed = True
                u = incoming["unit_as_written"]
                if u and u not in entry.setdefault("units_seen", []):
                    entry["units_seen"].append(u)
                    entry["units_seen"].sort()
                    changed = True

            if entry.get("resolved"):
                canonical = (entry.get("resolution") or {}).get("canonical")
                flags.append(
                    f"entry already resolved as {canonical!r}; recording the occurrence anyway "
                    "(the dictionary and the register have drifted)"
                )

            if changed:
                # Named `last_recorded`, not `last_seen`: it is the last CHANGE.
                # Bumping it on a no-op call would break byte-idempotency.
                entry["last_recorded"] = now
                _write_registry(path, data)
            else:
                _sort_registry(data)  # keeps the in-memory counts right for the return

            occurrence_count = entry["occurrence_count"]
            well_count = entry["well_count"]
            entry_count = len(data["entries"])
            resolved = bool(entry.get("resolved"))
            # Flags describe the RECORD as it now stands, not this call's
            # arguments: a repeat that passes no vendor must not claim the
            # stored occurrence has none.
            context_flags = _context_flags(final_occ)
    except _RegistryCorrupt as exc:
        return _corrupt_refusal(path, exc)
    except _LockBusy:
        return _busy_refusal(path)
    except OSError as exc:
        return _unwritable_refusal(path, exc)

    flags.extend(context_flags)
    return Quantity(
        value=float(occurrence_count),
        unit="occurrences",
        method="unknown-mnemonic register (bookkeeping)",
        source=NO_CITATION,
        inputs={
            "entry_key": key,
            "mnemonic": incoming["mnemonic_as_written"],
            "unit": incoming["unit_as_written"],
            "well_id": well,
            "source_file": src or None,
            "registry_path": str(path),
        },
        assumptions={
            "action": action,
            "well_count": well_count,
            "entry_count": entry_count,
            "resolved": resolved,
            "occurrence_grain": "(well_id, source_file)",
            "entry_key_grain": "(MNEMONIC uppercased, unit lowercased)",
        },
        flags=tuple(flags),
    )


def mnemonic_unknown_list(
    registry_path: str | Path | None = None,
    *,
    include_resolved: bool = False,
    limit: int | None = None,
) -> list[dict[str, Any]] | Refusal:
    """The human review queue, ranked by how often the mnemonic has been seen.

    Ranked by distinct wells desc, then occurrences desc, then key asc: a
    mnemonic seen in five wells is stronger evidence than one seen five times in
    one well's five reruns.

    Returns the stored records themselves rather than a `Quantity`. This is a
    listing of persisted rows, not a derived quantity - each row carries its own
    provenance (well, file, timestamps) inside it, so a wrapper would have to
    invent a meaningless `value`.

    Takes no lock: the atomic replace in `_write_registry` guarantees a reader
    sees a complete file.
    """
    path = _resolve_path(registry_path)
    try:
        data = _load_registry(path)
    except _RegistryCorrupt as exc:
        return _corrupt_refusal(path, exc)
    except OSError as exc:
        return _unwritable_refusal(path, exc)

    rows = [e for e in data["entries"] if include_resolved or not e.get("resolved")]
    rows.sort(key=lambda e: (-len({o.get("well_id") for o in e["occurrences"]}), -len(e["occurrences"]), e["key"]))
    if limit is not None:
        rows = rows[:limit]
    return json.loads(json.dumps(rows))  # deep copy; callers cannot mutate the file's shape


def mnemonic_unknown_resolve(
    mnemonic: str,
    *,
    canonical: str,
    resolved_by: str,
    unit: str | None = None,
    note: str | None = None,
    registry_path: str | Path | None = None,
) -> Quantity | Refusal:
    """Mark an entry resolved once the mnemonic has entered the dictionary.

    The entry and every occurrence are kept: they are the audit trail behind the
    dictionary row. `canonical` and `resolved_by` are required and never
    inferred - this tool does not decide what a mnemonic means.
    """
    if _blank(mnemonic):
        return Refusal(
            reason="no mnemonic given to resolve",
            needed=("the mnemonic as registered",),
            source=NO_CITATION,
        )
    if _blank(canonical) or _blank(resolved_by):
        return Refusal(
            reason="a resolution must name the canonical mnemonic and who decided it; "
            "this tool never infers a meaning",
            needed=("canonical", "resolved_by"),
            source=NO_CITATION,
        )

    path = _resolve_path(registry_path)
    key = _entry_key(mnemonic, unit)
    now = _now()
    flags: list[str] = []

    try:
        with _registry_lock(path):
            data = _load_registry(path)
            entry = next((e for e in data["entries"] if e["key"] == key), None)
            if entry is None:
                return Refusal(
                    reason=f"no registry entry for {key!r}; "
                    f"{len(data['entries'])} entr{'y' if len(data['entries']) == 1 else 'ies'} on file",
                    needed=("a mnemonic and unit pair already registered as unknown",),
                    source=NO_CITATION,
                )

            resolution = {
                "canonical": canonical.strip(),
                "resolved_by": resolved_by.strip(),
                "resolved_at": now,
                "note": _clean(note),
            }
            prior = entry.get("resolution")
            if entry.get("resolved") and prior:
                if prior.get("canonical") == resolution["canonical"] and prior.get("resolved_by") == resolution["resolved_by"]:
                    action = "unchanged"
                    changed = False
                else:
                    # Never overwrite a human decision silently: keep the old one.
                    entry.setdefault("resolution_history", []).append(prior)
                    entry["resolution"] = resolution
                    flags.append(
                        f"re-resolved; previous canonical {prior.get('canonical')!r} "
                        "retained in resolution_history"
                    )
                    action = "resolved"
                    changed = True
            else:
                entry["resolved"] = True
                entry["resolution"] = resolution
                action = "resolved"
                changed = True

            if changed:
                entry["last_recorded"] = now
                _write_registry(path, data)
            else:
                _sort_registry(data)

            occurrence_count = entry["occurrence_count"]
            well_count = entry["well_count"]
            entry_count = len(data["entries"])
    except _RegistryCorrupt as exc:
        return _corrupt_refusal(path, exc)
    except _LockBusy:
        return _busy_refusal(path)
    except OSError as exc:
        return _unwritable_refusal(path, exc)

    return Quantity(
        value=float(occurrence_count),
        unit="occurrences",
        method="unknown-mnemonic register (resolution)",
        source=NO_CITATION,
        inputs={
            "entry_key": key,
            "canonical": canonical.strip(),
            "resolved_by": resolved_by.strip(),
            "registry_path": str(path),
        },
        assumptions={
            "action": action,
            "well_count": well_count,
            "entry_count": entry_count,
            "resolved": True,
            "occurrences_retained": occurrence_count,
        },
        flags=tuple(flags),
    )


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _merge_fill_only(existing: dict[str, Any], incoming: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Fill nulls, never overwrite. Returns (filled fields, conflicting fields).

    A stored non-null value that disagrees with the incoming one is kept and
    reported. Overwriting would lose evidence; the disagreement itself is
    information a reviewer wants.
    """
    filled: list[str] = []
    conflicts: list[str] = []
    for field in CONTEXT_FIELDS:
        new = incoming.get(field)
        old = existing.get(field)
        if new is None or new == [] :
            continue
        if old is None or old == []:
            existing[field] = new
            filled.append(field)
        elif old != new:
            conflicts.append(field)
    return filled, conflicts


def _context_flags(occ: dict[str, Any]) -> list[str]:
    """Missing context is flagged, never refused: a partial record of a real
    unknown beats no record, but the reviewer must see what is thin."""
    flags: list[str] = []
    if not occ.get("service_company"):
        flags.append(
            "no service company recorded; vendor is what disambiguates a mnemonic "
            f"({VENDOR_ERA_ANCHOR})"
        )
    if not occ.get("log_date"):
        flags.append(
            f"no log date recorded; era is what disambiguates a mnemonic ({VENDOR_ERA_ANCHOR})"
        )
    if not occ.get("description"):
        flags.append("no ~C description recorded")
    if occ.get("depth_start") is None or occ.get("depth_stop") is None:
        flags.append("depth range not stated")
    else:
        if occ.get("depth_unit") is None:
            flags.append("depth unit not stated")
        if occ["depth_start"] > occ["depth_stop"]:
            flags.append("depth range reversed as supplied")
    if occ.get("value_count") is None:
        flags.append("no values supplied; range unknown")
    elif occ["value_count"] == 0:
        flags.append("all sampled values are null")
    return flags


def _corrupt_refusal(path: Path, exc: Exception) -> Refusal:
    return Refusal(
        reason=f"unknown-mnemonic registry at {path} is corrupt: {exc}. "
        "Nothing was written; the file is untouched. It is not treated as empty, "
        "because starting fresh would discard every unknown recorded so far",
        needed=("a valid registry file, or the damaged one moved aside for repair",),
        source=NO_CITATION,
    )


def _busy_refusal(path: Path) -> Refusal:
    return Refusal(
        reason=f"could not lock the unknown-mnemonic registry at {path} within "
        f"{LOCK_TIMEOUT_SECONDS:.0f}s; another ingest holds it",
        needed=("a retry once the other ingest finishes",),
        source=NO_CITATION,
    )


def _unwritable_refusal(path: Path, exc: OSError) -> Refusal:
    return Refusal(
        reason=f"unknown-mnemonic registry at {path} could not be read or written: {exc}",
        needed=("a readable and writable registry path, or $" + REGISTRY_ENV_VAR,),
        source=NO_CITATION,
    )

# ---------------------------------------------------------------------------
# 09_mnemonic_normalize
# Curve-mnemonic normalization. Staging file for `tools/mnemonics.py` (#9).
# ---------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Corpus anchors
# --------------------------------------------------------------------------
BEG_TIMELINE = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#34"
ASQ = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004"
ASQ_SP = f"{ASQ}#12"        # "measured in millivolts (mV)"
ASQ_GR = f"{ASQ}#15"        # "0 to 150 API gamma ray units"
ASQ_SONIC = f"{ASQ}#16"     # DT, SPHI, "microseconds per foot"
ASQ_DENS = f"{ASQ}#18"      # RHOB, DRHO, DPHI, PE/PEF, the 0.20 g/cm3 note
ASQ_NEUT = f"{ASQ}#19"      # "liquid-filled porosity (phi_N, PHIN, or NPHI)"
ASQ_ND = f"{ASQ}#20"        # "a caliper (CALI) and gamma ray (GR) in track 1"
ASQ_CURVES = f"{ASQ}#11"    # "Log curve ILD:" glossary - ILD/ILM/SFLU/LLD/LLS/RXO
ASQ_RESTAB = f"{ASQ}#30"
ASQ_MICROLOG = f"{ASQ}#37"  # "the micronormal log (MNOR ...) / the microinverse (MINV ...)"    # Table 5.1 classification of resistivity logs
ASQ_TRACKS = f"{ASQ}#27"    # "the caliper measures the borehole diameter from 6 to 16 inches"

# Sentences from beg#34 that set the era windows below. Quoted rather than
# paraphrased because they are the whole of the era evidence in the corpus.
ERA_RESISTIVITY_ONLY = (
    'beg#34: "In the 1940\'s and 1950\'s, only resistivity measurements were available."'
)
ERA_MICROLOG_CALIPER = (
    'beg#34: the 1940s-50s microlog "provided three measurements: Caliper, Micro Normal '
    '(2 inches), and Micro Inverse (1 inch x 1 inch)."'
)
ERA_SHORT_NORMAL_END = (
    'beg#34: "In the late 1960\'s, the Short Normal was replaced by focused shallow '
    'resistivity tools, such as the Spherically Focused Log (SFL)."'
)
ERA_LATE_60S_SUITE = (
    'beg#34: the focused-resistivity tool "was often run with the newly developed borehole '
    'compensated sonic (BHS) tool and the gamma ray (GR) tool."'
)
ERA_1970S_POROSITY = (
    'beg#34: "In the 1970\'s, two new tools, the Compensated Neutron (CNL) and the '
    'Compensated Formation Density (FDC) devices, became commonly used."'
)
ERA_1980S_PEF = (
    'beg#34: "In the 1980\'s, the density tool was enhanced to include a photoelectric '
    'effect measurement (PEF)."'
)
ERA_ES_START = 'beg#34: "Wells were logged from the discovery of the field in 1945."'
ERA_DUAL_LATEROLOG = (
    'asquith#30: "In the early 1970s, the dual laterolog was released commercially."'
)
ERA_ADVISORY = (
    "era window is owned, anchored to beg#34's decade prose; beg#34 calls its own figure "
    '"a rough time line" and it describes one field (Boonsville). Advisory only.'
)
VENDOR_EMPTY = (
    'beg#34: "Other logging companies had different tool mnemonics, but the tools provided '
    "similar measurements.\" The corpus names no vendor's mnemonic list, so the vendor "
    "dimension of the key is present and empty."
)

# --------------------------------------------------------------------------
# Unit tokens
# --------------------------------------------------------------------------
# OWNED. The corpus supplies the unit *names* in prose - "grams per cubic
# centimeter, g/cm3 (or Kg/m3 or Mg/m3)" (asquith#18), "microseconds per foot"
# (asquith#16), "ohm-meters" (asquith#8), "millivolts (mV)" (asquith#12),
# "API gamma ray units" (asquith#15), "barns per electron, b/e" (asquith#18),
# "inches" (asquith#27) - but no document lists the ASCII spellings a LAS file
# actually carries. These synonym sets are therefore this project's.
#
# The safety property that makes an incomplete table tolerable: an unrecognized
# spelling degrades a match toward `unit_relaxed` (conditional, registered). It
# can never produce a wrong `exact` match.
UNIT_SYNONYMS: dict[str, str] = {
    # bulk density and density correction
    "G/CM3": "G/CM3", "G/CM^3": "G/CM3", "G/C3": "G/CM3", "G/CC": "G/CM3",
    "GM/CC": "G/CM3", "GM/CM3": "G/CM3", "G/CM**3": "G/CM3",
    "KG/M3": "KG/M3", "KG/M^3": "KG/M3", "K/M3": "KG/M3",
    "MG/M3": "MG/M3", "MG/M^3": "MG/M3",
    # porosity / fractions
    "V/V": "V/V", "DEC": "V/V", "FRAC": "V/V", "FRACTION": "V/V", "VDEC": "V/V",
    "%": "PCT", "PCT": "PCT", "PERCENT": "PCT", "P.U.": "PCT", "PU": "PCT",
    # resistivity
    "OHMM": "OHM-M", "OHM-M": "OHM-M", "OHM.M": "OHM-M", "OHMS-M": "OHM-M",
    "OHM*M": "OHM-M", "OHMM2/M": "OHM-M",
    # sonic
    "US/F": "USEC/FT", "US/FT": "USEC/FT", "USEC/FT": "USEC/FT", "USEC/F": "USEC/FT",
    "USFT": "USEC/FT", "US/M": "USEC/M", "USEC/M": "USEC/M",
    # gamma ray. NOTE: "API" is a calibration standard, not a convertible unit -
    # see the unit_convert (#11) catalog note. Recognized here, never converted.
    "GAPI": "GAPI", "API": "GAPI", "APIGR": "GAPI",
    # spontaneous potential
    "MV": "MV", "MVOLT": "MV", "MVOLTS": "MV", "MILLIVOLTS": "MV",
    # caliper / depth
    "IN": "IN", "INCH": "IN", "INCHES": "IN", "INS": "IN",
    "MM": "MM",
    "F": "FT", "FT": "FT", "FEET": "FT",
    "M": "M", "METER": "M", "METERS": "M", "METRES": "M",
    # photoelectric effect
    "B/E": "B/E", "BARNS/E": "B/E", "B/ELEC": "B/E",
}

FAMILY_RESISTIVITY = "resistivity"
FAMILY_POROSITY = "porosity"
FAMILY_LITHOLOGY = "lithology"
FAMILY_BOREHOLE = "borehole"
FAMILY_POTENTIAL = "potential"
FAMILY_INDEX = "index"

PROV_CITED = "cited"
PROV_OWNED = "owned"

REASON_UNKNOWN = "unknown_mnemonic"
REASON_BLANK = "blank_mnemonic"
REASON_AMBIGUOUS = "ambiguous"
REASON_UNIT_CONFLICT = "unit_conflict"
REASON_CONDITIONAL = "conditional_match"


@dataclass(frozen=True)
class MnemonicRule:
    """One row of the owned dictionary, keyed by (mnemonic, unit, vendor, era).

    `provenance` is the honest half of this record. `cited` means a named corpus
    segment states what the mnemonic means; `owned` means nothing in the corpus
    does and this project asserted it anyway. `source` is empty exactly when
    `provenance` is `owned`.
    """

    mnemonic: str                       # the lookup key, uppercased
    canonical: str                      # canonical curve name
    measures: str                       # what it measures, in words
    family: str
    canonical_unit: str                 # the unit the curve is defined in
    units: tuple[str, ...]              # every unit token accepted for this rule
    provenance: str
    source: str = ""
    vendor: str | None = None           # None == vendor-independent
    era_first: int | None = None        # inclusive; None == open
    era_last: int | None = None         # inclusive; None == open
    era_basis: str = ""                 # the quoted sentence that set the window
    note: str = ""

    def __post_init__(self) -> None:
        if self.provenance not in (PROV_CITED, PROV_OWNED):
            raise ValueError(f"{self.mnemonic}: provenance must be cited or owned")
        if self.provenance == PROV_CITED and not self.source:
            raise ValueError(f"{self.mnemonic}: a cited rule must name its anchor")
        if self.provenance == PROV_OWNED and self.source:
            raise ValueError(f"{self.mnemonic}: an owned rule must not claim a source")
        if self.canonical_unit not in self.units:
            raise ValueError(f"{self.mnemonic}: canonical unit missing from accepted units")


@dataclass(frozen=True)
class MnemonicMatch:
    """A mnemonic resolved to a canonical curve, with how it was resolved.

    Carries the raw declaration alongside the normalized view: the build's rule
    is that a converted value always retains its original, and a normalized
    mnemonic is a conversion of a name.
    """

    raw_mnemonic: str
    raw_unit: str | None
    raw_vendor: str | None
    raw_era: int | None
    mnemonic_key: str
    canonical: str
    measures: str
    family: str
    canonical_unit: str
    declared_unit: str | None
    match: str                          # exact | unit_relaxed | era_conditional
    conditional: bool
    provenance: str
    source: str
    rule_note: str
    needs_unit_convert: bool = False
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)
    registered: Any = None

    def __repr__(self) -> str:  # keeps test failures readable
        cond = "" if not self.conditional else " CONDITIONAL"
        return f"MnemonicMatch({self.raw_mnemonic!r} -> {self.canonical}, {self.match}{cond})"


# --------------------------------------------------------------------------
# The dictionary. OWNED ARTEFACT.
# --------------------------------------------------------------------------
# The KGS curve-mnemonic table is not in this corpus. Each entry below is
# either `cited` - a corpus segment states the mnemonic's meaning while using
# the curve - or `owned` with no corpus support and a note saying so. Nothing
# was added from recollection of a vendor catalogue: a mnemonic that "everyone
# knows" but that no corpus document names is deliberately absent, and refuses.
#
# Every entry is vendor-independent. See VENDOR_EMPTY.
RULES: tuple[MnemonicRule, ...] = (
    # ---- potential and lithology indicators -------------------------------
    MnemonicRule(
        "SP", "SP", "spontaneous potential between a moveable electrode in the "
        "well bore and a fixed electrode at the surface", FAMILY_POTENTIAL,
        "MV", ("MV",), PROV_CITED, ASQ_SP,
        era_first=1945, era_basis=ERA_ES_START,
        note='asquith#12: "The spontaneous potential (SP) log ... It is measured in '
             'millivolts (mV)." beg#34 lists SP among the four ES-log measurements from 1945.',
    ),
    MnemonicRule(
        "GR", "GR", "natural gamma radioactivity of the formation", FAMILY_LITHOLOGY,
        "GAPI", ("GAPI",), PROV_CITED, ASQ_GR,
        era_first=1965, era_basis=ERA_LATE_60S_SUITE,
        note='asquith#15: "The gamma ray log (GR) ... ranges from 0 to 150 API gamma ray '
             'units." Era from beg#34: the GR tool arrives with the late-1960s suite.',
    ),
    MnemonicRule(
        "CALI", "CALI", "borehole diameter", FAMILY_BOREHOLE,
        "IN", ("IN", "MM"), PROV_CITED, ASQ_TRACKS,
        era_first=1945, era_basis=ERA_MICROLOG_CALIPER,
        note='asquith#27: "the caliper measures the borehole diameter from 6 to 16 inches"; '
             'asquith#20: "a caliper (CALI) and gamma ray (GR) in track 1". The caliper is '
             'NOT subject to the 1940s-50s resistivity-only rule: beg#34 puts a caliper on '
             'the microlog in that era.',
    ),
    # ---- sonic ------------------------------------------------------------
    MnemonicRule(
        "DT", "DT", "interval transit time of a compressional sound wave", FAMILY_POROSITY,
        "USEC/FT", ("USEC/FT", "USEC/M"), PROV_CITED, ASQ_SONIC,
        era_first=1965, era_basis=ERA_LATE_60S_SUITE,
        note='asquith#16: "interval transit time (delta t, delta t, or DT)" ... "in '
             'microseconds per foot, usec/ft (or microseconds per meter, usec/m)". Era from '
             'beg#34: the borehole compensated sonic is "newly developed" in the late 1960s.',
    ),
    MnemonicRule(
        "SPHI", "SPHI", "sonic-derived porosity", FAMILY_POROSITY,
        "V/V", ("V/V", "PCT"), PROV_CITED, ASQ_SONIC,
        era_first=1965, era_basis=ERA_LATE_60S_SUITE,
        note='asquith#16: "A sonic-derived porosity curve (SPHI) is sometimes displayed in '
             'tracks 2 and 3, along with the DT curve."',
    ),
    # ---- density ----------------------------------------------------------
    MnemonicRule(
        "RHOB", "RHOB", "bulk density of the entire formation, solid and fluid",
        FAMILY_POROSITY, "G/CM3", ("G/CM3", "KG/M3", "MG/M3"), PROV_CITED, ASQ_DENS,
        era_first=1970, era_basis=ERA_1970S_POROSITY,
        note='asquith#18: "the bulk density (rho_b or RHOB)" and "Density is measured in '
             'grams per cubic centimeter, g/cm3 (or Kg/m3 or Mg/m3)". The three scales are '
             'why the unit is enforced: kg/m3 into Asquith Eq. 4.7 is a factor of 1000 out.',
    ),
    MnemonicRule(
        "DRHO", "DRHO", "density correction applied for borehole effects; a "
        "quality-control indicator, not a formation measurement", FAMILY_POROSITY,
        "G/CM3", ("G/CM3", "KG/M3"), PROV_CITED, ASQ_DENS,
        era_first=1970, era_basis=ERA_1970S_POROSITY,
        note='asquith#18: "A correction curve (DRHO in g/cm3 or Kg/m3) ... Whenever the '
             'correction curve (DRHO) exceeds 0.20 g/cm3, the value of the bulk density ... '
             'should be considered suspect." tools/petrophysics.py DRHO_SUSPECT = 0.20 is '
             'bound to g/cm3, so a kg/m3 DRHO matched silently would disable that gate.',
    ),
    MnemonicRule(
        "DPHI", "DPHI", "density-derived porosity", FAMILY_POROSITY,
        "V/V", ("V/V", "PCT"), PROV_CITED, ASQ_DENS,
        era_first=1970, era_basis=ERA_1970S_POROSITY,
        note='asquith#18: "A density-derived porosity curve (DPHI) is sometimes present in '
             'tracks 2 and 3"; asquith#20 pairs DPHI with NPHI on the neutron-density display.',
    ),
    MnemonicRule(
        "PEF", "PEF", "photoelectric effect, used to determine lithology", FAMILY_LITHOLOGY,
        "B/E", ("B/E",), PROV_CITED, ASQ_DENS,
        era_first=1980, era_basis=ERA_1980S_PEF,
        note='asquith#18: "the photoelectric-effect measurement (P_e, PE, or PEF)" and "the '
             'photoelectric-effect curve (P_e in barns per electron, b/e)".',
    ),
    MnemonicRule(
        "PE", "PEF", "photoelectric effect, used to determine lithology", FAMILY_LITHOLOGY,
        "B/E", ("B/E",), PROV_CITED, ASQ_DENS,
        era_first=1980, era_basis=ERA_1980S_PEF,
        note='asquith#18 gives "P_e, PE, or PEF" as one measurement; folded to canonical PEF.',
    ),
    # ---- neutron ----------------------------------------------------------
    MnemonicRule(
        "NPHI", "NPHI", "liquid-filled porosity from hydrogen concentration; carries a "
        "matrix reference, normally limestone", FAMILY_POROSITY,
        "V/V", ("V/V", "PCT"), PROV_CITED, ASQ_NEUT,
        era_first=1970, era_basis=ERA_1970S_POROSITY,
        note='asquith#19: "the neutron log measures liquid-filled porosity (phi_N, PHIN, or '
             'NPHI)"; asquith#18 shows the curve on a "-0.10 (-10%) to +0.30 (30%)" scale, '
             'which is why both V/V and PCT are accepted and the scale is reported. '
             'asquith#20: "normally recorded in limestone porosity units" - the matrix '
             'reference must travel with the curve (see the unit_convert #11 catalog note).',
    ),
    MnemonicRule(
        "PHIN", "NPHI", "liquid-filled porosity from hydrogen concentration; carries a "
        "matrix reference, normally limestone", FAMILY_POROSITY,
        "V/V", ("V/V", "PCT"), PROV_CITED, ASQ_NEUT,
        era_first=1970, era_basis=ERA_1970S_POROSITY,
        note='asquith#19 gives "phi_N, PHIN, or NPHI" as one measurement; folded to NPHI.',
    ),
    # ---- resistivity: induction ------------------------------------------
    MnemonicRule(
        "ILD", "ILD", "deep induction resistivity; usually true formation resistivity Rt, "
        "beyond the outer boundary of the invaded zone", FAMILY_RESISTIVITY,
        "OHM-M", ("OHM-M",), PROV_CITED, ASQ_CURVES,
        note='asquith#11: "Log curve ILD: Deep induction log resistivity curves usually '
             'measure true formation resistivity (R_t)". beg#34 lists Deep Induction (ILD) '
             'among the three IES-log measurements. No era window: induction is a '
             'resistivity measurement, so the 1940s-50s restriction does not bite.',
    ),
    MnemonicRule(
        "ILM", "ILM", "medium induction resistivity; the invaded zone Ri", FAMILY_RESISTIVITY,
        "OHM-M", ("OHM-M",), PROV_CITED, ASQ_CURVES,
        note='asquith#11: "Log curve ILM: Medium induction log resistivity curves measure '
             'the resistivity of the invaded zone (R_i)."',
    ),
    MnemonicRule(
        "SFL", "SFL", "spherically focused resistivity; the flushed zone Rxo",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_RESTAB,
        era_first=1965, era_basis=ERA_SHORT_NORMAL_END,
        note='asquith#30 Table 5.1 lists the Spherically Focused Log (SFL) among the '
             'galvanic devices; beg#34 dates its arrival to the late 1960s, replacing the '
             'Short Normal.',
    ),
    MnemonicRule(
        "SFLU", "SFL", "spherically focused resistivity; the flushed zone Rxo",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_CURVES,
        era_first=1965, era_basis=ERA_SHORT_NORMAL_END,
        note='asquith#11: "Log curve SFLU: Spherically focused log resistivity curves '
             'measure the resistivity of the flushed zone (R_xo)." Folded to canonical SFL; '
             'see open question 3 in the spec.',
    ),
    # ---- resistivity: laterolog ------------------------------------------
    MnemonicRule(
        "LLD", "LLD", "deep laterolog resistivity; usually true formation resistivity Rt",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_CURVES,
        era_first=1970, era_basis=ERA_DUAL_LATEROLOG,
        note='asquith#11: "Log curve LLD: Deep laterolog resistivity curves usually measure '
             'true formation resistivity (R_t)." Era from asquith#30, dual laterolog '
             'commercial in the early 1970s.',
    ),
    MnemonicRule(
        "LLS", "LLS", "shallow laterolog resistivity; the invaded zone Ri",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_CURVES,
        era_first=1970, era_basis=ERA_DUAL_LATEROLOG,
        note='asquith#11: "Log curve LLS: Shallow laterolog resistivity curves measure the '
             'resistivity in the invaded zone (R_i)."',
    ),
    MnemonicRule(
        "LL8", "LL8", "laterolog-8, a shallow-reading focused electrode resistivity",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_RESTAB,
        note='asquith#30 Table 5.1 places Laterolog-8 (LL8) in the invaded-zone column; '
             'asquith#32: "The shallow-reading laterolog may be either a laterolog-8 (LL8) '
             'or a spherically focused log (SFL)." Depth of investigation "similar to the '
             'short normal", i.e. it reads R_i.',
    ),
    # ---- resistivity: microresistivity -----------------------------------
    MnemonicRule(
        "RXO", "RXO", "microresistivity of the flushed zone Rxo", FAMILY_RESISTIVITY,
        "OHM-M", ("OHM-M",), PROV_CITED, ASQ_CURVES,
        note='asquith#11: "Log curve RXO: Microresistivity curves measure the resistivity of '
             'the flushed zone (R_xo)."',
    ),
    MnemonicRule(
        "MSFL", "MSFL", "microspherically focused resistivity of the flushed zone Rxo",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_RESTAB,
        note='asquith#30 Table 5.1, flushed-zone column: MicroSpherically Focused Log '
             '(MSFL). asquith#33: "The microlaterolog (MLL), the proximity log (PL) ... and the microspherically focused log (MSFL) are pad-type, focused, electrode logs designed to measure the resistivity in the flushed zone (R_xo)."',
    ),
    MnemonicRule(
        "MLL", "MLL", "microlaterolog resistivity of the flushed zone Rxo",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_RESTAB,
        note='asquith#30 Table 5.1, flushed-zone column: Microlaterolog (MLL). asquith#33: "The microlaterolog (MLL), the proximity log (PL) ... and the microspherically focused log (MSFL) are pad-type, focused, electrode logs designed to measure the resistivity in the flushed zone (R_xo)." '
             'asquith#33 adds the limit: the MLL "should be run only with saltwater muds".',
    ),
    MnemonicRule(
        "ML", "ML", "microlog resistivity of the flushed zone Rxo; used qualitatively to "
        "find permeable zones from curve cross-over", FAMILY_RESISTIVITY,
        "OHM-M", ("OHM-M",), PROV_CITED, ASQ_RESTAB,
        era_first=1945, era_basis=ERA_ES_START,
        note='asquith#30 Table 5.1: MicroLog (ML), flushed zone. beg#34: the microlog was '
             '"commonly run in Boonsville field" from the ES era and its cross-over below '
             '20 ohm-m "is a good indication of a permeable sand". See spec open question 4.',
    ),
    MnemonicRule(
        "PL", "PL", "proximity log resistivity of the flushed zone Rxo", FAMILY_RESISTIVITY,
        "OHM-M", ("OHM-M",), PROV_CITED, ASQ_RESTAB,
        note='asquith#30 Table 5.1, flushed-zone column: Proximity Log (PL). asquith#33: "The microlaterolog (MLL), the proximity log (PL) ... and the microspherically focused log (MSFL) are pad-type, focused, electrode logs designed to measure the resistivity in the flushed zone (R_xo)."',
    ),
    # ---- resistivity: the pre-induction electrode logs --------------------
    MnemonicRule(
        "SN", "SN", "16-inch short normal resistivity; the invaded zone Ri",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_RESTAB,
        era_first=1945, era_last=1969, era_basis=ERA_SHORT_NORMAL_END,
        note='asquith#30 Table 5.1 places Short Normal (SN) in the invaded-zone column; '
             'beg#34 names it "16-inch Short Normal (SN)" among the four ES measurements and '
             'dates its replacement to the late 1960s. This is the era-dependent case the '
             'catalog anchor exists for.',
    ),
    MnemonicRule(
        "LN", "LN", "64-inch long normal resistivity; the uninvaded zone Rt",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_RESTAB,
        era_first=1945, era_last=1969, era_basis=ERA_SHORT_NORMAL_END,
        note='asquith#30 Table 5.1 places Long Normal (LN) in the uninvaded-zone column; '
             'beg#34 names it "64-inch Long Normal (LN)". The 1969 end is inherited from the '
             'Short Normal sentence - beg#34 gives no separate date for the Long Normal.',
    ),
    MnemonicRule(
        "LAT", "LAT", "18-ft 8-in lateral log resistivity; asymmetric, close to true "
        "resistivity only in sands at least five times the tool's measure length",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, BEG_TIMELINE,
        era_first=1945, era_last=1969, era_basis=ERA_SHORT_NORMAL_END,
        note='beg#34: "18-ft, 8-inch Lateral Log (LAT)" ... "This log was later replaced by '
             'the Induction Log." beg#34 gives NO date for that replacement; the 1969 end is '
             "borrowed from the Short Normal sentence and is the weakest era window here.",
    ),
    # ---- index ------------------------------------------------------------
    # OWNED, no corpus support. kgs-las-2.0-field-table#1 says only that "The
    # index of the data columns is either Depth or Time" and never names the
    # mnemonic. The CWLS LAS 2.0 spec would source these; it is not in the corpus.
    MnemonicRule(
        "MNOR", "MNOR",
        "microlog micronormal, ~2 in. investigation. asquith#37 says it "
        "\"measures the resistivity of the flushed zone\", but asquith#33 is "
        "explicit that the microlog \"generally does not provide a good estimate "
        "of flushed-zone resistivity (R_xo)\" and reserves R_xo for the pad-type "
        "focused tools (MLL, PL, MSFL). Its real use is the MNOR > MINV positive "
        "separation that indicates mudcake, hence permeability",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_MICROLOG,
        note='asquith#37: "The micronormal log (MNOR, shown by the dashed line) '
             'measures the resistivity of the flushed zone, and the microinverse '
             '(MINV, shown by the solid line) measures the resistivity of any '
             'mudcake that might be present." Both tokens are named in the text, '
             'so these are cited rules rather than owned ones. Consumed by '
             'microlog_permeability_flag (#38), which takes values not mnemonics '
             '- this entry exists because the curves came back unidentified on '
             'both real fixtures, which carry MINV/MNOR and nothing else names them.',
    ),
    MnemonicRule(
        "MINV", "MINV",
        "microlog microinverse, ~1 in. investigation; reads the mudcake "
        "resistivity R_mc rather than the formation. Positive separation "
        "(MNOR > MINV) indicates mudcake and therefore permeability",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_CITED, ASQ_MICROLOG,
        note='asquith#37, same sentence as MNOR. asquith#33 gives the depths of '
             'investigation: the micronormal "investigates three to four inches" '
             'and the microinverse "approximately one to two inches and is '
             'significantly affected by the resistivity of the mudcake".',
    ),
    MnemonicRule(
        "RFOC", "RFOC",
        "shallow focused resistivity; the third curve of a dual induction. Which "
        "zone it reads is NOT settled by the corpus: asquith#32 twice puts the "
        "dual induction's shallow focused curve in the invaded zone "
        "(\"similar in depth of investigation to the short normal\"; "
        "\"R_i = resistivity tool measuring in the invaded zone, usually "
        "laterolog-8 or spherically focused log\"), while asquith#11's SFLU "
        "caption reads a spherically focused curve as the flushed zone R_xo. "
        "asquith#33 reserves R_xo for the pad-type micro devices (MLL, PL, MSFL). "
        "Consumers must treat the zone as undetermined rather than assume R_xo",
        FAMILY_RESISTIVITY, "OHM-M", ("OHM-M",), PROV_OWNED,
        note="OWNED, uncited SPELLING. The device class is well sourced - "
             "asquith#32 defines the dual induction's shallow focused curve and "
             "asquith#33 the pad-type R_xo tools - but the token 'RFOC' appears "
             "nowhere in the corpus, so this cannot be a cited rule. It is here "
             "because leaving it unidentified made every analysis on "
             "repass-2-stephens-tx-1983.las (ILD/ILM/RFOC, a textbook dual "
             "induction) blocked for want of a shallow curve. The Ri-vs-Rxo "
             "question is deliberately left open in `measures`: resolving it "
             "silently would hand analysis_feasibility (#101) an R_xo the "
             "corpus does not support. A vendor mnemonic list would source the "
             "spelling; a source reconciling asquith#11 with #32 would settle "
             "the zone.",
    ),
    MnemonicRule(
        "DEPT", "DEPT", "measured depth along the wellbore; the LAS index column",
        FAMILY_INDEX, "FT", ("FT", "M"), PROV_OWNED,
        note="OWNED, uncited. kgs-las-2.0-field-table#1 says the index is Depth or Time but "
             "never gives its mnemonic. The CWLS LAS 2.0 specification "
             "(cwls.org/docs/las_20_updated_july2009.pdf, linked from that page but not "
             "ingested) would source it.",
    ),
    MnemonicRule(
        "DEPTH", "DEPT", "measured depth along the wellbore; the LAS index column",
        FAMILY_INDEX, "FT", ("FT", "M"), PROV_OWNED,
        note="OWNED, uncited. Spelled-out variant of the index mnemonic; folded to DEPT.",
    ),
    MnemonicRule(
        "MD", "DEPT", "measured depth along the wellbore; the LAS index column",
        FAMILY_INDEX, "FT", ("FT", "M"), PROV_OWNED,
        note="OWNED, uncited. Measured-depth spelling of the index mnemonic; folded to DEPT. "
             "Note md_to_tvd (#17) distinguishes MD from TVD - this entry asserts only that "
             "the curve is a measured depth, not that it is the index of this file.",
    ),
)

_BY_MNEMONIC: dict[str, tuple[MnemonicRule, ...]] = {}
for _rule in RULES:
    _BY_MNEMONIC.setdefault(_rule.mnemonic, ())
    _BY_MNEMONIC[_rule.mnemonic] += (_rule,)


# --------------------------------------------------------------------------
# The register (#10), written concurrently in the same module
# --------------------------------------------------------------------------
# The two halves of this module were specified independently and did not agree.
# `mnemonic_normalize` assumed a flat `(mnemonic, *, unit, vendor, era, reason,
# context)`; the register above requires a **well identity** and keys occurrences
# on `(well_id, source_file)`, which is what makes a re-ingest a no-op and a
# second well new evidence. The register's contract is the one that survives:
# dropping well identity to satisfy the caller would make those two cases
# indistinguishable. So the caller adapts, here, in one place.
#
# `context` carries the well the mnemonic was seen in. The two names the
# register cannot do without are `well_id` and `source_file`; everything else it
# accepts is passed through when present.
_FALLBACK_LOG: list[dict[str, Any]] = []
_REGISTER_UNAVAILABLE = "unknown-register-unavailable: logged to _FALLBACK_LOG in this module"
_REGISTER_NO_WELL = (
    "unknown-mnemonic not registered: no well identity in `context`; "
    "pass context={'well_id': ..., 'source_file': ...} so the register can tell "
    "a re-ingest from a second well"
)

# Context keys the register takes verbatim. `vendor` and `era` are named
# differently on the two sides and are mapped below rather than renamed on
# either, because `vendor`/`era` is the normalizer's dictionary key and
# `service_company`/`era_year` is what a reviewer reads off a header.
_REGISTER_CONTEXT_KEYS = (
    "well_id", "source_file", "well_name", "api", "description",
    "service_company", "log_date", "depth_start", "depth_stop", "depth_unit",
    "values", "null_value", "registry_path",
)


def _fallback_register(mnemonic: str, **kw: Any) -> None:
    """Stand-in used only when the register is genuinely absent.

    Records rather than discards: an unmapped mnemonic that vanished is a
    dictionary that cannot grow, which is the one job of the pair.
    """
    _FALLBACK_LOG.append({"mnemonic": mnemonic, **kw})
    return None


def _resolve_register() -> tuple[Callable[..., Any], bool]:
    """Return (register, available). The sibling is in this module's globals."""
    fn = globals().get("mnemonic_unknown_register")
    if callable(fn):
        return fn, True
    return _fallback_register, False


def _call_register(register: Callable[..., Any], mnemonic: str, *, unit: str | None,
                   vendor: str | None, era: int | None, reason: str,
                   context: dict[str, Any] | None) -> Any:
    """Record one unmapped mnemonic, adapting to the register's own signature.

    Returns whatever the register returned - including its `Refusal` when the
    context carried no well identity. The refusal is handed back rather than
    raised: failing to log a mnemonic must not abort normalization of the forty
    curves in the same file that mapped cleanly.
    """
    ctx = dict(context) if context else {}
    kw: dict[str, Any] = {k: ctx[k] for k in _REGISTER_CONTEXT_KEYS if k in ctx}
    well_id = kw.pop("well_id", None)
    if vendor is not None:
        kw.setdefault("service_company", vendor)
    if era is not None:
        kw["era"] = era
    if not well_id:
        return Refusal(
            reason=_REGISTER_NO_WELL,
            needed=("context['well_id'] - the API number, or another stable well identity",),
            source=NO_CITATION,
        )
    if register is _fallback_register:
        return register(mnemonic, well_id=well_id, unit=unit, reason=reason, **kw)
    return register(mnemonic, well_id, unit=unit, reason=reason, **kw)


# --------------------------------------------------------------------------
# Normalization helpers
# --------------------------------------------------------------------------
def _normalize_mnemonic(raw: str) -> tuple[str, tuple[str, ...]]:
    """Uppercase and strip the two owned suffix conventions, flagging each.

    Nothing else. No fuzzy matching, no prefix stripping, no edit distance -
    every one of those is a way of guessing, which is what this tool forbids.
    """
    flags: list[str] = []
    key = raw.strip().upper()
    if key.endswith("."):
        key = key[:-1].strip()
        flags.append("mnemonic-trailing-dot-stripped")
    if ":" in key:
        head, _, tail = key.rpartition(":")
        if head and tail.isdigit():
            key = head.strip()
            flags.append(f"mnemonic-run-suffix-stripped: ':{tail}' (owned LAS convention)")
    return key, tuple(flags)


def _normalize_unit(raw: str | None) -> str | None:
    """Declared unit to a canonical token, or None if absent/unrecognized."""
    if raw is None:
        return None
    token = raw.strip().upper()
    if not token or token in (".", "-"):
        return None
    token = token.lstrip(".")
    return UNIT_SYNONYMS.get(token)


def _era_flags(rule: MnemonicRule, era: int | None) -> tuple[str, ...]:
    if era is None:
        return ()
    flags = [f"era-window-is-advisory: {ERA_ADVISORY}"]
    if rule.era_first is not None and era < rule.era_first:
        flags.append(
            f"era-implausible: {rule.canonical} logged {era}, but this rule's window opens "
            f"{rule.era_first}. {rule.era_basis or '(no era basis recorded on this rule)'}"
        )
    if rule.era_last is not None and era > rule.era_last:
        flags.append(
            f"era-implausible: {rule.canonical} logged {era}, but this rule's window closes "
            f"{rule.era_last}. {rule.era_basis or '(no era basis recorded on this rule)'}"
        )
    return tuple(flags)


def _era_admits(rule: MnemonicRule, era: int) -> bool:
    if rule.era_first is not None and era < rule.era_first:
        return False
    if rule.era_last is not None and era > rule.era_last:
        return False
    return True


# --------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------
def mnemonic_normalize(
    mnemonic: str,
    unit: str | None = None,
    vendor: str | None = None,
    era: int | None = None,
    *,
    register: Callable[..., Any] | None = None,
    context: dict[str, Any] | None = None,
    rules: tuple[MnemonicRule, ...] | None = None,
) -> MnemonicMatch | Refusal:
    """Map one raw curve mnemonic to a canonical curve, or refuse.

    Never guesses. An unmapped mnemonic, an ambiguous one, and one whose
    declared unit contradicts the dictionary are all `Refusal`s, and all three
    are recorded through `mnemonic_unknown_register` (#10) so the dictionary can
    grow from the log rather than from recollection.

    A mapping made without a declared unit, or under an era/vendor assumption,
    is a *conditional* match: it is returned, but `conditional` is True, the
    assumption is on `assumptions`, and it is registered as a dictionary gap.
    """
    if not isinstance(mnemonic, str):
        raise ValueError(f"mnemonic must be a str, got {type(mnemonic).__name__}")
    if era is not None and not isinstance(era, int):
        raise ValueError(f"era must be a four-digit year as int, got {era!r}")
    if unit is not None and not isinstance(unit, str):
        raise ValueError(f"unit must be a str or None, got {type(unit).__name__}")

    reg, reg_available = (register, True) if register is not None else _resolve_register()
    ctx = dict(context) if context else None  # never hand the caller's dict onward

    table = RULES if rules is None else tuple(rules)
    index: dict[str, tuple[MnemonicRule, ...]] = _BY_MNEMONIC
    if rules is not None:
        index = {}
        for r in table:
            index[r.mnemonic] = index.get(r.mnemonic, ()) + (r,)

    flags: list[str] = []
    if rules is not None:
        flags.append("non-default-rule-table: results are not from the seeded dictionary")
    if not reg_available:
        flags.append(_REGISTER_UNAVAILABLE)

    key, key_flags = _normalize_mnemonic(mnemonic)
    flags.extend(key_flags)

    def _refuse(reason_code: str, reason: str, needed: tuple[str, ...]) -> Refusal:
        receipt = _call_register(reg, key, unit=unit, vendor=vendor, era=era,
                                 reason=reason_code, context=ctx)
        local = list(flags)
        if isinstance(receipt, Refusal):
            # The mnemonic was refused AND not logged. Say both, or the operator
            # is told the dictionary will grow from this when it will not.
            local.append(f"not registered: {receipt.reason}")
        note = "; ".join(local)
        return Refusal(
            reason=reason + (f" [{note}]" if note else ""),
            needed=needed,
            source=BEG_TIMELINE,
        )

    if not key:
        return _refuse(
            REASON_BLANK,
            f"blank curve mnemonic (raw {mnemonic!r}); nothing to map",
            ("a non-empty ~C mnemonic",),
        )

    candidates = index.get(key, ())
    if not candidates:
        return _refuse(
            REASON_UNKNOWN,
            f"{key!r} is not in the mnemonic dictionary and will not be guessed. "
            "The dictionary is an owned artefact - the canonical KGS curve-mnemonic table "
            "is not in this corpus - so absence means unadjudicated, not invalid.",
            (
                f"a reviewed dictionary entry for {key!r}",
                "or the KGS curve-mnemonic table ingested into 02-las-format/",
            ),
        )

    # --- vendor ---------------------------------------------------------
    if vendor:
        v = vendor.strip().casefold()
        vendor_specific = tuple(c for c in candidates if c.vendor and c.vendor.casefold() == v)
        if vendor_specific:
            candidates = vendor_specific
        else:
            candidates = tuple(c for c in candidates if c.vendor is None)
            flags.append(f"vendor-declared-but-not-discriminating: {vendor!r}. {VENDOR_EMPTY}")
    else:
        candidates = tuple(c for c in candidates if c.vendor is None) or candidates

    # --- era: may break a tie, may never veto the last candidate ---------
    grade = "exact"
    conditional = False
    if era is not None and len(candidates) > 1:
        admitted = tuple(c for c in candidates if _era_admits(c, era))
        if admitted and len(admitted) < len(candidates):
            candidates = admitted
            grade = "era_conditional"
            conditional = True
            flags.append(
                f"era-conditional: {len(admitted)} of the competing rules admit a {era} log; "
                f"the choice rests on beg#34's timeline. {ERA_ADVISORY}"
            )

    # --- unit ------------------------------------------------------------
    declared = _normalize_unit(unit)
    assumptions: dict[str, Any] = {}
    needs_convert = False

    if declared is None:
        grade = grade if grade == "era_conditional" else "unit_relaxed"
        conditional = True
        if unit is None or not unit.strip():
            flags.append(
                "unit-not-declared: mapped on the mnemonic alone. The same mnemonic under a "
                "different unit can be a different scale or a different measurement, so this "
                "is a conditional match."
            )
        else:
            flags.append(
                f"declared-unit-not-recognized: {unit!r} is not a known spelling, so it "
                "could neither confirm nor contradict the rule."
            )
    else:
        matching = tuple(c for c in candidates if declared in c.units)
        if not matching:
            allowed = sorted({u for c in candidates for u in c.units})
            return _refuse(
                REASON_UNIT_CONFLICT,
                f"{key!r} is declared in {unit!r} (read as {declared}), which no dictionary "
                f"rule for it accepts; the rules allow {allowed}. Matching anyway would be a "
                "data-corruption path, not a convenience.",
                (
                    f"a corrected ~C unit for {key!r}",
                    f"or a reviewed dictionary entry for {key!r} in {declared}",
                ),
            )
        candidates = matching

    # --- resolve ---------------------------------------------------------
    if len(candidates) > 1:
        separators = []
        if declared is None:
            separators.append("a declared unit")
        if not vendor:
            separators.append("the service company (~W SRVC)")
        if era is None:
            separators.append("the log year (~W DATE)")
        return _refuse(
            REASON_AMBIGUOUS,
            f"{key!r} matches {len(candidates)} dictionary rules "
            f"({', '.join(sorted(c.canonical for c in candidates))}); it will not be "
            "resolved by picking one.",
            tuple(separators) or ("a dictionary review to separate the competing rules",),
        )

    rule = candidates[0]

    if declared is None:
        assumptions["assumed_unit"] = rule.canonical_unit
    elif declared != rule.canonical_unit:
        needs_convert = True
        flags.append(
            f"unit-scale-differs-from-canonical: declared {declared}, canonical "
            f"{rule.canonical_unit}. This tool does not convert - unit_convert (#11) does, "
            "and the original is retained here."
        )

    flags.extend(_era_flags(rule, era))

    if rule.provenance == PROV_OWNED:
        conditional = True
        flags.append(
            "owned-rule-no-corpus-source: this entry is asserted by this project with no "
            "corpus support. " + rule.note
        )

    if vendor:
        assumptions["vendor_declared"] = vendor
    if era is not None:
        assumptions["era_declared"] = era
        assumptions["rule_era_window"] = (rule.era_first, rule.era_last)

    registered = None
    if conditional:
        registered = _call_register(reg, key, unit=unit, vendor=vendor, era=era,
                                    reason=REASON_CONDITIONAL, context=ctx)
        if isinstance(registered, Refusal):
            flags.append(f"not registered: {registered.reason}")

    return MnemonicMatch(
        raw_mnemonic=mnemonic,
        raw_unit=unit,
        raw_vendor=vendor,
        raw_era=era,
        mnemonic_key=key,
        canonical=rule.canonical,
        measures=rule.measures,
        family=rule.family,
        canonical_unit=rule.canonical_unit,
        declared_unit=declared,
        match=grade,
        conditional=conditional,
        provenance=rule.provenance,
        source=rule.source,
        rule_note=rule.note,
        needs_unit_convert=needs_convert,
        flags=tuple(flags),
        assumptions=assumptions,
        registered=registered,
    )
