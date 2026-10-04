"""Document handling for user-supplied non-RRC paper. Destination: `tools/documents.py`.

`document_extract` (#5) was specified to do two unrelated jobs, and only one of them
is supportable. It is split here rather than blurred.

**The structured-field half refuses, always.** Turning a scout ticket or a mud log
into named fields requires a schema — a published statement of what fields that
document type has and what they mean — and the corpus contains none for any of the
five types the catalog names. Searches are recorded in `specs/05-document_extract.md`;
the short version is that "scout" appears in the corpus only as Boy Scout camps, lease
scouts in 1919 prose, and three bibliography lines, and the one place `toc/TOC.md`
mentions mud logging at all is a *"Not good for"* disclaimer. Deciding the field list
myself would be an invented standard presented as sourced, which is the failure this
layer exists to prevent, and no model may be called from a tool to decide it either.
So the refusal is per document type and each one names the specific acquisition that
would unblock it.

DST tickets are the one type whose field list does exist: the Fig 8.1 caption at
`03-dst/earlougher-well-test-analysis-part2-1977#1` names the six chart-stage
pressures. That list already belongs to `dst_structure` (#41, group E). This tool
refuses `dst_ticket` and redirects rather than duplicating it — two implementations of
one field list is the reconcile failure, not a convenience.

**The verbatim half is implemented**, because returning the document's own bytes with
a page reference asserts nothing about the document's meaning and so needs no
petrophysical authority. Three rules keep it from drifting into the refused half:
text is returned unmodified (no strip, no case folding, no dehyphenation); pagination
comes from the caller and is never inferred from blank lines or running heads, since a
guessed page number is a false provenance claim; and search is literal substring only,
never regex, so no library of field patterns ("the IP line looks like…") can accrete
inside the tool.

`Excerpt` is not a `Quantity` — it has no value, unit or method. It carries the
provenance a quote needs instead: document id, page as the caller numbers it, and
offsets that re-slice to exactly the returned text.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .result import Quantity, Range, Refusal  # noqa: F401  (contract import)

# There is no corpus source for a document schema. The empty string is the honest
# value for `Refusal.source`; a plausible-looking anchor here would be the lie.
NO_SOURCE = ""

# Where a DST ticket's fields actually live, and who owns them.
EARLOUGHER_FIG_8_1 = "03-dst/earlougher-well-test-analysis-part2-1977#1"

# Page-break convention for `paginate`. Declared, not detected.
FORM_FEED = "\f"

# What would have to be acquired, per document type, before the structured half could
# be written. Keyed by the doc_type strings this tool accepts. Nothing in this table
# is a field list — that is the point; each entry names a document to go and get.
SCHEMA_NEEDED: dict[str, tuple[str, ...]] = {
    "scout_ticket": (
        "a published scout-ticket field specification: a scout-service data "
        "dictionary or record layout defining field names, meanings and units",
        "the vendor and vintage of the ticket, since layouts are not comparable "
        "across decades",
    ),
    "dst_ticket": (
        "nothing to acquire: the DST field list is Fig 8.1 at "
        f"{EARLOUGHER_FIG_8_1} and is implemented by dst_structure (#41)",
    ),
    "mud_log": (
        "a mud-log format specification (API/IADC mud-logging record standard, or a "
        "service-company mud-log legend) defining tracks, gas units, lag correction "
        "and depth registration",
    ),
    "core_report": (
        "a routine-core-analysis reporting standard (API RP 40 or equivalent) "
        "defining the reported quantities, their confining conditions and units",
    ),
    "engineering_memo": (
        "no schema is acquirable: free-form prose has no field list, so only the "
        "verbatim path applies to memos",
    ),
}

DOC_TYPES: tuple[str, ...] = tuple(SCHEMA_NEEDED)


@dataclass(frozen=True)
class Excerpt:
    """A verbatim span with the provenance needed to find it again.

    `text` is always exactly `page_text[char_start:char_end]` of the page the caller
    supplied. Nothing is normalised, so a quote can be located in the original.
    """

    document_id: str
    page: int
    char_start: int
    char_end: int
    text: str


# --------------------------------------------------------------------------- #
# The catalog tool: structured fields. Refuses, per document type.
# --------------------------------------------------------------------------- #

def document_extract(
    document_id: str,
    pages: Sequence[str],
    doc_type: str,
    fields: Sequence[str] | None = None,
) -> Refusal:
    """Structured fields from a non-RRC document. Always refuses — see module docstring.

    The refusal is a returned value. `needed` names the specific document that would
    have to be acquired for this `doc_type`, not a generic "more sources".
    """
    _require_text_pages(pages)
    key = (doc_type or "").strip().lower()
    wanted = tuple(fields or ())
    asked = f" (asked for: {', '.join(wanted)})" if wanted else ""

    if key == "dst_ticket":
        return Refusal(
            reason=(
                f"document_extract does not structure DST tickets{asked}. The DST "
                f"field list exists in the corpus — the Fig 8.1 caption at "
                f"{EARLOUGHER_FIG_8_1} names the six chart-stage pressures (p_ihm, "
                "p_if1, p_isi, p_if2, p_fsi, p_fhm) — and it belongs to dst_structure "
                "(#41), which takes an already-parsed ticket. Duplicating it here "
                "would give one field list two implementations. Call dst_structure. "
                "For the ticket's own words, use document_verbatim/document_find."
            ),
            needed=SCHEMA_NEEDED["dst_ticket"],
            source=EARLOUGHER_FIG_8_1,
        )

    if key in SCHEMA_NEEDED:
        return Refusal(
            reason=(
                f"no {key.replace('_', ' ')} schema exists in the corpus, so the "
                f"structured fields of document {document_id!r} cannot be produced "
                f"without inventing the field list{asked}. Searched: knowledge-base/ "
                "(18 sections, none on document forms), toc/TOC.md (no document "
                "claims authority; its only 'mud log' mention is a 'Not good for' "
                "disclaimer), and full-text grep for scout ticket / mud log / core "
                "report, whose hits are all narrative mentions rather than field "
                "definitions. A model may not be called to supply the schema. "
                "Verbatim page-anchored text IS available: use document_verbatim, "
                "document_find or document_excerpt."
            ),
            needed=SCHEMA_NEEDED[key],
            source=NO_SOURCE,
        )

    return Refusal(
        reason=(
            f"unknown document type {doc_type!r} for document {document_id!r}{asked}. "
            "This tool does not infer a document's type from its content, and it has "
            "no schema for any type: the corpus supplies none. Known types are "
            f"{', '.join(DOC_TYPES)}, and all of them are refused for the same "
            "reason. Verbatim page-anchored text IS available: use document_verbatim, "
            "document_find or document_excerpt."
        ),
        needed=(
            f"a published field specification for document type {doc_type!r}",
            "a decision to add the type to this tool's catalog entry",
        ),
        source=NO_SOURCE,
    )


# --------------------------------------------------------------------------- #
# The supportable half: verbatim text with page references.
# --------------------------------------------------------------------------- #

def document_verbatim(
    document_id: str,
    pages: Sequence[str],
    page_number: int | None = None,
    first_page_number: int = 1,
) -> tuple[Excerpt, ...] | Refusal:
    """Every page (or one page) as a verbatim, page-anchored excerpt.

    Blank pages are returned with `text=""` rather than dropped: "page 4 is blank" is
    information, and dropping it would silently renumber nothing but mislead a reader
    counting pages.
    """
    _require_text_pages(pages)
    _require_first_page(first_page_number)
    empty = _refuse_if_nothing_to_read(document_id, pages)
    if empty is not None:
        return empty

    if page_number is None:
        wanted = range(first_page_number, first_page_number + len(pages))
    else:
        _require_page_in_range(page_number, pages, first_page_number)
        wanted = range(page_number, page_number + 1)

    out = []
    for n in wanted:
        text = pages[n - first_page_number]
        out.append(Excerpt(document_id, n, 0, len(text), text))
    return tuple(out)


def document_find(
    document_id: str,
    pages: Sequence[str],
    needle: str,
    case_sensitive: bool = False,
    context_chars: int = 0,
    first_page_number: int = 1,
) -> tuple[Excerpt, ...] | Refusal:
    """Every occurrence of a literal substring, as page-anchored verbatim spans.

    Literal only — regex is deliberately not offered, so that no table of field
    patterns can grow inside this module and become an unsourced schema. Matching may
    be case-insensitive, but the returned `text` is always the original casing, cut
    from the page.
    """
    _require_text_pages(pages)
    _require_first_page(first_page_number)
    if not isinstance(needle, str) or needle == "":
        raise ValueError("needle must be a non-empty literal string")
    if context_chars < 0:
        raise ValueError("context_chars must be >= 0")
    empty = _refuse_if_nothing_to_read(document_id, pages)
    if empty is not None:
        return empty

    probe = needle if case_sensitive else _fold(needle)
    out = []
    for offset, text in enumerate(pages):
        hay = text if case_sensitive else _fold(text)
        at = hay.find(probe)
        while at != -1:
            start = max(0, at - context_chars)
            end = min(len(text), at + len(needle) + context_chars)
            out.append(
                Excerpt(
                    document_id=document_id,
                    page=first_page_number + offset,
                    char_start=start,
                    char_end=end,
                    text=text[start:end],
                )
            )
            at = hay.find(probe, at + 1)
    return tuple(out)


def document_excerpt(
    document_id: str,
    pages: Sequence[str],
    page_number: int,
    char_start: int,
    char_end: int,
    first_page_number: int = 1,
) -> Excerpt:
    """One half-open span `[char_start, char_end)` of one page, verbatim."""
    _require_text_pages(pages)
    _require_first_page(first_page_number)
    _require_page_in_range(page_number, pages, first_page_number)
    text = pages[page_number - first_page_number]
    if not 0 <= char_start <= char_end <= len(text):
        raise ValueError(
            f"span [{char_start}, {char_end}) is not inside page {page_number}, "
            f"which is {len(text)} characters long"
        )
    return Excerpt(document_id, page_number, char_start, char_end, text[char_start:char_end])


def paginate(text: str, first_page_number: int = 1) -> list[str] | Refusal:
    """Split on ASCII form feed only. Refuses text with no form feed in it.

    Page boundaries are not guessed from blank lines, running heads or numbers on the
    page: a wrong page number is a false provenance claim, and heuristics here would
    manufacture one silently.
    """
    if not isinstance(text, str):
        raise TypeError("paginate takes text, not bytes or pixels")
    _require_first_page(first_page_number)
    if FORM_FEED not in text:
        return Refusal(
            reason=(
                "the supplied text contains no form-feed page breaks, so its page "
                "boundaries are unknown. This tool will not infer them from blank "
                "lines or running heads, because a guessed page number would be "
                "reported as provenance."
            ),
            needed=(
                "text with \\f page breaks, or the pages supplied separately as a "
                "sequence of strings",
            ),
            source=NO_SOURCE,
        )
    return text.split(FORM_FEED)


# --------------------------------------------------------------------------- #
# Argument checking. Exceptions are for impossible arguments; refusals are for
# "there is nothing here to answer from".
# --------------------------------------------------------------------------- #

def _fold(text: str) -> str:
    """Lowercase for matching *without changing the string's length*.

    `str.lower()` is not length-preserving — `'İ'.lower()` is two characters —
    and an offset taken from a folded haystack is then wrong against the original
    page. The span returned would still re-slice, so it looks verbatim, while
    pointing at characters the caller never searched for: a false provenance claim,
    the one failure this module is built to avoid. Characters whose lowercase is not
    a single character are therefore left as they are; they simply do not match
    case-insensitively, which is a missed match rather than a mislocated one.
    """
    lowered = text.lower()
    if len(lowered) == len(text):
        return lowered
    return "".join(c.lower() if len(c.lower()) == 1 else c for c in text)


def _require_text_pages(pages: Any) -> None:
    if isinstance(pages, str) or not isinstance(pages, Sequence):
        raise TypeError("pages must be a sequence of page strings, not a single string")
    for i, page in enumerate(pages):
        if not isinstance(page, str):
            raise TypeError(
                f"page at index {i} is {type(page).__name__}, not str; this tool "
                "reads text, never bytes or images (a scan goes to raster_header_ocr)"
            )


def _require_first_page(first_page_number: int) -> None:
    if not isinstance(first_page_number, int) or first_page_number < 1:
        raise ValueError("first_page_number must be an integer >= 1")


def _require_page_in_range(page_number: int, pages: Sequence[str], first: int) -> None:
    last = first + len(pages) - 1
    if not isinstance(page_number, int) or not first <= page_number <= last:
        raise ValueError(
            f"page {page_number} is outside the supplied range {first}..{last}"
        )


def _refuse_if_nothing_to_read(document_id: str, pages: Sequence[str]) -> Refusal | None:
    if len(pages) == 0:
        return Refusal(
            reason=f"no pages were supplied for document {document_id!r}",
            needed=("the document's page texts, in order",),
            source=NO_SOURCE,
        )
    if all(page.strip() == "" for page in pages):
        return Refusal(
            reason=(
                f"every page of document {document_id!r} is blank, so there is no "
                "verbatim text to quote. The usual cause is a scan that has not been "
                "through OCR."
            ),
            needed=(
                "OCR'd text for the document",
                "or, for a scanned log header, raster_header_ocr (#6)",
            ),
            source=NO_SOURCE,
        )
    return None
