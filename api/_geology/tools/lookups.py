"""Sourced lookup tables: geolex (#61), basin priors (#62), correlation choice (#64).

These three tools have no equation. Their payload *is* the citation, so the
provenance contract is stronger here than elsewhere: **every field of every
record carries the anchor of the segment it was transcribed from**, not just the
call as a whole. `basin_prior_lookup` is the clearest case — its four answers come
from four different segments of one report, and a single tool-level `source`
string would misattribute three of them.

Three decisions here are not obvious from the code.

**Nothing resolves silently.** `geolex_lookup` covers an outcrop belt whose
literature renamed the same beds for seventy years, and twice applied a name to
the wrong bed. So an abandoned name returns its current equivalent *together
with* the history that produced it, and where Eargle (1960) states no single
equivalent — "Avis", "Whitt" — the record returns the history and no equivalent
at all rather than picking the likelier reading. A short name that reaches more
than one catalogued unit ("Ricker" reaches three, "Speck Mountain" two) is a
Refusal listing the candidates.

**Normalisation is whitespace, case, and one closed list of rank suffixes.** No
stemming, no substring or prefix matching, no edit distance. Every hit reports
which index it came from and the exact string it matched, so a caller can always
see what happened to what it passed.

**An argument the source does not support is recorded and never used.** The
catalog gives `correlation_selector` a `well_geometry` input; Asquith &
Krygowski chapter 7 states no geometry limit for any of these methods, so the
argument is echoed into `inputs`, excludes nothing, and the result says so.
Inventing a bed-thickness cutoff to make the signature look complete is the
orphan-number failure this project exists to prevent.

Specs: `specs/61-geolex_lookup.md`, `specs/62-basin_prior_lookup.md`,
`specs/64-correlation_selector.md`.
"""
from __future__ import annotations

import functools
import json
import os
import pathlib
import re
from typing import Any

from .result import Quantity, Refusal

# --- anchors -----------------------------------------------------------------
# Eargle, D. H., 1960, USGS Professional Paper 315-D. Brown and Coleman
# Counties, Texas; field mapping 1950-54.
EARGLE = "07-bend-arch/eargle-1960-usgs-pp-315d"
E_INTRO = f"{EARGLE}#2"      # 1950-54 survey years
E_TABLE1 = f"{EARGLE}#3"     # Table 1, the nomenclature column
E_STRAWN_HIST = f"{EARGLE}#4"
E_STRAWN = f"{EARGLE}#5"
E_RICKER = f"{EARGLE}#6"
E_CAPPS = f"{EARGLE}#7"      # also the Canyon group member list
E_GRAFORD = f"{EARGLE}#8"
E_BROWNWOOD = f"{EARGLE}#9"  # also Adams Branch, Cedarton, Winchell
E_WINCHELL_MBRS = f"{EARGLE}#10"  # also Brad, Placid, Ranger
E_CADDO = f"{EARGLE}#14"     # also Colony Creek, Home Creek
E_CISCO = f"{EARGLE}#15"
E_GRAHAM = f"{EARGLE}#16"
E_BLUFF = f"{EARGLE}#17"     # also Gunsight
E_WAYLAND = f"{EARGLE}#18"   # also Ivan, Thrifty, Speck Mountain
E_BRECK = f"{EARGLE}#19"     # also Parks Mountain, Chaffin, Quinn clay
E_WICHITA = f"{EARGLE}#20"   # also Pueblo formation and its members
E_WALDRIP = f"{EARGLE}#21"   # also Saddle Creek, Coon Mountain

# BEG/GRI/DOE, 1995, Boonsville field secondary gas recovery study.
BOONSVILLE = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery"
B_HABITAT = f"{BOONSVILLE}#8"      # contact behaviour
B_PITFALLS = f"{BOONSVILLE}#10"    # log-correlation pitfalls
B_TRAP = f"{BOONSVILLE}#16"        # structure and compartmentalisation styles
B_TOOLS = f"{BOONSVILLE}#34"       # wireline tool suites by era
B_AREA = f"{BOONSVILLE}#7"         # basin, 26-mi2 study area, prior trapping statement
# #7 names the basin and the 26-mi2 study area but NOT the counties and not the
# field's full name. Appendix B's opening sentence states all four in one place:
# "the 26-mi2 project area in Boonsville (Bend Conglomerate Gas) field in Wise and
# Jack Counties, Texas". The area record's county and field fields cite it.
B_AREA_NAMED = f"{BOONSVILLE}#23"

# Asquith, G., and D. Krygowski, 2004, Basic Well Log Analysis, chapter 7.
ASQUITH = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004"
A_SHALY = f"{ASQUITH}#49"    # shale gates, clay effects on each measurement
A_SW = f"{ASQUITH}#50"       # the saturation methods and their limits
A_CHARTS = f"{ASQUITH}#51"   # carbonate reconnaissance, Hingle grids, K chart
# Chapter 5, not chapter 7: the published limit on the measurement every saturation
# method here consumes. `tool-verification.md` ("Kind corrections") names it as part
# of this tool's payload, so it is carried rather than left to model judgment.
A_RESISTIVITY = f"{ASQUITH}#30"   # laterolog / induction applicability


# --- shared, local, deliberately dumb ----------------------------------------
def _canonical(text: str) -> str:
    """strip -> collapse internal whitespace -> casefold. Nothing else.

    Whitespace and case are presentation; everything else is identity. Kept
    local rather than imported so that no change to another module's matching
    can quietly widen what these tables will answer to.
    """
    return re.sub(r"\s+", " ", text.strip()).casefold()


# =============================================================================
# 61 - geolex_lookup
# =============================================================================

# One trailing rank phrase, removed only for the short-name index. Longest
# first, so "limestone member" wins over "member". Nothing is stripped from the
# stored names themselves.
RANK_SUFFIXES: tuple[str, ...] = (
    "conglomerate and sandstone bed",
    "limestone member", "shale member", "sandstone member", "clay member",
    "limestone lentil", "limestone bed", "shale bed", "sandstone bed", "clay bed",
    "sandstone division",
    "formation", "limestone", "sandstone", "conglomerate",
    "division", "series", "member", "lentil", "group", "shale", "clay", "bed",
    "fm.", "fm",
)

# Every result says when the mapping was done. "1960" is the publication date.
VINTAGE_FLAG = (
    "vintage: Eargle (1960), USGS PP 315-D; field mapping 1950-54, published "
    "1960, reviewing nomenclature published 1890-1960 - verify against current "
    "usage before matching a modern tops database"
)
AREA_FLAG = (
    "area: Brown and Coleman Counties, Texas (Colorado River valley, Bend Arch "
    "outcrop belt); several of the report's recommendations are explicitly "
    "restricted to this area and do not apply in the Brazos River valley"
)
BOUNDS_FLAG = (
    "above/below are the adjacent NAMED units in the source's descending column; "
    "unnamed shale and sandstone intervals lie between many of them, so they are "
    "not necessarily in contact"
)

# Table 1 (#3) printed top-down, with the upper Pueblo members from #20. This
# list is the sole source of `above`/`below`; nothing is ordered by hand.
GEOLEX_MEMBER_COLUMN: tuple[str, ...] = (
    "camp colorado limestone member",
    "salt creek bend shale member",
    "stockwether limestone member",
    "coon mountain sandstone member",
    "camp creek shale member",
    "saddle creek limestone member",
    "waldrip shale member",
    "chaffin limestone member",
    "parks mountain sandstone member",
    "breckenridge limestone member",
    "speck mountain limestone member",
    "ivan limestone member",
    "wayland shale member",
    "gunsight limestone member",
    "bluff creek shale member",
    "home creek limestone member",
    "colony creek shale member",
    "ranger limestone member",
    "placid shale member",
    "upper unnamed limestone member of the winchell limestone",
    "lower unnamed limestone member of the winchell limestone",
    "cedarton shale member",
    "adams branch limestone member",
    "brownwood shale member",
    "capps limestone lentil of plummer and moore (1921)",
    "ricker sandstone member of nickell (1938)",
    "ricker station limestone of cheney (1949)",
)

_UNDESCRIBED = (
    "not described in this report: '#20' states that the Waldrip, Saddle Creek "
    "and locally the Coon Mountain sandstone members are the only members of "
    "the Pueblo formation described here; see Moore (1949, sheet 2)"
)

# Each record's `anchors` maps field -> the segment its wording came from.
GEOLEX_UNITS: dict[str, dict[str, Any]] = {
    # --- groups --------------------------------------------------------------
    "wichita group": {
        "name": "Wichita group", "rank": "group", "system": "Permian",
        "group": None, "formation": None,
        "lithology": "consists of sandstone, shale, and limestone, and in the lower part contains sequences of gray and red shale, sandstone, and coal",
        "type_locality": None,
        "thickness": None,
        "named_by": None,
        "members": ("Pueblo formation",),
        "anchors": {"column": E_TABLE1, "lithology": E_TABLE1, "members": E_WICHITA},
        "flags": ("only the Pueblo formation of this group crops out in the area (#20)",),
    },
    "cisco group": {
        "name": "Cisco group", "rank": "group", "system": "Pennsylvanian",
        "group": None, "formation": None,
        "lithology": "consists of thin beds of limestone, relatively thick beds of shale, and some lenticular beds of sandstone and other channel-fill sedimentary deposits",
        "type_locality": None, "thickness": None, "named_by": "Cummins (1891), as a division",
        "members": ("Thrifty formation", "Graham formation"),
        "anchors": {"column": E_TABLE1, "lithology": E_TABLE1, "members": E_CISCO,
                    "bounds": E_CISCO},
        "bounds_note": "base at the top of the Home Creek limestone; the report places the top of the Thrifty formation at the top of the Chaffin limestone member",
        "flags": (
            "the Pennsylvanian-Permian boundary above this group is unresolved in the "
            "source: 'As the boundary between the Permian and the Pennsylvanian is "
            "obscure and probably gradational, no definite upper boundary between the "
            "two systems has been drawn' (#15)",
        ),
    },
    "canyon group": {
        "name": "Canyon group", "rank": "group", "system": "Pennsylvanian",
        "group": None, "formation": None,
        "lithology": "consists of ridge-forming beds of limestone separated by less-resistant beds of shale and of sandstone that is locally conglomeratic",
        "type_locality": None, "thickness": None, "named_by": "Cummins (1891), as a division; applied in the Colorado River valley by Drake (1893)",
        "members": ("Caddo Creek formation", "Brad formation", "Winchell limestone",
                    "Graford formation"),
        "anchors": {"column": E_TABLE1, "lithology": E_TABLE1, "members": E_CAPPS},
        "flags": (),
    },
    "strawn group": {
        "name": "Strawn group", "rank": "group", "system": "Pennsylvanian",
        "group": None, "formation": None,
        "lithology": "has a prominent ridge-forming limestone at the top but consists chiefly of shale and lenticular beds of sandstone with some conglomerate",
        "type_locality": None,
        "thickness": "Drake's totalled outcrop beds give 4,100 ft, yet 'in wells where there is a complete section of Strawn, no more than 1,200 feet of it has been drilled' (#4)",
        "named_by": "Cummins (1891), as a division",
        "members": ("Capps limestone lentil of Plummer and Moore (1921)",
                    "Ricker sandstone member of Nickell (1938)",
                    "Ricker Station limestone of Cheney (1949)"),
        "bounds_note": "'all rocks in the Colorado River valley between the top of the Smithwick shale of the Bend group and the base of the Brownwood shale member of the Graford formation of the Canyon group'",
        "anchors": {"column": E_TABLE1, "lithology": E_TABLE1, "members": E_TABLE1,
                    "bounds": E_STRAWN, "history": E_STRAWN_HIST},
        "history": (
            "first called the Richland sandstone division by Tarr (1890, p. 204), and the correlative Brazos River valley beds the Richland-Gordon sandstones by Dumble (1890, pl. 3) (#4)",
            "Table 1 leaves the group undifferentiated in this area (#3)",
        ),
        "flags": ("only the upper part of the group crops out in the area (#5)",),
        "aliases": ("strawn",),
    },

    # --- Permian: Wichita group / Pueblo formation ---------------------------
    "pueblo formation": {
        "name": "Pueblo formation", "rank": "formation", "system": "Permian",
        "group": "Wichita group", "formation": None,
        "lithology": None, "type_locality": None,
        "thickness": "thins northward along the outcrop from about 200 ft along the Colorado River in southern Coleman County to about 115 ft in northwestern Brown County",
        "named_by": "nomenclature of Moore (1949), except for the addition of the Coon Mountain sandstone member",
        "members": ("Camp Colorado limestone member", "Salt Creek Bend shale member",
                    "Stockwether limestone member", "Coon Mountain sandstone member",
                    "Camp Creek shale member", "Saddle Creek limestone member",
                    "Waldrip shale member"),
        "bounds_note": "base 'defined by Moore (1949, sheet 2) as an obscure disconformity that separates the Permian from the Pennsylvanian'; for practical purposes the report draws the boundary at the base of the Waldrip shale member",
        "anchors": {"column": E_TABLE1, "members": E_WICHITA, "thickness": E_WICHITA,
                    "bounds": E_WICHITA, "named_by": E_WICHITA},
        "flags": ("Table 1 (#3) lists only the lower part of this formation; the full "
                  "member list is from #20",),
    },
    "camp colorado limestone member": {
        "name": "Camp Colorado limestone member", "rank": "member", "system": "Permian",
        "group": "Wichita group", "formation": "Pueblo formation",
        "lithology": None, "type_locality": None, "thickness": None,
        "named_by": "named and described as a bed by Drake (1893, p. 39)",
        "anchors": {"column": E_WICHITA, "named_by": E_WICHITA},
        "flags": (_UNDESCRIBED,),
    },
    "salt creek bend shale member": {
        "name": "Salt Creek Bend shale member", "rank": "member", "system": "Permian",
        "group": "Wichita group", "formation": "Pueblo formation",
        "lithology": None, "type_locality": None, "thickness": None,
        "named_by": "Drake's Bed 13, named Salt Creek Bend shale by Bullard and Cuyler (1935, p. 249, 250)",
        "anchors": {"column": E_WICHITA, "named_by": E_WICHITA},
        "flags": (_UNDESCRIBED,),
    },
    "stockwether limestone member": {
        "name": "Stockwether limestone member", "rank": "member", "system": "Permian",
        "group": "Wichita group", "formation": "Pueblo formation",
        "lithology": None, "type_locality": None, "thickness": None,
        "named_by": "named and described as a bed by Drake (1893, p. 39)",
        "anchors": {"column": E_WICHITA, "named_by": E_WICHITA},
        "flags": (_UNDESCRIBED,),
    },
    "coon mountain sandstone member": {
        "name": "Coon Mountain sandstone member", "rank": "member", "system": "Permian",
        "group": "Wichita group", "formation": "Pueblo formation",
        "lithology": "chiefly a sandstone and conglomerate deposit which, with finer-grained sediments, fills one or more deep channels; forms a prominent ridge in northwestern Brown and northeastern Coleman Counties",
        "type_locality": "Coon Mountain, locally called The Holloway, in northwestern Brown County",
        "thickness": None,
        "named_by": "Coon Mountain bed of Drake (1893, p. 51); called the Coon Mountain sandstone by Sellards (1933, p. 103) and Nickell (1937, p. 133)",
        "anchors": {"column": E_WICHITA, "lithology": E_WICHITA, "named_by": E_WICHITA,
                    "type_locality": E_WALDRIP},
        "flags": (
            "'The exact relations of the Coon Mountain sandstone member to the beds "
            "surrounding it are only partially known, and the thick body may be a "
            "complex of two or more channels... This member is, therefore, tentatively "
            "placed in the section where Drake placed it' (#21)",
            "Plummer and Moore (1921, p. 172) considered it of Cretaceous age (#21)",
        ),
    },
    "camp creek shale member": {
        "name": "Camp Creek shale member", "rank": "member", "system": "Permian",
        "group": "Wichita group", "formation": "Pueblo formation",
        "lithology": None, "type_locality": None, "thickness": None,
        "named_by": "named and described as a bed by Drake (1893, p. 39)",
        "anchors": {"column": E_WICHITA, "named_by": E_WICHITA},
        "flags": (_UNDESCRIBED,),
    },
    "saddle creek limestone member": {
        "name": "Saddle Creek limestone member", "rank": "member", "system": "Permian",
        "group": "Wichita group", "formation": "Pueblo formation",
        "lithology": "generally dense, very light to medium gray, and only locally fusulinid-bearing; weathers into rounded blocks or slabs and is moderately resistant to weathering",
        "type_locality": None, "thickness": None,
        "named_by": "named and described as a bed by Drake (1893, p. 39)",
        "anchors": {"column": E_TABLE1, "lithology": E_WALDRIP, "named_by": E_WICHITA},
        "flags": ("caps a continuous high cuesta west of the Waldrip lowland; extensively "
                  "removed by channel erosion in northern Brown County (#21)",),
    },
    "waldrip shale member": {
        "name": "Waldrip shale member", "rank": "member", "system": "Permian",
        "group": "Wichita group", "formation": "Pueblo formation",
        "lithology": "Drake: 'principally of blue clay, sandstone, coal, carbonaceous shale, and limestone'; most shale in the lower part is gray, the shale in the upper part red and variegated, with hematite nodules and several coal beds low in the member",
        "type_locality": None,
        "thickness": "Nickell (1938) found Drake's Waldrip beds 238 ft thick; the interval from the Chaffin limestone member up to Drake's No. 1 limestone is 85.2 ft (Bullard and Cuyler, 1935)",
        "named_by": "Waldrip bed of Drake (1893, p. 47-50)",
        "bounds_note": "'The Waldrip lies between the top of the Chaffin limestone member of the Thrifty formation, and the base of the Saddle Creek limestone member of the Pueblo formation'",
        "anchors": {"column": E_TABLE1, "lithology": E_WALDRIP, "thickness": E_WALDRIP,
                    "named_by": E_WALDRIP, "bounds": E_WALDRIP},
        "flags": (
            "the report draws the practical Permian-Pennsylvanian boundary at the base "
            "of this member, while stating that no traceable horizon was found: "
            "Moore (1949) placed it 40 to 55 ft below the top, between Drake's "
            "limestones 1 and 2 (#20, #21)",
        ),
    },

    # --- Cisco group / Thrifty formation -------------------------------------
    "thrifty formation": {
        "name": "Thrifty formation", "rank": "formation", "system": "Pennsylvanian",
        "group": "Cisco group", "formation": None,
        "lithology": "two persistent beds of limestone, another less persistent bed of limestone, and a lenticular channel-fill sandstone, with relatively nonresistant sandstone and shale between them",
        "type_locality": "named for the small village of Thrifty in northwestern Brown County",
        "thickness": "about 55 ft along the Colorado River in southern Coleman County; about 100 ft average in northern Brown County",
        "named_by": "Plummer and Moore (1921, p. 152, 153)",
        "members": ("Chaffin limestone member", "Parks Mountain sandstone member",
                    "Breckenridge limestone member", "Speck Mountain limestone member"),
        "bounds_note": "'lie between the base of the Speck Mountain limestone member and the top of the Chaffin limestone member, the uppermost persistent limestone of Pennsylvanian age as determined by fusulinids'",
        "anchors": {"column": E_TABLE1, "lithology": E_WAYLAND, "members": E_WAYLAND,
                    "type_locality": E_WAYLAND, "thickness": E_WAYLAND,
                    "named_by": E_WAYLAND, "bounds": E_WAYLAND},
        "flags": ("redefined by this report 'to facilitate mapping in the Colorado River "
                  "valley'; earlier usages differ (pl. 27) (#18)",),
    },
    "chaffin limestone member": {
        "name": "Chaffin limestone member", "rank": "member", "system": "Pennsylvanian",
        "group": "Cisco group", "formation": "Thrifty formation",
        "lithology": "a slabby irregularly bedded gray limestone, stained purplish red in large spots, with abundant fusulinids and thin wavy structures of clear calcite; thinner, massive and generally darker gray northward",
        "type_locality": "the now abandoned Chaffin mines about a quarter of a mile southwest of Chaffin crossing on the Colorado River, 1.5 miles east of Waldrip, McCulloch County",
        "thickness": "about 15 ft at the Chaffin mines to about 7 ft south of the Colorado River; averages only 1 to 2 ft in Brown County",
        "named_by": "Chaffin beds of Drake (1893)",
        "anchors": {"column": E_TABLE1, "lithology": E_BRECK, "type_locality": E_BRECK,
                    "thickness": E_BRECK, "named_by": E_BRECK},
        "history": (
            "the persistent upper part has been called the Breckenridge limestone (Plummer and Moore, 1921; Bullard and Cuyler, 1935), the Upper Crystal Falls limestone (Hudnall and Pirtle, 1929, 1931), the Chaffin limestone (Sellards, 1933; Nickell, 1938; Cheney and Eargle, 1951b) and the Crystal Falls limestone (Cheney, 1950) (#19)",
            "Drake's LOWER Chaffin limestone is a different bed: it is here correlated with the Breckenridge limestone member (#19)",
        ),
        "flags": ("homonym: 'Chaffin' alone does not distinguish this member from Drake's "
                  "lower Chaffin limestone, which is the Breckenridge limestone member (#19)",),
    },
    "parks mountain sandstone member": {
        "name": "Parks Mountain sandstone member", "rank": "member",
        "system": "Pennsylvanian", "group": "Cisco group", "formation": "Thrifty formation",
        "lithology": "conglomeratic channel-fill sandstone grading laterally into a thin-bedded sandstone of wide extent; overlain by carbonaceous shale and coal near the Colorado River and by ferruginous red shale farther north",
        "type_locality": "Parks Mountain, north of the Colorado River in southeastern Coleman County",
        "thickness": "at least 60 ft where it is a channel-fill deposit; a few feet to 30 ft or more as thin-bedded sandstone to the north",
        "named_by": "Parks Mountain conglomerate and sandstone bed of Drake (1893, p. 45)",
        "anchors": {"column": E_TABLE1, "lithology": E_BRECK, "type_locality": E_BRECK,
                    "thickness": E_BRECK, "named_by": E_BRECK},
        "history": (
            "termed the Avis sandstone by Bullard and Cuyler (1935, p. 232, 233); the report rejects that: 'the name Avis of Bullard and Cuyler (1935) can not be correctly applied to the stratigraphically higher Parks Mountain sandstone member' (#19)",
        ),
        "flags": (),
    },
    "breckenridge limestone member": {
        "name": "Breckenridge limestone member", "rank": "member",
        "system": "Pennsylvanian", "group": "Cisco group", "formation": "Thrifty formation",
        "lithology": "characteristically pale greenish gray to almost white, blotched with pale reddish purple; generally a nodular bed a foot or two thick, thickening to about 3 ft in northern Brown County",
        "type_locality": "a gray massive resistant limestone forming a prominent escarpment in and about Breckenridge, the county seat of Stephens County",
        "thickness": "3 or 4 ft at the type locality; about 1 to 2 ft in this area, to about 3 ft in northern Brown County",
        "named_by": "Plummer and Moore (1921, p. 155)",
        "bounds_note": "'20 to 40 feet above the Speck Mountain limestone member'",
        "anchors": {"column": E_TABLE1, "lithology": E_BRECK, "type_locality": E_BRECK,
                    "thickness": E_BRECK, "named_by": E_BRECK, "bounds": E_BRECK},
        "history": (
            "correlative with the bed Drake considered the lower Chaffin limestone (#19)",
            "shown on the geologic map of Coleman County (Hudnall and Pirtle, 1929) as the Lower Crystal Falls limestone (#19)",
        ),
        "flags": ("'has not been recognized south of the Colorado River'; between Home "
                  "Creek and the river it is removed by channel erosion and the channel "
                  "filled by the Parks Mountain sandstone member (#19)",),
    },
    "speck mountain limestone member": {
        "name": "Speck Mountain limestone member", "rank": "member",
        "system": "Pennsylvanian", "group": "Cisco group", "formation": "Thrifty formation",
        "lithology": "a firm massive dark-gray limestone that breaks along vertical joints, forming blocks that creep down the scarp of the cuesta it forms; contains Foraminifera and abundant minute algal(?) structures",
        "type_locality": "Speck Mountain, a mesa capped with the limestone member in southern Coleman County about a mile north of the Home Creek crossing of the Whon-Santa Anna road",
        "thickness": "ranges from 1 to 3 ft",
        "named_by": "Drake (1893, p. 39)",
        "anchors": {"column": E_TABLE1, "lithology": E_WAYLAND, "type_locality": E_WAYLAND,
                    "thickness": E_WAYLAND, "named_by": E_WAYLAND},
        "history": (
            "called the Breckenridge limestone by Hudnall and Pirtle (1929, 1931), but the Speck Mountain limestone member by most other authors (#18)",
            "correlated with Plummer and Moore's (1921) Blach Ranch limestone of the Brazos River valley by Cheney (1948, 1949, 1950) (#18)",
        ),
        "flags": ("homonym: distinct from Drake's Speck Mountain CLAY bed, which is the "
                  "shale overlying the Ivan limestone member (#18)",),
    },

    # --- Cisco group / Graham formation --------------------------------------
    "graham formation": {
        "name": "Graham formation", "rank": "formation", "system": "Pennsylvanian",
        "group": "Cisco group", "formation": None,
        "lithology": None,
        "type_locality": "named for the county seat of Young County in the Brazos River valley",
        "thickness": "about 265 ft in southeastern Coleman County and about 290 ft in northern Brown County",
        "named_by": "Plummer and Moore (1921, p. 125)",
        "members": ("Ivan limestone member", "Wayland shale member",
                    "Gunsight limestone member", "Bluff Creek shale member"),
        "bounds_note": "the report recommends the base of the Speck Mountain limestone member of the Thrifty formation as the Graham-Thrifty boundary, in place of the base of the Avis sandstone member, which is not mappable in the Colorado River valley",
        "anchors": {"column": E_TABLE1, "members": E_CISCO, "type_locality": E_GRAHAM,
                    "thickness": E_GRAHAM, "named_by": E_GRAHAM, "bounds": E_GRAHAM},
        "flags": (),
    },
    "ivan limestone member": {
        "name": "Ivan limestone member", "rank": "member", "system": "Pennsylvanian",
        "group": "Cisco group", "formation": "Graham formation",
        "lithology": "in southeastern Coleman County a massive oolitic and algal(?) limestone, medium gray, about 8 ft thick; changes to calcareous sandstone and/or shale within short distances",
        "type_locality": "Stephens County, in the Brazos River valley",
        "thickness": "as much as 18 ft locally, but much thinner within short distances and locally removed by channel erosion",
        "named_by": "Ivan limestone of Cheney and Eargle (1951a, 1951b); recommended for this area by this report",
        "anchors": {"column": E_TABLE1, "lithology": E_WAYLAND, "type_locality": E_WAYLAND,
                    "thickness": E_WAYLAND, "named_by": E_WAYLAND},
        "history": (
            "described as the Bellerophon bed by earlier authors (Nickell, 1938, p. 123, 124); the report rejects that name because 'the name of a characteristic fossil found in a member does not constitute a satisfactory name for a member' (#18)",
        ),
        "flags": ("'it cannot be continuously traced from the Brazos River valley to the "
                  "Colorado River valley' (#18)",),
    },
    "wayland shale member": {
        "name": "Wayland shale member", "rank": "member", "system": "Pennsylvanian",
        "group": "Cisco group", "formation": "Graham formation",
        "lithology": "chiefly gray, commonly silty to sandy near the top, containing abundant sideritic platy concretions; locally red near sandstone channel deposits",
        "type_locality": "Wayland shale of Stephens County (Plummer and Moore, 1921), brought into the Colorado River valley",
        "thickness": "about 100 ft along the Colorado River, about 75 ft near Pecan Bayou, about 105 ft in northern Brown County",
        "named_by": "Plummer and Moore (1921, p. 138)",
        "anchors": {"column": E_TABLE1, "lithology": E_WAYLAND, "type_locality": E_WAYLAND,
                    "thickness": E_WAYLAND, "named_by": E_WAYLAND},
        "history": (
            "part of the unit was termed the Trickham bed by Drake (1893, p. 39-42); 'Although the term \"Trickham\" has priority, retention of the name Wayland shale member is recommended on the basis of this usage' (#18)",
        ),
        "flags": (),
    },
    "gunsight limestone member": {
        "name": "Gunsight limestone member", "rank": "member", "system": "Pennsylvanian",
        "group": "Cisco group", "formation": "Graham formation",
        "lithology": "generally fine grained and pale brownish yellow to gray; the upper bed commonly contains clear crystalline wavy structures believed to be of algal origin",
        "type_locality": None,
        "thickness": "about 17 ft along the Colorado River to 25 ft in north-central Brown County; as thin as 13 ft toward northern Brown County",
        "named_by": "Gunsight limestone of Plummer (1919)",
        "anchors": {"column": E_TABLE1, "lithology": E_BLUFF, "thickness": E_BLUFF,
                    "named_by": E_BLUFF},
        "history": (
            "called the Campophyllum bed by Drake (1893, p. 38, 39) (#17)",
            "divided into Upper and Lower Gunsight limestones by Hudnall and Pirtle (1931) and again by Cheney and Eargle (1951b); Stafford (1960) and Terriere (1960) showed the Upper Gunsight as mapped by Cheney and Eargle to be discontinuous north of Pecan Bayou (#17)",
        ),
        "flags": (),
    },
    "bluff creek shale member": {
        "name": "Bluff Creek shale member", "rank": "member", "system": "Pennsylvanian",
        "group": "Cisco group", "formation": "Graham formation",
        "lithology": "a gray marine shale; locally the basal 10 to 30 ft is red shale, generally near channels; contains as many as six thin, mostly discontinuous limestone units in its lower part",
        "type_locality": "exposures along a tributary of the Colorado River in northeastern McCulloch County",
        "thickness": "about 90 ft along the Colorado River to about 140 ft in north-central Brown County",
        "named_by": "Bluff Creek bed of Drake (1893, p. 37, 38); Bluff Creek shale of Plummer and Moore (1921, p. 137)",
        "anchors": {"column": E_TABLE1, "lithology": E_BLUFF, "type_locality": E_BLUFF,
                    "thickness": E_BLUFF, "named_by": E_BLUFF},
        "history": (
            "Bullard and Cuyler (1935) split it into Upper and Lower Bluff Creek shale about their Bunger limestone, and named the White Ranch limestone within the lower part (#17)",
            "the report does not recommend formal use of the Bunger, North Leon, Gonzales or White Ranch bed names in the Colorado River valley 'until more definite correlations can be established' (#17)",
        ),
        "flags": ("channel-fill sandstones near the base are 'reported to be the so-called "
                  "Overall oil sand as recognized by petroleum geologists in the Overall "
                  "oil field in Coleman County' (#16)",),
    },

    # --- Canyon group / Caddo Creek formation --------------------------------
    "caddo creek formation": {
        "name": "Caddo Creek formation", "rank": "formation", "system": "Pennsylvanian",
        "group": "Canyon group", "formation": None,
        "lithology": None,
        "type_locality": "strata exposed in a creek in the Brazos River valley",
        "thickness": "about 55 ft along the Colorado River to about 75 ft in central Brown County; about 115 ft from well logs in northern Brown County",
        "named_by": "Plummer and Moore (1921, p. 117-118)",
        "members": ("Home Creek limestone member", "Colony Creek shale member"),
        "anchors": {"column": E_TABLE1, "members": E_CADDO, "type_locality": E_CADDO,
                    "thickness": E_CADDO, "named_by": E_CADDO},
        "history": (
            "'As originally defined, it included Drake's Hog Creek shale below and the Home Creek limestone member above... Because of miscorrelations in the past, the name Hog Creek shale member should be replaced. As redefined here, the formation includes, in descending order, the Home Creek limestone member and the Colony Creek shale member.' (#14)",
        ),
        "flags": (),
    },
    "home creek limestone member": {
        "name": "Home Creek limestone member", "rank": "member",
        "system": "Pennsylvanian", "group": "Canyon group", "formation": "Caddo Creek formation",
        "lithology": "ranges from a light-gray cherty vugular solid limestone to nodular irregularly bedded limestone containing partings of shale; fossils generally scarce",
        "type_locality": "southeastern corner of Coleman County",
        "thickness": "averages about 30 ft in southern Brown County, estimated to exceed 50 ft along the Colorado River, 10 to 15 ft in northern Brown County",
        "named_by": "Home Creek bed of Drake (1893); applied to the prominent limestone at the top of the Canyon group by Plummer and Moore (1921, p. 118-121)",
        "anchors": {"column": E_TABLE1, "lithology": E_CADDO, "type_locality": E_CADDO,
                    "thickness": E_CADDO, "named_by": E_CADDO},
        "history": (
            "Nickell (1938, p. 116-118) found that the limestone called Home Creek by most geologists correlated with one higher on the slope than the bed Drake named at the type locality; 'Drake's Home Creek limestone, he found, was the one that Plummer and Moore had subsequently named the Ranger' (#14)",
        ),
        "flags": ("the top of this member is the base of the Cisco group (#15)",),
    },
    "colony creek shale member": {
        "name": "Colony Creek shale member", "rank": "member", "system": "Pennsylvanian",
        "group": "Canyon group", "formation": "Caddo Creek formation",
        "lithology": "a gray shale that contains a generally conspicuous fine-grained thinly to thickly and irregularly bedded sandstone near its top; greenish-gray shale generally underlies the Home Creek limestone member",
        "type_locality": "a stream in Eastland County between the towns of Ranger and Eastland",
        "thickness": "about 25 ft in the south, locally absent; averages about 60 ft in north-central Brown County; 75 to 80 ft in the subsurface northeast",
        "named_by": "Cheney (1948, p. 20); adopted here in place of 'Hog Creek'",
        "anchors": {"column": E_TABLE1, "lithology": E_CADDO, "type_locality": E_CADDO,
                    "thickness": E_CADDO, "named_by": E_CADDO},
        "flags": (),
    },

    # --- Canyon group / Brad formation ---------------------------------------
    "brad formation": {
        "name": "Brad formation", "rank": "formation", "system": "Pennsylvanian",
        "group": "Canyon group", "formation": None,
        "lithology": None,
        "type_locality": "a locality in southwestern Palo Pinto County",
        "thickness": "about 130 ft in southwestern Brown County; about 105 ft in central Brown County",
        "named_by": "Plummer and Moore (1921, p. 107-109)",
        "members": ("Ranger limestone member", "Placid shale member"),
        "anchors": {"column": E_TABLE1, "members": E_WINCHELL_MBRS,
                    "type_locality": E_WINCHELL_MBRS, "thickness": E_WINCHELL_MBRS,
                    "named_by": E_WINCHELL_MBRS},
        "history": (
            "as originally defined it also included the Clear Creek limestone and the Cedarton shale member; Sellards assigned those to the Graford formation (#10)",
        ),
        "flags": (),
    },
    "ranger limestone member": {
        "name": "Ranger limestone member", "rank": "member", "system": "Pennsylvanian",
        "group": "Canyon group", "formation": "Brad formation",
        "lithology": "normally about 12 to 20 ft thick, fine grained, gray to pale yellowish brown; locally contains fusulinids and brachiopods; a limestone complex at least 35 ft thick in southwestern Brown County",
        "type_locality": "named for the town of Ranger in Eastland County",
        "thickness": "about 12 to 20 ft; at least 35 ft where it becomes a limestone complex",
        "named_by": "Plummer and Moore (1921, p. 111), to replace Drake's term Cherty limestone",
        "anchors": {"column": E_TABLE1, "lithology": E_WINCHELL_MBRS,
                    "type_locality": E_WINCHELL_MBRS, "thickness": E_WINCHELL_MBRS,
                    "named_by": E_WINCHELL_MBRS},
        "flags": ("the identity of the cherty limestone at the Home Creek type locality is "
                  "disputed in the source: Cheney read it as the Ranger, Jenkins placed the "
                  "cherty limestone above his Corn Creek member of the Placid shale (#10)",),
    },
    "placid shale member": {
        "name": "Placid shale member", "rank": "member", "system": "Pennsylvanian",
        "group": "Canyon group", "formation": "Brad formation",
        "lithology": "red shale and sandstone, in places conglomerate, occupy the position of Jenkins's Corn Creek limestone northward through Brown County",
        "type_locality": "a town in northeastern McCulloch County",
        "thickness": "120 to 145 ft along the Colorado River to about 95 ft in the central and north-central parts of Brown County",
        "named_by": "Plummer and Moore (1921, p. 110)",
        "anchors": {"column": E_TABLE1, "lithology": E_WINCHELL_MBRS,
                    "type_locality": E_WINCHELL_MBRS, "thickness": E_WINCHELL_MBRS,
                    "named_by": E_WINCHELL_MBRS},
        "history": (
            "as defined by Plummer and Moore it included Drake's bed 7 and his Cherty limestone bed; Jenkins (1952) treated the Placid as a formation and named the Corn Creek limestone member within it (#10)",
        ),
        "flags": (),
    },

    # --- Canyon group / Winchell limestone -----------------------------------
    "winchell limestone": {
        "name": "Winchell limestone", "rank": "formation", "system": "Pennsylvanian",
        "group": "Canyon group", "formation": None,
        "lithology": "two sequences of resistant limestone beds forming escarpments, separated by less resistant shale; about one-third limestone",
        "type_locality": "the Winchell area, Brown County",
        "thickness": "about 100 feet",
        "named_by": "Winchell member of the Graford formation, Nickell (1938, p. 105); raised to formation rank by this report",
        "members": ("upper unnamed limestone member of the Winchell limestone",
                    "lower unnamed limestone member of the Winchell limestone"),
        "anchors": {"column": E_TABLE1, "lithology": E_BROWNWOOD, "thickness": E_BROWNWOOD,
                    "named_by": E_BROWNWOOD, "members": E_BROWNWOOD},
        "history": (
            "the lowermost rocks were Drake's Clear Creek bed, later the Clear Creek limestone of Plummer and Moore (1921); 'Inasmuch as the name \"Clear Creek\" had been preempted, Sellards (1933) suggested that the term Merriman limestone... be substituted' (#9)",
        ),
        "flags": ("the two limestone sequences 'coalesce into a single limestone downdip, "
                  "making a lithologic unit that is easily recognizable as a strong "
                  "deflection on electric logs' (#9)",),
    },
    "upper unnamed limestone member of the winchell limestone": {
        "name": "upper unnamed limestone member of the Winchell limestone",
        "rank": "member", "system": "Pennsylvanian", "group": "Canyon group",
        "formation": "Winchell limestone",
        "lithology": "two beds of limestone totaling more than 20 ft, separated by a 4- to 10-ft bed of shale that forms a grass-covered slope conspicuous on aerial photographs; the limestone beds generally contain few fossils",
        "type_locality": None,
        "thickness": "more than 20 ft of limestone",
        "named_by": "referred to informally by this report; formally unnamed",
        "anchors": {"column": E_TABLE1, "lithology": E_WINCHELL_MBRS,
                    "thickness": E_WINCHELL_MBRS, "named_by": E_BROWNWOOD},
        "history": (
            "included in the Placid shale by Plummer and Moore (1921) and by Bullard and Cuyler (1935) before Nickell (1938) renamed the two ridge-forming sequences the Winchell member (#10)",
        ),
        "flags": (),
        "aliases": ("upper unnamed limestone member",),
    },
    "lower unnamed limestone member of the winchell limestone": {
        "name": "lower unnamed limestone member of the Winchell limestone",
        "rank": "member", "system": "Pennsylvanian", "group": "Canyon group",
        "formation": "Winchell limestone",
        "lithology": "several limestone beds from 1 to 10 ft thick over calcareous gray shale; the uppermost and thickest bed, called the Clear Creek limestone by Plummer and Moore (1921), is light gray, nodular and irregular in thickness with abundant apparently algal structures",
        "type_locality": None,
        "thickness": "separated from the upper member by 30 to 40 ft of shale and thin sandstone beds",
        "named_by": "referred to informally by this report; formally unnamed",
        "anchors": {"column": E_TABLE1, "lithology": E_WINCHELL_MBRS,
                    "thickness": E_WINCHELL_MBRS, "named_by": E_BROWNWOOD},
        "flags": (),
        "aliases": ("lower unnamed limestone member",),
    },

    # --- Canyon group / Graford formation ------------------------------------
    "graford formation": {
        "name": "Graford formation", "rank": "formation", "system": "Pennsylvanian",
        "group": "Canyon group", "formation": None,
        "lithology": None,
        "type_locality": "a locality in Palo Pinto County",
        "thickness": "about 285 ft in the southern part of Brown County and about 340 ft in the central part of Brown County",
        "named_by": "Plummer and Moore (1921, p. 95); redefined by this report",
        "members": ("Cedarton shale member", "Adams Branch limestone member",
                    "Brownwood shale member"),
        "anchors": {"column": E_TABLE1, "members": E_GRAFORD, "type_locality": E_GRAFORD,
                    "thickness": E_GRAFORD, "named_by": E_GRAFORD},
        "history": (
            "Sellards (1933, p. 111) redefined it to include his Merriman limestone and the Cedarton shale as well as the Adams Branch and Brownwood; Cheney (1940) instead put the Brownwood in a new group he named the Whitt (#8)",
            "this report defines the Winchell as a formation overlying the Graford, leaving the Graford with the Brownwood shale, Adams Branch limestone and Cedarton shale members (#8)",
        ),
        "flags": (),
    },
    "cedarton shale member": {
        "name": "Cedarton shale member", "rank": "member", "system": "Pennsylvanian",
        "group": "Canyon group", "formation": "Graford formation",
        "lithology": "gray shale near the base grading upward into red shale containing thin lenticular sandstone bodies near the top; locally thin argillaceous limestone near the middle",
        "type_locality": None,
        "thickness": "ranges from 60 to 80 ft",
        "named_by": "Cedarton shale of Moore and Plummer (1922)",
        "anchors": {"column": E_TABLE1, "lithology": E_BROWNWOOD, "thickness": E_BROWNWOOD,
                    "named_by": E_GRAFORD},
        "flags": ("a sandstone at this position produces oil in southeastern Callahan "
                  "County and is 'known to petroleum geologists as the Cross Plains sand' "
                  "(Cheney, 1949) (#9)",),
    },
    "adams branch limestone member": {
        "name": "Adams Branch limestone member", "rank": "member",
        "system": "Pennsylvanian", "group": "Canyon group", "formation": "Graford formation",
        "lithology": "a light-gray wavy-bedded slabby limestone that is brittle and easily crushed; a basal 2-ft bed is massive, tough and sandy; grades laterally into shale, calcareous sandstone and coquina northeast of Brownwood",
        "type_locality": "exposures along the head of Adams Branch, west of Brownwood",
        "thickness": "about 15 ft a mile west of Brownwood, thickening to about 40 ft downdip to the west and at least 50 to 60 ft in northeastern McCulloch County",
        "named_by": "Drake (1893)",
        "anchors": {"column": E_TABLE1, "lithology": E_BROWNWOOD,
                    "type_locality": E_BROWNWOOD, "thickness": E_BROWNWOOD,
                    "named_by": E_BROWNWOOD},
        "flags": (),
    },
    "brownwood shale member": {
        "name": "Brownwood shale member", "rank": "member", "system": "Pennsylvanian",
        "group": "Canyon group", "formation": "Graford formation",
        "lithology": "basal gray shale with marine fossils grading upward into red shale containing several beds of impure limestone and beds of sandstone; mostly gray silty shale and lenticular sandstone in the upper half",
        "type_locality": None,
        "thickness": "approximately 225 ft along the Colorado River and about 300 ft in the central part of Brown County",
        "named_by": "Brownwood bed of Drake (1893, p. 28-30); proposed for formal adoption as a member by this report",
        "bounds_note": "'the base of the member be drawn at the top of the Capps limestone lentil of Plummer and Moore (1921)... the top of the Brownwood be drawn at the base of the Adams Branch limestone member'",
        "anchors": {"column": E_TABLE1, "lithology": E_BROWNWOOD,
                    "thickness": E_BROWNWOOD, "named_by": E_BROWNWOOD,
                    "bounds": E_BROWNWOOD},
        "flags": ("'In the subsurface of northern Brown County extensive lenses of "
                  "oil-bearing sandstone at about this stratigraphic position are known "
                  "locally as the Cross Cut sands' (#9)",),
    },

    # --- Strawn group, undifferentiated --------------------------------------
    "capps limestone lentil of plummer and moore (1921)": {
        "name": "Capps limestone lentil of Plummer and Moore (1921)", "rank": "lentil",
        "system": "Pennsylvanian", "group": "Strawn group", "formation": None,
        "lithology": "gray, wavy-bedded to nodular, in some places conglomeratic at its base; abundantly fossiliferous with Fusulina sp., Chaetetes and brachiopods chiefly of the genus Composita",
        "type_locality": "the community of Early encompasses the type locality; named for exposures on the nearby Capps farm",
        "thickness": "about 10 to 30 ft near Brownwood",
        "named_by": "Plummer and Moore (1921)",
        "anchors": {"column": E_TABLE1, "lithology": E_CAPPS, "type_locality": E_CAPPS,
                    "thickness": E_CAPPS, "named_by": E_CAPPS, "history": E_STRAWN_HIST},
        "history": (
            "originally called the Coral limestone bed by Drake because it contains an abundance of Chaetetes (#7)",
            "classified by Sellards (1933) as the Capps limestone member of the Mineral Wells formation, a term this report does not extend into the Colorado River valley (#7)",
            "its top is taken as the top of the Strawn group (#4)",
        ),
        "flags": (),
        "aliases": ("capps limestone lentil", "capps limestone member", "capps limestone",
                    "capps"),
    },
    "ricker sandstone member of nickell (1938)": {
        "name": "Ricker sandstone member of Nickell (1938)", "rank": "member",
        "system": "Pennsylvanian", "group": "Strawn group", "formation": None,
        "lithology": "at the best exposure a 25- to 35-ft brown sandstone containing chert pebbles, irregularly overlying greenish-gray shale and locally occupying channels cut 10 to 12 ft into it",
        "type_locality": "Drake's Ricker bed caps an isolated butte north of Ricker Station, 5.5 miles east of Brownwood; best exposure in a railroad cut 5 miles east of the courthouse at Brownwood",
        "thickness": "25 to 35 ft at the best exposure",
        "named_by": "Nickell (1938, pl. 9), from Drake's Ricker bed",
        "bounds_note": "'separated from the underlying Ricker Station limestone of Cheney (1949) by 50 to 70 feet of interbedded gray shale and sandstone'",
        "anchors": {"column": E_TABLE1, "lithology": E_RICKER, "type_locality": E_RICKER,
                    "thickness": E_RICKER, "named_by": E_RICKER, "bounds": E_RICKER},
        "history": (
            "'Only Drake's name for the upper unit, the Ricker, is in common use today, but that name has been restricted to the prominent sandstone at the base of Drake's Ricker bed' (#4)",
            "Nickell placed it in the Mineral Wells formation of the Strawn group, a term this report does not use in the area (#6)",
        ),
        "flags": ("homonym: 'Ricker' alone does not distinguish this member from Drake's "
                  "Ricker bed or from the Ricker Station limestone of Cheney (1949) (#4, #6)",),
        "aliases": ("ricker sandstone member", "ricker sandstone"),
    },
    "ricker station limestone of cheney (1949)": {
        "name": "Ricker Station limestone of Cheney (1949)", "rank": "informal unit",
        "system": "Pennsylvanian", "group": "Strawn group", "formation": None,
        "lithology": "a 4-ft bed of grayish-brown limestone containing fine-grained sand; fusulinids constitute about half the rock near Ricker siding, with mollusks, crinoid columnals and scattered subrounded chert pebbles",
        "type_locality": "a pasture about one-tenth of a mile south of the road crossing at the Ricker railroad siding, 5.5 miles S. 76 deg E. of the courthouse at Brownwood",
        "thickness": "a thin discontinuous bed, about 4 ft at the best exposure",
        "named_by": "Cheney (1940, as Ricker limestone; 1949, as Ricker Station limestone)",
        "bounds_note": "'the lowermost limestone bed of the Strawn group found to the date of this survey in the Colorado River valley'; about 200 ft below the top of the Strawn in central Brown County",
        "anchors": {"column": E_TABLE1, "lithology": E_RICKER, "type_locality": E_RICKER,
                    "thickness": E_RICKER, "named_by": E_RICKER, "bounds": E_RICKER},
        "history": (
            "Cheney 'called it the Ricker Station limestone apparently to avoid confusion with the Ricker bed described previously by Drake' (#6)",
        ),
        "flags": ("homonym: see the Ricker sandstone member of Nickell (1938) (#6)",),
        # "Ricker limestone" is Cheney's own earlier name for this bed (#6), so it
        # is a sourced alias - and it is what puts this unit into the "ricker"
        # ambiguity bucket, where it belongs.
        "aliases": ("ricker station limestone", "ricker limestone", "ricker station"),
    },

    # --- informal intervals the source names and then discards names for -----
    "shale overlying the ivan limestone member": {
        "name": "shale overlying the Ivan limestone member", "rank": "informal interval",
        "system": "Pennsylvanian", "group": "Cisco group", "formation": "Graham formation",
        "lithology": "chiefly silty or sandy, and red, with locally abundant limonite concretions; lenticular sandstone and conglomerate at the base filling channels that locally cut through the Ivan limestone member",
        "type_locality": None,
        "thickness": "about 45 to 65 ft in southeastern Coleman County to about 25 to 40 ft in northern Brown County",
        "named_by": "unnamed in this report",
        "bounds_note": "overlying the Ivan limestone member and underlying the Speck Mountain limestone member of the Thrifty formation",
        "above": "Speck Mountain limestone member", "below": "Ivan limestone member",
        "anchors": {"lithology": E_WAYLAND, "thickness": E_WAYLAND, "bounds": E_WAYLAND,
                    "history": E_WAYLAND},
        "history": (
            "'was called the Speck Mountain clay bed by Drake (1893, p. 43, 44)' (#18)",
        ),
        "flags": ("a thin coal bed immediately below the Speck Mountain limestone member "
                  "extends over a wide area in northwestern Brown County (#18)",),
    },
    "shale overlying the speck mountain limestone member": {
        "name": "shale overlying the Speck Mountain limestone member",
        "rank": "informal interval", "system": "Pennsylvanian", "group": "Cisco group",
        "formation": "Thrifty formation",
        "lithology": "generally gray with abundant marine fossils, grading upward into red and variegated shale up to the base of the Breckenridge limestone member; south of Home Creek mostly red to gray shale, in places silty and sandy",
        "type_locality": None, "thickness": None,
        "named_by": "unnamed in this report",
        "bounds_note": "overlying the Speck Mountain limestone member and extending up to the Chaffin limestone member",
        "above": "Chaffin limestone member", "below": "Speck Mountain limestone member",
        "anchors": {"lithology": E_WAYLAND, "bounds": E_WAYLAND, "history": E_WAYLAND},
        "history": (
            "Drake named the interval the Lohn bed (1893, p. 44, 45); Sellards (1933) and Nickell (1938) called it the Lohn shale; 'the name Lohn is being discarded as a stratigraphic name for use in eastern Coleman and northwestern Brown Counties' (#18)",
        ),
        "flags": (),
    },
    "clay overlying the breckenridge limestone member": {
        "name": "clay overlying the Breckenridge limestone member",
        "rank": "informal interval", "system": "Pennsylvanian", "group": "Cisco group",
        "formation": "Thrifty formation",
        "lithology": "red clay containing abundant hematite nodules and plant fossils; lenticular sandstone beds particularly near the base, with some channel-fill conglomerate",
        "type_locality": "exposures in Eastland County, where it has been extensively mined (Quinn clay of Plummer and Bradley, 1949)",
        "thickness": None,
        "named_by": "named the Quinn clay by Plummer and Bradley (1949) in a brick-clay study",
        "bounds_note": "'The beds that intervene between the Breckenridge and Chaffin limestone members in Brown County and north of Home Creek in eastern Coleman County'",
        "above": "Chaffin limestone member", "below": "Breckenridge limestone member",
        "anchors": {"lithology": E_BRECK, "named_by": E_BRECK, "bounds": E_BRECK,
                    "type_locality": E_BRECK},
        "flags": ("the conglomerate in this interval 'may perhaps be correlated with the "
                  "Parks Mountain sandstone member... inasmuch as it occupies the same "
                  "stratigraphic interval' (#19)",),
        "aliases": ("quinn clay",),
    },
}

# Superseded names. `current_equivalent` is populated ONLY where the source
# states the replacement or the equivalence in its own words; otherwise it is
# empty and the result says the source states none.
GEOLEX_SUPERSEDED: dict[str, dict[str, Any]] = {
    "hog creek shale member": {
        "name": "Hog Creek shale member", "rank": "member",
        "current_equivalent": ("Colony Creek shale member",),
        "history": (
            "'Because of miscorrelations in the past... the name Hog Creek shale member should be replaced.' (#14)",
            "'Actually the Hog Creek shale of Drake lies above the Home Creek, and because of this confusion, Cheney (1948, p. 20) recommended discarding the term \"Hog Creek\" for the unit underlying the Home Creek and substituting the term \"Colony Creek\" shale.' (#14)",
        ),
        "anchors": {"history": E_CADDO, "current_equivalent": E_CADDO},
        "flags": ("the name was applied to the wrong bed: Drake's Hog Creek shale lies "
                  "ABOVE the Home Creek limestone, not below it (#14)",),
        "aliases": ("hog creek shale", "hog creek"),
    },
    "mineral wells formation": {
        "name": "Mineral Wells formation", "rank": "formation",
        "current_equivalent": ("Strawn group",),
        "history": (
            "'The term \"Strawn group\" is used here for all rocks in the Colorado River valley between the top of the Smithwick shale of the Bend group and the base of the Brownwood shale member of the Graford formation... The term \"Mineral Wells formation\" is not used in this area because of the marked range in thickness and lithology that occurs in the Strawn between the Brazos and Colorado River valleys.' (#5)",
            "Cheney (1940) 'advocated the abandonment of the name Mineral Wells because that formation in the Brazos River valley includes rocks of both Strawn and Canyon ages' (#4)",
        ),
        "anchors": {"history": E_STRAWN, "current_equivalent": E_STRAWN},
        "flags": ("area-restricted: the source declines the name in the Colorado River "
                  "valley; it does not abandon it in the Brazos River valley (#5)",),
        "aliases": ("mineral wells",),
    },
    "palo pinto limestone": {
        "name": "Palo Pinto limestone", "rank": "formation",
        "current_equivalent": ("Brownwood shale member",),
        "history": (
            "'It is here recommended that the name Palo Pinto be abandoned in the Colorado River valley, and that the beds called Palo Pinto with question by Nickell (1938, p. 95) and the shale unit between it and the Capps limestone member be included in the Brownwood shale member, in accordance with general current usage in Texas.' (#8)",
            "Nickell described the questioned bed as 1 ft of yellow dense limestone lying 111 ft above the Capps limestone lentil in the Brownwood area (#9)",
        ),
        "anchors": {"history": E_GRAFORD, "current_equivalent": E_GRAFORD},
        "flags": ("area-restricted to the Colorado River valley (#8)",),
        "aliases": ("palo pinto",),
    },
    "lohn bed": {
        "name": "Lohn bed", "rank": "bed",
        "current_equivalent": ("shale overlying the Speck Mountain limestone member",),
        "history": (
            "Drake named the shale and sandstone above the Speck Mountain limestone member up to the Chaffin limestone member the Lohn bed, for a locality south of the Colorado River in northern McCulloch County (1893, p. 44, 45) (#18)",
            "'His Lohn bed, therefore, includes a thicker stratigraphic interval south of Home Creek than that north of the creek. For that reason the name Lohn is being discarded as a stratigraphic name for use in eastern Coleman and northwestern Brown Counties.' (#18)",
            "'Inasmuch as the term \"Lohn\" did not apply to exactly the same interval north of the river... it is not recommended for use in Coleman and Brown Counties.' (#19)",
        ),
        "anchors": {"history": E_WAYLAND, "current_equivalent": E_WAYLAND,
                    "history_2": E_BRECK},
        "flags": ("the discarded name covered different intervals north and south of Home "
                  "Creek, which is why it was discarded (#18)",),
        "aliases": ("lohn shale", "lohn"),
    },
    "avis sandstone member": {
        "name": "Avis sandstone member", "rank": "member",
        "current_equivalent": (),
        "history": (
            "named the Avis sandstone by Plummer and Moore (1921) in the Brazos River valley, who took its base as the Graham-Thrifty boundary (#18)",
            "'Inasmuch as sandstone is present only locally and the sandstone lenses occupy several stratigraphic positions in the Wayland, the name Avis sandstone member probably should not be brought into the Colorado River valley.' (#18)",
            "Bullard and Cuyler (1935) applied 'Avis' to what this report calls the Parks Mountain sandstone member; 'the Avis of Plummer and Moore (1921), however, has been shown by Lee to have originated before the Ivan limestone member was deposited... and, therefore, the name Avis of Bullard and Cuyler (1935) can not be correctly applied to the stratigraphically higher Parks Mountain sandstone member.' (#19)",
            "'In the Colorado River valley, however, this boundary is not mappable because only discontinuous lenses of sandstone are present at the stratigraphic position of the Avis.' (#16)",
        ),
        "anchors": {"history": E_WAYLAND, "history_2": E_BRECK, "history_3": E_GRAHAM},
        "flags": (
            "the source states no single current equivalent: the name has been used for "
            "lenses in the Wayland shale member AND, by Bullard and Cuyler (1935), for the "
            "stratigraphically higher Parks Mountain sandstone member, which #19 says is "
            "not a correct application",
        ),
        "aliases": ("avis sandstone", "avis"),
    },
    "harpersville formation": {
        "name": "Harpersville formation", "rank": "formation",
        "current_equivalent": ("Waldrip shale member", "Saddle Creek limestone member"),
        "history": (
            "'Their Harpersville formation consisted of Drake's Waldrip and Saddle Creek beds.' (#15)",
            "'Moore (1949) lowered the top of the Cisco to the base of a sandstone in the Waldrip shale member of the Pueblo group, and discontinued the use of the name \"Harpersville formation.\"' (#15)",
            "Bullard and Cuyler called the lower part, from the top of the Chaffin limestone member up, the Lower Harpersville beds (#21)",
        ),
        "anchors": {"history": E_CISCO, "current_equivalent": E_CISCO, "history_2": E_WALDRIP},
        "flags": ("resolves to two units, not one (#15)",),
        "aliases": ("harpersville",),
    },
    "clear creek limestone": {
        "name": "Clear Creek limestone", "rank": "informal unit",
        "current_equivalent": ("lower unnamed limestone member of the Winchell limestone",),
        "history": (
            "described originally as the Clear Creek bed by Drake (1893, p. 31, 32), later the Clear Creek limestone of Plummer and Moore (1921, p. 109, 110) (#9)",
            "'Inasmuch as the name \"Clear Creek\" had been preempted, Sellards (1933) suggested that the term Merriman limestone, a term applied by Reeves (1922, p. 120) to a bed in a similar stratigraphic position in the Brazos River valley, be substituted.' (#9)",
            "'This limestone, which was called the Clear Creek limestone by Plummer and Moore (1921), is light gray, nodular, and irregular in thickness' - the uppermost and generally thickest bed of the lower unnamed limestone member (#10)",
        ),
        "anchors": {"history": E_BROWNWOOD, "current_equivalent": E_WINCHELL_MBRS},
        "flags": ("the Clear Creek is one BED within the lower unnamed limestone member, "
                  "not the whole member (#10)",),
        "aliases": ("clear creek bed", "clear creek"),
    },
    "cherty limestone bed": {
        "name": "Cherty limestone bed of Drake", "rank": "bed",
        "current_equivalent": ("Ranger limestone member",),
        "history": (
            "'The Ranger limestone, named by Plummer and Moore (1921, p. 111) for the town of Ranger in Eastland County to replace Drake's term Cherty limestone' (#10)",
            "Drake applied 'Cherty bed' to the lower massive limestone in the walls of Home Creek; 'The chert-bearing limestone is now included in the Brad formation' (#14)",
        ),
        "anchors": {"history": E_WINCHELL_MBRS, "current_equivalent": E_WINCHELL_MBRS,
                    "history_2": E_CADDO},
        "flags": ("the identity of the cherty limestone at the Home Creek locality is "
                  "disputed within the source itself (#10)",),
        "aliases": ("cherty limestone", "cherty bed"),
    },
    "coral limestone bed": {
        "name": "Coral limestone bed of Drake", "rank": "bed",
        "current_equivalent": ("Capps limestone lentil of Plummer and Moore (1921)",),
        "history": (
            "'The Capps limestone lentil as used by Plummer and Moore (1921), originally called the Coral limestone bed by Drake because it contains an abundance of Chaetetes' (#7)",
            "Drake considered the base of the Canyon to be the top of his Coral limestone bed (#7)",
        ),
        "anchors": {"history": E_CAPPS, "current_equivalent": E_CAPPS},
        "flags": (),
        "aliases": ("coral limestone",),
    },
    "bellerophon bed": {
        "name": "Bellerophon bed", "rank": "bed",
        "current_equivalent": ("Ivan limestone member",),
        "history": (
            "'The name \"Ivan limestone member\" is here recommended for the member that was described as the Bellerophon bed by the earlier authors (Nickell, 1938, p. 123, 124)... As the name of a characteristic fossil found in a member does not constitute a satisfactory name for a member... the extension to this area of the name Ivan limestone member is recommended' (#18)",
        ),
        "anchors": {"history": E_WAYLAND, "current_equivalent": E_WAYLAND},
        "flags": (),
        "aliases": ("bellerophon limestone", "bellerophon"),
    },
    "campophyllum bed": {
        "name": "Campophyllum bed", "rank": "bed",
        "current_equivalent": ("Gunsight limestone member",),
        "history": (
            "'This member, called the Campophyllum bed by Drake (1893, p. 38, 39) and the Gunsight limestone by Plummer (1919)' (#17)",
            "Drake considered the top of the Canyon to be his Campophyllum bed (#7)",
        ),
        "anchors": {"history": E_BLUFF, "current_equivalent": E_BLUFF, "history_2": E_CAPPS},
        "flags": (),
        "aliases": ("campophyllum",),
    },
    "trickham bed": {
        "name": "Trickham bed", "rank": "bed",
        "current_equivalent": ("Wayland shale member",),
        "history": (
            "'The thick shale that forms broad lowlands above the Gunsight limestone member, part of which was termed the Trickham bed by Drake (1893, p. 39-42), was first correlated by Plummer and Moore (1921, p. 138) with their Wayland shale of Stephens County.' (#18)",
            "'Although the term \"Trickham\" has priority, retention of the name Wayland shale member is recommended on the basis of this usage, and on the similarity in lithologic character, fossil content, and thickness to the Wayland of the Brazos River valley.' (#18)",
        ),
        "anchors": {"history": E_WAYLAND, "current_equivalent": E_WAYLAND},
        "flags": ("partial: the source says the Trickham bed was PART of the shale now "
                  "called the Wayland shale member, not the whole of it (#18)",),
        "aliases": ("trickham",),
    },
    "upper crystal falls limestone": {
        "name": "Upper Crystal Falls limestone", "rank": "informal unit",
        "current_equivalent": ("Chaffin limestone member",),
        "history": (
            "'The generally persistent upper part of the Chaffin limestone member has been variously called... the Upper Crystal Falls limestone by Hudnall and Pirtle (1929, 1931)... and the Crystal Falls limestone by Cheney (1950, table following p. 11)' (#19)",
        ),
        "anchors": {"history": E_BRECK, "current_equivalent": E_BRECK},
        "flags": (),
        "aliases": ("crystal falls limestone", "crystal falls"),
    },
    "lower crystal falls limestone": {
        "name": "Lower Crystal Falls limestone", "rank": "informal unit",
        "current_equivalent": ("Breckenridge limestone member",),
        "history": (
            "'The bed here correlated with the Breckenridge is shown on the geologic map of Coleman County (Hudnall and Pirtle, 1929) as the Lower Crystal Falls limestone.' (#19)",
        ),
        "anchors": {"history": E_BRECK, "current_equivalent": E_BRECK},
        "flags": (),
    },
    "lower chaffin limestone of drake": {
        "name": "lower Chaffin limestone of Drake", "rank": "bed",
        "current_equivalent": ("Breckenridge limestone member",),
        "history": (
            "'During the preparation of this report, the Breckenridge limestone member was mapped as far southwest as Home Creek, and was found to be correlative with the bed Drake considered the lower Chaffin limestone.' (#19)",
            "'In the present survey, however, Drake's lower Chaffin was found to be the Breckenridge limestone member' (#18)",
        ),
        "anchors": {"history": E_BRECK, "current_equivalent": E_BRECK, "history_2": E_WAYLAND},
        "flags": ("homonym trap: the (upper) Chaffin limestone member is a different bed "
                  "(#19)",),
        "aliases": ("lower chaffin limestone", "lower chaffin"),
    },
    "ricker bed of drake": {
        "name": "Ricker bed of Drake", "rank": "bed",
        "current_equivalent": ("Ricker sandstone member of Nickell (1938)",),
        "history": (
            "Drake (1893) placed the Ricker bed at the top of his Strawn division; 'Only Drake's name for the upper unit, the Ricker, is in common use today, but that name has been restricted to the prominent sandstone at the base of Drake's Ricker bed.' (#4)",
            "'Drake (1893) stated that the sandstone and conglomerate of his Ricker bed caps an isolated butte north of Ricker Station, 5.5 miles east of Brownwood.' (#6)",
        ),
        "anchors": {"history": E_STRAWN_HIST, "current_equivalent": E_STRAWN_HIST,
                    "history_2": E_RICKER},
        "flags": ("restricted, not renamed: current usage keeps 'Ricker' only for the "
                  "prominent sandstone at the BASE of Drake's bed, which is Nickell's "
                  "Ricker sandstone member (#4)",),
        "aliases": ("ricker bed",),
    },
    "richland sandstone division": {
        "name": "Richland sandstone division", "rank": "division",
        "current_equivalent": ("Strawn group",),
        "history": (
            "'The sandstone and shale beds that constitute the Strawn group in the Colorado River valley were first called the Richland sandstone division by Tarr (1890, p. 204).' (#4)",
        ),
        "anchors": {"history": E_STRAWN_HIST, "current_equivalent": E_STRAWN_HIST},
        "flags": (),
        "aliases": ("richland sandstone", "richland"),
    },
    "richland-gordon sandstones": {
        "name": "Richland-Gordon sandstones", "rank": "informal unit",
        "current_equivalent": ("Strawn group",),
        "history": (
            "'These and correlative beds in the Brazos River valley were called the Richland-Gordon sandstones by Dumble (1890, pl. 3).' (#4)",
        ),
        "anchors": {"history": E_STRAWN_HIST, "current_equivalent": E_STRAWN_HIST},
        "flags": ("named in the Brazos River valley, not the Colorado River valley (#4)",),
        "aliases": ("richland-gordon sandstone", "richland gordon sandstones"),
    },
    "milburn shales": {
        "name": "Milburn shales", "rank": "informal unit",
        "current_equivalent": ("Brownwood shale member",),
        "history": (
            "'Hill (1901, p. 98) and Gordon (1911, p. 117) used the name \"Brownwood division\" to include also all of the Milburn division of Tarr, approximately equivalent to the present Brownwood shale member.' (#9)",
            "the Canyon group 'includes most of the rocks assigned to the Milburn shales and the Brownwood division by Tarr (1890)' (#7)",
        ),
        "anchors": {"history": E_BROWNWOOD, "current_equivalent": E_BROWNWOOD,
                    "history_2": E_CAPPS},
        "flags": ("the source says 'approximately equivalent', not equivalent (#9)",),
        "aliases": ("milburn shale", "milburn division", "milburn"),
    },
    "whitt group": {
        "name": "Whitt group", "rank": "group",
        "current_equivalent": (),
        "history": (
            "'Cheney (1940, 1945, 1948, 1949, 1950) considered the Brownwood to be the one and only formation of a new group, which he named the Whitt.' (#8)",
            "'Cheney and Eargle (1951b) defined the Whitt of Cheney (1940) to include the Adams Branch and the Brownwood units whereas the Graford included only the Winchell limestone and Cedarton shale.' (#8)",
            "this report instead places the Brownwood shale, Adams Branch limestone and Cedarton shale members in the Graford formation, with the Winchell limestone as a separate overlying formation (#8)",
        ),
        "anchors": {"history": E_GRAFORD},
        "flags": ("the source states no single current equivalent: the two published "
                  "definitions of the Whitt cover different units (#8)",),
        "aliases": ("whitt",),
    },
    "obregon formation": {
        "name": "Obregon formation", "rank": "formation",
        "current_equivalent": (),
        "history": (
            "Cheney (1940, p. 91) placed the top of his Cisco series at an unconformity in the Harpersville formation; 'The beds underlying this systemic boundary and overlying his Chaffin formation he termed the Obregon formation.' (#21)",
            "'No traceable horizon was found during this survey which could be considered the boundary between the Permian and Pennsylvanian. The whole interval that Drake called the Waldrip beds is, therefore, for purposes of mapping and description, considered the Waldrip shale member of the Pueblo formation.' (#21)",
        ),
        "anchors": {"history": E_WALDRIP},
        "flags": ("the source states no current equivalent: it declines Cheney's boundary "
                  "and does not map his unit (#21)",),
        "aliases": ("obregon",),
    },
    "speck mountain clay bed": {
        "name": "Speck Mountain clay bed", "rank": "bed",
        "current_equivalent": ("shale overlying the Ivan limestone member",),
        "history": (
            "'The shale overlying the Ivan limestone member and underlying the Speck Mountain limestone member of the Thrifty formation was called the Speck Mountain clay bed by Drake (1893, p. 43, 44), and was discussed as a separate shale member by Nickell (1938, p. 123, 124).' (#18)",
        ),
        "anchors": {"history": E_WAYLAND, "current_equivalent": E_WAYLAND},
        "flags": ("homonym trap: this is NOT the Speck Mountain limestone member, which "
                  "overlies it (#18)",),
    },
}


def _short_name(canon: str) -> str:
    """Canonical name with at most one trailing rank phrase removed."""
    for suffix in RANK_SUFFIXES:
        if canon.endswith(" " + suffix):
            return canon[: -(len(suffix) + 1)].strip()
    return canon


def _build_geolex_indexes() -> tuple[dict[str, tuple[str, str]], dict[str, list[str]]]:
    """(exact index, short-name index). Both derived from the tables, never hand-kept."""
    exact: dict[str, tuple[str, str]] = {}   # canonical string -> (table, key)
    short: dict[str, list[str]] = {}

    def register(table: str, key: str, record: dict[str, Any]) -> None:
        names = [key, _canonical(record["name"])]
        names.extend(_canonical(a) for a in record.get("aliases", ()))
        for n in names:
            exact.setdefault(n, (table, key))
        for n in names:
            s = _short_name(n)
            bucket = short.setdefault(s, [])
            if key not in bucket:
                bucket.append(key)

    for key, rec in GEOLEX_UNITS.items():
        register("unit", key, rec)
    for key, rec in GEOLEX_SUPERSEDED.items():
        register("superseded", key, rec)
    return exact, short


_GEOLEX_EXACT, _GEOLEX_SHORT = _build_geolex_indexes()


def _column_neighbours(key: str) -> tuple[str | None, str | None]:
    """(above, below) as printed in the source's descending column."""
    if key not in GEOLEX_MEMBER_COLUMN:
        return None, None
    i = GEOLEX_MEMBER_COLUMN.index(key)
    above = GEOLEX_MEMBER_COLUMN[i - 1] if i > 0 else None
    below = GEOLEX_MEMBER_COLUMN[i + 1] if i + 1 < len(GEOLEX_MEMBER_COLUMN) else None
    pretty = lambda k: GEOLEX_UNITS[k]["name"] if k else None  # noqa: E731
    return pretty(above), pretty(below)


def _geolex_record(table: str, key: str) -> dict[str, Any]:
    """Materialise one record, with bounding units derived from the column."""
    if table == "superseded":
        rec = dict(GEOLEX_SUPERSEDED[key])
        rec.setdefault("system", None)
        rec.setdefault("group", None)
        rec.setdefault("formation", None)
        rec.setdefault("lithology", None)
        rec.setdefault("type_locality", None)
        rec.setdefault("thickness", None)
        rec.setdefault("named_by", None)
        rec["status"] = "superseded"
        rec["above"] = None
        rec["below"] = None
        rec.pop("aliases", None)
        return rec

    rec = dict(GEOLEX_UNITS[key])
    rec["status"] = "current"
    rec.setdefault("history", ())
    rec["current_equivalent"] = ()
    if "above" not in rec or "below" not in rec:
        above, below = _column_neighbours(key)
        rec.setdefault("above", above)
        rec.setdefault("below", below)
    rec.pop("aliases", None)
    return rec


def geolex_lookup(name: str, resolve_superseded: bool = True) -> Quantity | Refusal:
    """Resolve a Bend Arch outcrop-belt stratigraphic name. See `specs/61-geolex_lookup.md`.

    Abandoned names return their history with the current equivalent, and return
    no equivalent where Eargle (1960) states none. A short name reaching more
    than one catalogued unit is a Refusal, because "Ricker" names three units in
    this document and guessing between them is the failure mode.
    """
    if not isinstance(name, str):
        raise TypeError("geolex_lookup takes a string name")
    if not name.strip():
        raise ValueError("geolex_lookup needs a non-empty name")

    query = _canonical(name)
    match_mode = "exact"
    matched_on = query
    hit = _GEOLEX_EXACT.get(query)

    if hit is None:
        short = _short_name(query)
        candidates = _GEOLEX_SHORT.get(short, [])
        if len(candidates) > 1:
            names = tuple(sorted(
                (GEOLEX_UNITS.get(c) or GEOLEX_SUPERSEDED[c])["name"] for c in candidates
            ))
            return Refusal(
                reason=(f"{name!r} is ambiguous: the short name {short!r} reaches "
                        f"{len(candidates)} catalogued units; this tool will not choose "
                        "between them"),
                needed=names,
                source=E_TABLE1,
            )
        if len(candidates) == 1:
            key = candidates[0]
            hit = ("unit" if key in GEOLEX_UNITS else "superseded", key)
            match_mode = "short_name"
            matched_on = short

    if hit is None:
        known = tuple(sorted(
            {r["name"] for r in GEOLEX_UNITS.values()}
            | {r["name"] for r in GEOLEX_SUPERSEDED.values()}
        ))
        return Refusal(
            reason=(f"{name!r} is not in the Eargle (1960) nomenclature of Brown and "
                    "Coleman Counties, Texas; this tool matches exactly and will not "
                    "guess a near neighbour"),
            needed=known,
            source=E_TABLE1,
        )

    table, key = hit
    if match_mode == "exact" and query != key and query != _canonical(
            (GEOLEX_UNITS.get(key) or GEOLEX_SUPERSEDED[key])["name"]):
        match_mode = "alias"

    record = _geolex_record(table, key)

    current_unit = None
    if table == "superseded" and resolve_superseded and record["current_equivalent"]:
        resolved = []
        for eq in record["current_equivalent"]:
            ekey = _canonical(eq)
            target = _GEOLEX_EXACT.get(ekey)
            if target and target[0] == "unit":
                resolved.append(_geolex_record("unit", target[1]))
        current_unit = tuple(resolved) or None

    flags: list[str] = [VINTAGE_FLAG, AREA_FLAG]
    if record.get("above") or record.get("below"):
        flags.append(BOUNDS_FLAG)
    if table == "superseded" and not record["current_equivalent"]:
        flags.append("the source states no single current equivalent for this name; "
                     "the history is the answer")
    if match_mode == "short_name":
        flags.append(f"matched on short name {matched_on!r}; the catalogued unit is "
                     f"{record['name']!r}")
    flags.extend(record.get("flags", ()))

    anchors = tuple(dict.fromkeys(record.get("anchors", {}).values()))
    return Quantity(
        value=1.0,
        unit="records",
        method="geolex_lookup v1 (Eargle, 1960, USGS PP 315-D; Brown and Coleman Cos., Tex.)",
        source="; ".join(anchors) if anchors else E_TABLE1,
        inputs={
            "query": name,
            "canonical_query": query,
            "match_mode": match_mode,
            "matched_on": matched_on,
            "unit": record,
            "current_unit": current_unit,
        },
        assumptions={
            "survey": "1950-54 field mapping (#2)",
            "published": 1960,
            "area": "Brown and Coleman Counties, Texas (Colorado River valley)",
            "column_source": "Table 1 at #3; upper Pueblo members at #20",
        },
        flags=tuple(flags),
    )


# =============================================================================
# 62 - basin_prior_lookup
# =============================================================================

BASIN_FIELDS: tuple[str, ...] = ("trap_style", "contact_behaviour", "tool_suites",
                                 "pitfalls")

# `year_basis` is "stated" where #34 names the decade outright and "inferred"
# where a phrase ("late 1960's", "recently developed") had to be turned into
# integers so that `year=` can work. Every inferred range says so on the record.
BOONSVILLE_ERAS: tuple[dict[str, Any], ...] = (
    {
        "era": "1940s-1950s (ES logs)", "years": (1945, 1959), "year_basis": "stated",
        "curves": ("SP", "16-in Short Normal (SN)", "64-in Long Normal (LN)",
                   "18-ft 8-in Lateral Log (LAT)",
                   "microlog: Caliper, Micro Normal (2 in), Micro Inverse (1 in x 1 in)"),
        "statement": ("In the 1940's and 1950's, only resistivity measurements were "
                      "available. At first, these data consisted of electric sonde logs "
                      "(ES logs), which made four measurements: Spontaneous Potential "
                      "(SP), 16-inch Short Normal (SN), 64-inch Long Normal (LN), and "
                      "18-ft, 8-inch Lateral Log (LAT)."),
        "cautions": (
            "The Lateral Log measured resistivity values that were close to the true "
            "resistivity only in sandstones that were at least five times as thick as the "
            "measure length (18 ft, 8 inches) of the tool; most sands in the Bend "
            "Conglomerate are not this thick.",
            "These micrologging tools were used to find permeable zones in a qualitative "
            "way, on the basis of the concept that the curve cross-over that occurs when "
            "the resistivity is below 20 ohm-ms is a good indication of a permeable sand.",
            "no porosity measurement of any kind was available in this era",
        ),
    },
    {
        "era": "early induction (IES logs)", "years": (1960, 1964), "year_basis": "inferred",
        "curves": ("SP", "16-in Short Normal (SN)", "Deep Induction (ILD)"),
        "statement": ("The first induction tools that were used in Boonsville field were "
                      "the Induction Electric Logs (IES logs), which provided three "
                      "measurements: Spontaneous Potential (SP), 16-inch Short Normal "
                      "(SN), and Deep Induction (ILD)."),
        "cautions": (
            "#34 gives no start year for the IES era; the range here is the interval "
            "between the ES era and the late-1960s ISF era and is the tool's inference, "
            "not the source's statement",
            "vendor differences were 'not enough to make any substantial difference to "
            "the water-saturation calculations'",
        ),
    },
    {
        "era": "late 1960s (ISF/Sonic)", "years": (1965, 1969), "year_basis": "inferred",
        "curves": ("SP", "Spherically Focused Log (SFL)", "Deep Induction (ILD)",
                   "borehole compensated sonic (BHS)", "gamma ray (GR)"),
        "statement": ("In the late 1960's, the Short Normal was replaced by focused "
                      "shallow resistivity tools, such as the Spherically Focused Log "
                      "(SFL). The new resistivity tool was then known as the Induction "
                      "SFL (I/SFL) tool and was often run with the newly developed "
                      "borehole compensated sonic (BHS) tool and the gamma ray (GR) tool. "
                      "The combined tool suite was referred to as the ISF/Sonic suite by "
                      "Schlumberger."),
        "cautions": ("'late 1960's' read as 1965-1969 by this tool; #34 gives no years",),
    },
    {
        "era": "1970s (CNL/FDC)", "years": (1970, 1979), "year_basis": "stated",
        "curves": ("Compensated Neutron (CNL)", "Compensated Formation Density (FDC)",
                   "gamma ray (GR)", "Induction SFL"),
        "statement": ("In the 1970's, two new tools, the Compensated Neutron (CNL) and "
                      "the Compensated Formation Density (FDC) devices, became commonly "
                      "used. These tools were used to estimate porosities and lithologies "
                      "of the formation, and they usually replaced sonic tools in "
                      "Boonsville field."),
        "cautions": ("few sonic tools were run in the study area because at the time when "
                     "these tools were popular, the area was not being drilled",),
    },
    {
        "era": "1980s (density with PEF)", "years": (1980, 1989), "year_basis": "stated",
        "curves": ("Compensated Formation Density with photoelectric effect (PEF)",
                   "Compensated Neutron (CNL)", "gamma ray (GR)", "Induction SFL"),
        "statement": ("In the 1980's, the density tool was enhanced to include a "
                      "photoelectric effect measurement (PEF) that is very useful in "
                      "determining lithology, particularly for detecting the presence of "
                      "calcite."),
        "cautions": (),
    },
    {
        "era": "recent, to the 1995 report", "years": (1990, 1995), "year_basis": "inferred",
        "curves": ("microwave absorption tool (EPT)", "formation scanner (FMS)",
                   "formation microimager (FMI)"),
        "statement": ("Other recently developed tools that have been used in Boonsville "
                      "field include the microwave absorption tool (EPT) and formation "
                      "scanning tools (FMS and FMI)."),
        "cautions": ("'recently developed' read as 1990-1995 by this tool, bounded by the "
                     "report date; #34 gives no years",
                     "the FMI was run in only three cooperative wells (B Yates 17D, B "
                     "Yates 18D, I. G. Yates 33)"),
    },
)

BOONSVILLE_LOG_RECORD = (1945, 1995)  # discovery year (#34) to report date

BOONSVILLE_PRIORS: dict[str, dict[str, Any]] = {
    "trap_style": {
        "anchor": B_TRAP,
        "extra_anchors": (B_AREA,),
        "statements": (
            "The predominant compartmentalization mechanisms observed in the Boonsville "
            "Project Area are: stratigraphic, comprising surface-bounded, facies-bounded "
            "and cement-bounded compartments; structural, mainly fault-bounded "
            "compartments; and perhaps the most common type encountered at Boonsville is "
            "a combination of stratigraphic and structural mechanisms. (#16)",
            "Many small-scale, near-vertical fault zones... Most of these high-angle, "
            "normal and reverse faults have less than 100 ft of displacement and are "
            "typically on the order of 20 to 30 ft. (#16)",
            "We interpret these features to have resulted from dissolution and "
            "subsequent, episodic collapse of karst cavities in the Paleozoic platform "
            "carbonate units, namely, the Marble Falls (Pennsylvanian Morrow), Comyn "
            "(Mississippian), and Ellenburger (Cambro-Ordovician) Formations underlying "
            "the Atoka interval. (#16)",
            "subtle differences in structural elevation at the pre-Atoka, Paleozoic "
            "carbonate stratigraphic level controlled the geographical locations of "
            "incised valleys, fluvial and fluvio-deltaic axes in which high-energy "
            "reservoir facies were concentrated. (#16)",
            "the best production has occurred where thick Vineyard sandstones are draped "
            "over subtle structural highs (#16)",
            "Previous investigations have concluded that trapping mechanisms are due "
            "predominantly to sandstone facies pinch-outs and permeability pinch-outs due "
            "to diagenetic cements (Glover, 1982; Lahti and Huber, 1982; Thompson, 1982). "
            "(#7)",
        ),
        "flags": ("field-scale: observed in a 26-mi2 project area in Wise and Jack "
                  "Counties, Texas; the source does not offer this as a basin-wide or "
                  "general classification",),
    },
    "contact_behaviour": {
        "anchor": B_HABITAT,
        "extra_anchors": (B_TRAP,),
        "statements": (
            "Gas accumulations in Ouachita foreland basins, including Bend Conglomerate "
            "gas in the Fort Worth Basin, occur as large, pervasive, deep basin "
            "accumulations (Masters, 1979; Meckel and others, 1992). (#8)",
            "Pennsylvanian gas reservoirs in these basins, typically underpressured, "
            "produce little to no water and are relatively tight (typically less than 10 "
            "md). (#8)",
            "They are hydraulically separated from updip/overlying, more permeable, "
            "normally pressured water-bearing units (Meckel and others, 1992). (#8)",
            "The source of the natural gas is probably the abundant humic materials "
            "(land-derived, macerated plant material) in shales that encase the sandstone "
            "reservoirs (Meckel and others, 1992). (#8)",
            "Several Boonsville wells drilled in small (~ 100 acres), structurally high "
            "fault blocks encountered gas at higher than expected pressures in otherwise "
            "hydraulically well connected reservoir zones (Caddo, Vineyard), suggesting "
            "that the vertical faults observed in the 3-D seismic data can act as partial "
            "barriers to fluid flow. (#16)",
        ),
        "flags": (
            "do not expect a conventional downdip gas-water contact: the source describes "
            "a deep basin accumulation hydraulically separated from the updip water-"
            "bearing section, producing little to no water",
            "basin-scale: #8 makes this claim for Ouachita foreland basins generally, "
            "naming the Arkoma, Val Verde and Black Warrior Basins as similar habitats",
        ),
    },
    "tool_suites": {
        "anchor": B_TOOLS,
        "extra_anchors": (),
        "eras": BOONSVILLE_ERAS,
        "flags": ("this is Boonsville's own drilling and logging history, not a general "
                  "logging chronology: the 1970s sonic gap exists because 'the area was "
                  "not being drilled' (#34)",
                  "each generation replaced the last on NEW wells; older wells keep their "
                  "original suite"),
    },
    "pitfalls": {
        "anchor": B_PITFALLS,
        "extra_anchors": (B_TOOLS,),
        "statements": (
            "Log correlations and mapping of depositional environments and facies tracts "
            "in surface-dominated strata are especially difficult and prone to error "
            "because it is not uncommon for systems tracts and sometimes even entire "
            "sequences to be truncated or absent in some of a field's wells. (#10)",
            "The process of well-log correlation is inherently biased toward "
            "lithostratigraphic correlation... It is easy for the interpreter to string "
            "together rock units having a similar log character or units that appear at "
            "similar depths, when in reality, time lines, true reservoir compartment "
            "geometries, and flow-unit architectures can be vastly different from layer "
            "cake lithostratigraphic interpretations. (#10)",
            "without an accurate chronostratigraphic framework, subsequent "
            "interpretations and mapping of depositional systems and sandstone reservoir "
            "geometries are likely to be incorrect. (#10)",
            "Midcontinent strata are surface dominated and are typically made up of "
            "complex mosaics of thin, incompletely preserved slivers of systems tracts in "
            "which sandstone reservoirs occur. (#10)",
            "The Lateral Log measured resistivity values that were close to the true "
            "resistivity only in sandstones that were at least five times as thick as the "
            "measure length (18 ft, 8 inches) of the tool; most sands in the Bend "
            "Conglomerate are not this thick. (#34)",
        ),
        "flags": ("the Lateral Log statement means the deepest resistivity curve on a "
                  "1940s-50s Boonsville well is not Rt for these sands (#34)",),
    },
}

# Registered spellings, all of them names the source itself uses for the area.
BOONSVILLE_KEYS: tuple[str, ...] = (
    "boonsville", "boonsville field", "boonsville (bend conglomerate gas) field",
    "fort worth basin", "wise county", "wise county, texas", "jack county",
    "jack county, texas", "wise and jack counties",
)
_BASIN_SCALE_KEYS = frozenset({"fort worth basin"})

BOONSVILLE_AREA = {
    "field": "Boonsville (Bend Conglomerate Gas) field",
    "basin": "Fort Worth Basin",
    "counties": ("Wise", "Jack"),
    "state": "Texas",
    "project_area": "26-mi2 study area",
    "anchor": B_AREA,
    "extra_anchors": (B_AREA_NAMED,),
    # per field, because #7 does not name the counties and #23 does not name the basin
    "anchors": {"field": B_AREA_NAMED, "basin": B_AREA, "counties": B_AREA_NAMED,
                "state": B_AREA_NAMED, "project_area": B_AREA},
}

_BASIN_RECORDS: dict[str, dict[str, Any]] = {k: BOONSVILLE_PRIORS for k in BOONSVILLE_KEYS}

# --- regional priors beyond Boonsville ---------------------------------------
#
# The Boonsville records above are hand-written from one report, and they stay
# that way. These are extracted from the rest of the corpus by
# `scripts/build_basin_priors.py` under the same two gates the strat column uses:
# the statement is verbatim from the anchor it cites, and a second pass agreed it
# is about that location. Most cells come back empty, which is the corpus being
# honest about what it holds — an invented prior is worse than a refusal, because
# a screen acts on it.
_REGIONAL_FILE = pathlib.Path(
    os.environ.get("GEOLOGY_CORPUS_ROOT")
    or pathlib.Path(__file__).resolve().parent.parent
) / "tables" / "basin-priors-bend-arch.json"


@functools.lru_cache(maxsize=1)
def _regional_records() -> dict[str, dict[str, Any]]:
    """alias -> priors dict, in the same shape `BOONSVILLE_PRIORS` uses."""
    try:
        data = json.loads(_REGIONAL_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}

    out: dict[str, dict[str, Any]] = {}
    for entry in data.get("locations", ()):
        priors: dict[str, Any] = {}
        for field, cell in entry.get("priors", {}).items():
            if not cell.get("statement"):
                continue
            priors[field] = {
                "anchor": cell["anchor"],
                "statements": (cell["statement"],),
                "flags": (f"regional prior for {entry['label']}, extracted from the "
                          "corpus and verified verbatim against its anchor",),
            }
        if not priors:
            continue
        priors["_meta"] = {"key": entry["key"], "label": entry["label"],
                           "regional": True}
        for alias in [entry["key"], *entry.get("aliases", ())]:
            out.setdefault(_canonical(alias), priors)
    return out


def basin_prior_lookup(location: str, fields: tuple[str, ...] | None = None,
                       year: int | None = None) -> Quantity | Refusal:
    """Published regional priors for a location. See `specs/62-basin_prior_lookup.md`.

    The four fields come from four different segments, so each rides with its
    own anchor rather than sharing the call's. One area is covered; every other
    location is a refusal, which is the honest size of the evidence.
    """
    if not isinstance(location, str):
        raise TypeError("basin_prior_lookup takes a string location")
    if not location.strip():
        raise ValueError("basin_prior_lookup needs a non-empty location")
    wanted = tuple(fields) if fields is not None else BASIN_FIELDS
    unknown = [f for f in wanted if f not in BASIN_FIELDS]
    if unknown:
        raise ValueError(f"unknown prior field(s) {unknown}; known: {list(BASIN_FIELDS)}")
    if year is not None and not isinstance(year, int):
        raise TypeError("year must be an int")

    key = _canonical(location)
    regional = _regional_records()
    record = _BASIN_RECORDS.get(key) or regional.get(key)
    if record is None:
        return Refusal(
            reason=(f"no regional prior in the corpus for {location!r}; this tool covers "
                    "the areas the corpus actually documents and will not substitute a "
                    "neighbouring basin"),
            needed=BOONSVILLE_KEYS + tuple(sorted(regional)) + (
                "a published regional study for that area added to the corpus",),
            source=B_AREA,
        )

    meta = record.get("_meta")
    if meta and meta.get("regional"):
        return _regional_prior(location, key, meta, record, wanted)

    lo, hi = BOONSVILLE_LOG_RECORD
    eras = BOONSVILLE_ERAS
    if year is not None:
        if year < lo or year > hi:
            return Refusal(
                reason=(f"year {year} is outside the logged record the source documents: "
                        f"{lo} (field discovery) to {hi} (report date)"),
                needed=(f"a logging year between {lo} and {hi}",
                        "a later source for post-1995 tool suites"),
                source=B_TOOLS,
            )
        eras = tuple(e for e in BOONSVILLE_ERAS
                     if e["years"][0] <= year <= e["years"][1])

    priors: dict[str, Any] = {}
    anchors: list[str] = []
    flags: list[str] = [
        f"source: BEG/GRI/DOE (1995) Boonsville secondary gas recovery study; logging "
        f"record spans {lo}-{hi}",
    ]
    if key in _BASIN_SCALE_KEYS:
        flags.append(
            "queried at basin scale: only the hydrocarbon-habitat field (#8) is stated at "
            "basin scale by the source; trap style, tool suites and pitfalls are "
            "observations from a 26-mi2 project area in Wise and Jack Counties"
        )

    for field in wanted:
        entry = dict(record[field])
        if field == "tool_suites":
            entry["eras"] = eras
            if year is not None:
                entry["matched_year"] = year
                if any(e["year_basis"] == "inferred" for e in eras):
                    flags.append(
                        f"the era matching {year} has an inferred year range; #34 dates it "
                        "in words only")
        priors[field] = entry
        anchors.append(entry["anchor"])
        anchors.extend(entry.get("extra_anchors", ()))
        flags.extend(entry.get("flags", ()))

    return Quantity(
        value=float(len(priors)),
        unit="records",
        method="basin_prior_lookup v1 (BEG/GRI/DOE 1995, Boonsville SGR study)",
        source="; ".join(dict.fromkeys(anchors)),
        inputs={
            "location": location,
            "canonical_location": key,
            "matched_key": key,
            "area": BOONSVILLE_AREA,
            "year": year,
            "priors": priors,
        },
        assumptions={
            "study": "Secondary Natural Gas Recovery, Boonsville field, Fort Worth Basin",
            "published": 1995,
            "project_area_mi2": 26,
            "logging_record_spans": f"{lo}-{hi}",
        },
        flags=tuple(dict.fromkeys(flags)),
    )


def _regional_prior(location: str, key: str, meta: dict[str, Any],
                    record: dict[str, Any],
                    wanted: tuple[str, ...]) -> Quantity | Refusal:
    """The non-Boonsville half of `basin_prior_lookup`.

    Kept separate rather than folded in, because the Boonsville path carries a
    logging-era model that belongs to that one study: a `year=` argument means
    "which tool suite was running at Boonsville then", and answering it from a
    different area's record would be the sort of quiet substitution this tool
    exists to refuse. A regional record answers the fields it has evidence for
    and says plainly which ones it does not.
    """
    have = [f for f in wanted if f in record]
    missing = [f for f in wanted if f not in record]
    if not have:
        return Refusal(
            reason=(f"the corpus documents {meta['label']}, but not for "
                    f"{', '.join(missing)}"),
            needed=tuple(f for f in BASIN_FIELDS if f in record)
            or ("a published study of this area added to the corpus",),
            source="; ".join(dict.fromkeys(
                entry["anchor"] for f, entry in record.items() if f != "_meta")),
        )

    priors = {f: dict(record[f]) for f in have}
    anchors = [record[f]["anchor"] for f in have]
    flags = [flag for f in have for flag in record[f].get("flags", ())]
    if missing:
        flags.append("the corpus carries no statement for "
                     + ", ".join(missing) + " in this area")

    return Quantity(
        value=float(len(priors)),
        unit="records",
        method="basin_prior_lookup v1 - regional record extracted from the corpus",
        source="; ".join(dict.fromkeys(anchors)),
        inputs={
            "location": location,
            "canonical_location": key,
            "matched_key": meta["key"],
            "area": {"label": meta["label"], "scale": "regional"},
            "year": None,
            "priors": priors,
            "fields_without_evidence": tuple(missing),
        },
        assumptions={
            "extraction": ("every statement is verbatim from the anchor it cites and was "
                           "checked as being about this location"),
            "not_a_study": ("this is a reading of the corpus, not a single published "
                            "study of the area; treat it as evidence, not as a survey"),
        },
        flags=tuple(dict.fromkeys(flags)),
    )


# =============================================================================
# 64 - correlation_selector
# =============================================================================

ROCK_TYPES: dict[str, str] = {
    "sandstone": "clastic", "sand": "clastic", "clastic": "clastic",
    "shaly sand": "clastic", "shaly sandstone": "clastic",
    "limestone": "carbonate", "carbonate": "carbonate",
    "dolomite": "carbonate", "dolostone": "carbonate",
}
FLUIDS: tuple[str, ...] = ("oil", "gas", "water", "condensate")
FERTL_A: dict[str, float] = {"gulf coast": 0.25, "rocky mountains": 0.35,
                             "rockies": 0.35}

# Hilchie (1978), quoted at #49 and #50.
VSHALE_NEGLIGIBLE = 0.10      # below this, shale does not significantly affect Sw
VSHALE_SIGNIFICANT = 0.15     # above this, it does; between is the source's own band
SALTY_RW_OHMM_80F = 0.3       # Rw <= this => "very salty", corrections not needed
SALTY_NACL_PPM = 20000.0

RSH_CAVEAT = (
    "In shaly sand analysis, a geologist must make an assumption that resistivity of an "
    "adjacent shale (Rsh) is the same as resistivity of shale in the formation. This "
    "assumption is not always correct. (#50)"
)
DIRECTION_CAVEAT = (
    "Remember that all shaly sandstone formulas reduce the water saturation value from "
    "the value that would be calculated if shale effect were ignored... if a geologist "
    "overestimates shale content, a water-bearing zone might appear to be a "
    "hydrocarbon-bearing zone. (#49)"
)
# Asquith & Krygowski #30, verbatim. The tool has no Rmf or Rw input, so it cannot
# evaluate the condition; it names the limit and says the condition is unevaluated
# rather than accepting a laterolog as an unqualified Rt measurement. Table 5.1 at
# #30 lists the deep/shallow laterolog and Laterolog-3/-7 forms.
LATEROLOG_MNEMONICS = frozenset({"laterolog", "lld", "lls", "ll3", "ll7"})
LATEROLOG_LIMIT = (
    "But, when a well is drilled with freshwater muds (where Rmf > 3 Rw), the "
    "laterolog can be strongly affected by invasion. Under these conditions, a "
    "laterolog should not be used"
)
GEOMETRY_GAP_FLAG = (
    "well_geometry is recorded and never used: Asquith & Krygowski ch. 7 (#49-#51) states "
    "no hole-size, deviation, bed-thickness or invasion applicability limit for any of "
    "these methods, and this tool will not invent one"
)

# family: "saturation" | "reconnaissance" | "crossplot" | "chart"
CORRELATIONS: tuple[dict[str, Any], ...] = (
    {
        "name": "Archie, uncorrected for shale", "citation": "Archie (1942), via Asquith & Krygowski",
        "equation": "7.1", "family": "saturation", "anchor": A_SHALY,
        "limit": ("Hilchie (1978) suggests that for shale to significantly affect "
                  "log-derived water saturations, shale content must be greater than 10 "
                  "to 15%. (#49) Where formation water is very salty, shale has less "
                  "effect on the formation's resistivity. Therefore, calculated water "
                  "saturations without correction for shale are close to true formation "
                  "water saturation. (#50)"),
        "required_inputs": ("Rt", "porosity", "Rw"),
        "required_curves": ("resistivity", "porosity"),
        "shale_role": "uncorrected",
        "flags": (),
    },
    {
        "name": "Automatic compensation (Dewan, 1983)", "citation": "Dewan (1983)",
        "equation": "7.43", "family": "saturation", "anchor": A_SW,
        "limit": ("A technique popular in the 1950s... It used the resistivity and sonic "
                  "logs with Archie's equation. Since the presence of shale caused the "
                  "porosity to read too high and the resistivity to read too low, one "
                  "compensated for the other in the saturation equation."),
        "required_inputs": ("Rw", "Rt", "sonic porosity"),
        "required_curves": ("resistivity", "sonic"),
        "shale_role": "corrected",
        "flags": ("the compensation is an assumed cancellation of two errors, not a "
                  "measurement of either (#50)",),
    },
    {
        "name": "Dispersed-clay model (Dewan, 1983)", "citation": "Dewan (1983)",
        "equation": "7.44, 7.45", "family": "saturation", "anchor": A_SW,
        "limit": ("In the 1960s, with the advent of the density log, the dispersed-clay "
                  "model gained popularity. In this model, the density was assumed to "
                  "respond only to the liquid-filled porosity, while the sonic was "
                  "affected by the clays with the difference (q) being the fraction of "
                  "the intergranular space filled with clay."),
        "required_inputs": ("Rw", "Rt", "sonic porosity", "density porosity"),
        "required_curves": ("resistivity", "sonic", "density"),
        "shale_role": "corrected",
        "flags": ("assumes the clay is dispersed in the intergranular space (#50)",),
    },
    {
        "name": "Fertl (1975)", "citation": "Fertl (1975)",
        "equation": "7.46", "family": "saturation", "anchor": A_SW,
        "limit": "where: a = 0.25 in the Gulf Coast and a = 0.35 in the Rocky Mountains.",
        "required_inputs": ("Rw", "Rt", "porosity", "Vshale", "a (province constant)"),
        "required_curves": ("resistivity", "porosity"),
        "shale_role": "corrected",
        "province_gated": True,
        "flags": (DIRECTION_CAVEAT,),
    },
    {
        "name": "Schlumberger (1975)", "citation": "Schlumberger (1975)",
        "equation": "7.47", "family": "saturation", "anchor": A_SW,
        "limit": ("A Vshale-based method requiring a resistivity value for the shale "
                  "(Rsh) in the formation. " + RSH_CAVEAT),
        "required_inputs": ("Rw", "Rt", "porosity", "Vshale", "Rsh"),
        "required_curves": ("resistivity", "porosity"),
        "shale_role": "corrected",
        "flags": (DIRECTION_CAVEAT,),
    },
    {
        "name": "Simandoux (1963)", "citation": "Simandoux (1963)",
        "equation": "7.48", "family": "saturation", "anchor": A_SW,
        "limit": ("A Vshale-based method requiring a resistivity value for the shale "
                  "(Rsh) in the formation. " + RSH_CAVEAT),
        "required_inputs": ("Rw", "Rt", "porosity", "Vshale", "Rsh"),
        "required_curves": ("resistivity", "porosity"),
        "shale_role": "corrected",
        "flags": (DIRECTION_CAVEAT,),
    },
    {
        "name": "Dual water (Clavier et al., 1977)", "citation": "Clavier et al. (1977)",
        "equation": "7.49-7.52", "family": "saturation", "anchor": A_SW,
        "limit": ("It faces the reality that there is no way to measure cation-exchange "
                  "capacity (CEC) directly from logs and that CEC measurements on cores "
                  "are rare, so Vshale methods are used to correct porosity for clay "
                  "content and to calculate the bound-water saturation (Swb). The "
                  "bound-water and free-water resistivities are determined from nearby "
                  "shales and clean sands."),
        "required_inputs": ("Rw", "Rwa", "Rb", "Swb", "total porosity"),
        "required_curves": ("resistivity", "neutron", "density"),
        "shale_role": "corrected",
        "flags": ("continues to gain popularity because of its closer approximation to "
                  "the responses of shaly sands in a wide variety of conditions (#49) - "
                  "a preference statement, not an applicability limit",
                  "requires a nearby shale and a nearby clean sand in the same well (#50)"),
    },
    {
        "name": "Reconnaissance measurement, clastics", "citation": "Asquith & Krygowski, Fig. 7.1",
        "equation": "Fig. 7.1", "family": "reconnaissance", "anchor": A_SW,
        "limit": ("The resistivity log is the primary reconnaissance measurement because "
                  "clastics tend to consist of reservoirs surrounded by shales whose "
                  "resistivities vary gradually with depth."),
        "required_inputs": (), "required_curves": ("resistivity",),
        "rock_class": "clastic",
        "flags": ("Zones that appear to be shales might be radioactive productive zones; "
                  "shaly zones might produce oil or gas even if they have low resistivity "
                  "(#50)",),
    },
    {
        "name": "Reconnaissance measurement, carbonates", "citation": "Asquith & Krygowski, Fig. 7.1",
        "equation": "Fig. 7.1", "family": "reconnaissance", "anchor": A_CHARTS,
        "limit": ("Formation resistivities tend to vary widely with changing rock types, "
                  "and commonly there are few shales against which to measure changes. In "
                  "this case, the porosity log is the primary reconnaissance measurement."),
        "required_inputs": (), "required_curves": ("porosity",),
        "rock_class": "carbonate",
        "flags": (),
    },
    {
        "name": "Hingle plot, sandstone grid", "citation": "Western Atlas (1995) Chart 7-79, Fig. 7.5",
        "equation": "Fig. 7.5", "family": "crossplot", "anchor": A_CHARTS,
        "limit": ("Hingle plot... generally used for sandstones. The y-axis is "
                  "constructed with tortuosity factor (a) = 1.0 and cementation exponent "
                  "(m) = 2.0."),
        "required_inputs": ("Rt", "porosity or bulk density"),
        "required_curves": ("resistivity", "porosity"),
        "rock_class": "clastic",
        "constants": {"a": 1.0, "m": 2.0},
        "flags": (),
    },
    {
        "name": "Hingle plot, carbonate grid", "citation": "Western Atlas (1995) Chart 7-80, Fig. 7.6",
        "equation": "Fig. 7.6", "family": "crossplot", "anchor": A_CHARTS,
        "limit": ("Hingle plot... generally used for carbonates. The y-axis is "
                  "constructed with tortuosity factor (a) = 0.62 and cementation exponent "
                  "(m) = 2.15."),
        "required_inputs": ("Rt", "porosity or bulk density"),
        "required_curves": ("resistivity", "porosity"),
        "rock_class": "carbonate",
        "constants": {"a": 0.62, "m": 2.15},
        "flags": (),
    },
    {
        "name": "Pickett plot", "citation": "Asquith & Krygowski, Fig. 7.4",
        "equation": "Fig. 7.4", "family": "crossplot", "anchor": A_CHARTS,
        "limit": ("Hingle and Pickett crossplot techniques are simple and rapid methods "
                  "for determining a formation's water saturation (Sw), water resistivity "
                  "(Rw), cementation factor (m), and matrix values. (#50) The "
                  "water-bearing line (Sw = 100%) was drawn through the cluster of points "
                  "with a slope of -1/m. (#51)"),
        "required_inputs": ("Rt", "porosity", "a cluster of water-bearing points"),
        "required_curves": ("resistivity", "porosity"),
        "flags": ("m is read off the plot, so the plot needs enough porosity range to "
                  "constrain it: 'Because of the limited porosity range of the points and "
                  "their scatter, other values of m from 1.8 to 2.15 could be justified' "
                  "(#51)",),
    },
    {
        "name": "Buckles plot (bulk volume water)", "citation": "Asquith & Krygowski, Fig. 7.3",
        "equation": "Fig. 7.3", "family": "crossplot", "anchor": A_CHARTS,
        "limit": ("A series of points plotting along a particular hyperbolic curve "
                  "indicates that the bulk volume water is constant and that the "
                  "formation is close to irreducible water saturation... Data points from "
                  "zones not at Sw irr scatter from this pattern."),
        "required_inputs": ("Sw", "porosity"),
        "required_curves": ("resistivity", "porosity"),
        "flags": ("this is the TEST for irreducible saturation, so it does not require "
                  "irreducible saturation as an input (#51)",),
    },
    {
        "name": "Permeability from porosity vs irreducible Sw",
        "citation": "Schlumberger (1998) Chart K-3, Fig. 7.8",
        "equation": "Fig. 7.8", "family": "chart", "anchor": A_CHARTS,
        "limit": ("The chart is constructed with the assumption of a medium-gravity oil. "
                  "It is important to remember that this chart is only valid for "
                  "estimating permeability (K) in zones at irreducible water saturation "
                  "(Sw irr)."),
        "required_inputs": ("porosity", "irreducible water saturation"),
        "required_curves": ("porosity",),
        "fluid_gated": ("oil",),
        "needs_irreducible": True,
        "flags": (),
    },
)


# Which declared mnemonics satisfy which measurement class. A closed, explicit
# map rather than substring guessing: "RESD" does not contain "resistivity", and
# guessing either way would silently include or exclude a method. A mnemonic that
# is not listed satisfies nothing and is reported back as unrecognised, so the
# failure direction is "you appear to lack this curve", never "you have it".
# "porosity" is satisfied by any porosity-capable measurement, which is how
# Asquith's carbonate reconnaissance rule and the crossplots use the term.
CURVE_CLASSES: dict[str, frozenset[str]] = {
    "resistivity": frozenset({
        "resistivity", "res", "resd", "resm", "ress", "rt", "ro", "rdeep",
        "ild", "ilm", "lld", "lls", "laterolog", "sfl", "msfl",
        "sn", "ln", "lat", "at90", "at60", "at30", "induction"}),
    "sonic": frozenset({"sonic", "dt", "dtc", "dtco", "ac", "bhc", "bhs", "itt"}),
    "density": frozenset({"density", "rhob", "rhoz", "rhog", "den", "fdc", "dphi",
                          "drho"}),
    "neutron": frozenset({"neutron", "nphi", "npor", "cnl", "tnph", "nphi_ls"}),
    "gamma ray": frozenset({"gamma ray", "gr", "cgr", "sgr", "gapi"}),
    "porosity": frozenset({
        "porosity", "phi", "phit", "phie",
        "density", "rhob", "rhoz", "den", "fdc", "dphi",
        "neutron", "nphi", "npor", "cnl", "tnph",
        "sonic", "dt", "dtc", "dtco", "ac", "bhc", "bhs", "sphi"}),
}


def _curves_present(available: tuple[str, ...] | None,
                    needed: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(missing classes, unrecognised mnemonics). Both empty when nothing was declared."""
    if available is None:
        return (), ()
    have = {_canonical(c) for c in available}
    known = set().union(*CURVE_CLASSES.values())
    unrecognised = tuple(sorted(h for h in have if h not in known))
    missing = tuple(cls for cls in needed
                    if not (have & CURVE_CLASSES.get(cls, frozenset({cls}))))
    return missing, unrecognised


def correlation_selector(rock_type: str, fluid: str, vshale: float | None = None,
                         rw_ohmm_at_80f: float | None = None,
                         nacl_ppm: float | None = None,
                         province: str | None = None,
                         available_curves: tuple[str, ...] | None = None,
                         at_irreducible: bool | None = None,
                         well_geometry: dict[str, Any] | None = None,
                         ) -> Quantity | Refusal:
    """Which published correlations apply here, and which do not, and why not.

    See `specs/64-correlation_selector.md`. Every exclusion names the sentence in
    Asquith & Krygowski ch. 7 that caused it; an input that was not supplied
    excludes nothing and says which input would decide it.
    """
    if not isinstance(rock_type, str) or not isinstance(fluid, str):
        raise TypeError("rock_type and fluid must be strings")
    if vshale is not None and not (0.0 <= vshale <= 1.0):
        raise ValueError("vshale must be a fraction in [0, 1]")
    if rw_ohmm_at_80f is not None and rw_ohmm_at_80f <= 0:
        raise ValueError("rw_ohmm_at_80f must be positive")
    if nacl_ppm is not None and nacl_ppm < 0:
        raise ValueError("nacl_ppm must be non-negative")

    rock_key = _canonical(rock_type)
    if rock_key not in ROCK_TYPES:
        return Refusal(
            reason=f"unknown rock_type {rock_type!r}; this tool matches an exact vocabulary",
            needed=tuple(sorted(ROCK_TYPES)),
            source=A_SW,
        )
    fluid_key = _canonical(fluid)
    if fluid_key not in FLUIDS:
        return Refusal(
            reason=f"unknown fluid {fluid!r}; this tool matches an exact vocabulary",
            needed=FLUIDS,
            source=A_CHARTS,
        )
    rock_class = ROCK_TYPES[rock_key]
    prov_key = _canonical(province) if province else None

    # The two salinity indicators must agree about which side of Hilchie's
    # thresholds the formation sits on; the source gives no rule for reconciling
    # them, so a disagreement is a refusal rather than a silent precedence.
    salty_by_rw = None if rw_ohmm_at_80f is None else rw_ohmm_at_80f <= SALTY_RW_OHMM_80F
    salty_by_ppm = None if nacl_ppm is None else nacl_ppm >= SALTY_NACL_PPM
    if salty_by_rw is not None and salty_by_ppm is not None and salty_by_rw != salty_by_ppm:
        return Refusal(
            reason=(f"salinity inputs disagree: Rw={rw_ohmm_at_80f} ohm-m at 80F "
                    f"(threshold {SALTY_RW_OHMM_80F}) and NaCl={nacl_ppm} ppm (threshold "
                    f"{SALTY_NACL_PPM:.0f}) fall on opposite sides of Hilchie's (1978) "
                    "criterion; the source gives no rule for reconciling them"),
            needed=("one salinity indicator, or a measured water analysis",),
            source=A_SW,
        )
    very_salty = salty_by_rw if salty_by_rw is not None else salty_by_ppm

    applicable: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    result_flags: list[str] = [GEOMETRY_GAP_FLAG]

    _, unrecognised_curves = _curves_present(available_curves, ())
    laterologs = tuple(sorted(
        c for c in (available_curves or ()) if _canonical(c) in LATEROLOG_MNEMONICS))
    if laterologs:
        result_flags.append(
            f"{', '.join(laterologs)} satisfies the resistivity requirement above, but "
            f"Asquith & Krygowski state a limit on it ({A_RESISTIVITY}): "
            f"\"{LATEROLOG_LIMIT}\". This tool has no Rmf or Rw input, so that "
            "condition is UNEVALUATED here; supply the mud-filtrate and formation-water "
            "resistivities before reading the deep laterolog as Rt")
    if unrecognised_curves:
        result_flags.append(
            "unrecognised curve mnemonic(s) in available_curves: "
            + ", ".join(unrecognised_curves)
            + " - they satisfy no measurement class in CURVE_CLASSES, so a method may be "
              "reported as lacking a measurement the well actually has")

    for spec in CORRELATIONS:
        entry = {k: v for k, v in spec.items()
                 if k in ("name", "citation", "equation", "family", "limit",
                          "required_inputs", "anchor", "constants")}
        entry["flags"] = list(spec.get("flags", ()))
        reason = None

        # 1. rock type
        if spec.get("rock_class") and spec["rock_class"] != rock_class:
            reason = (f"stated for {spec['rock_class']}s; {rock_type!r} is a "
                      f"{rock_class}. Limit: {spec['limit']}")

        # 2. fluid
        if reason is None and spec.get("fluid_gated") and fluid_key not in spec["fluid_gated"]:
            reason = (f"the source states this is for {'/'.join(spec['fluid_gated'])}; "
                      f"fluid is {fluid_key!r}. Limit: The chart is constructed with the "
                      "assumption of a medium-gravity oil.")

        # 3. irreducible saturation
        if reason is None and spec.get("needs_irreducible"):
            if at_irreducible is False:
                reason = ("this chart is only valid for estimating permeability (K) in "
                          "zones at irreducible water saturation (Sw irr), and "
                          "at_irreducible=False")
            elif at_irreducible is None:
                entry["flags"].append(
                    "at_irreducible was not supplied; the chart is only valid at "
                    "irreducible water saturation, so confirm with a Buckles plot first")

        # 4. province (Fertl only)
        if reason is None and spec.get("province_gated"):
            if prov_key is None:
                entry["flags"].append(
                    "province was not supplied; a published coefficient a exists only for "
                    "the Gulf Coast (0.25) and the Rocky Mountains (0.35)")
            elif prov_key not in FERTL_A:
                reason = (f"no published coefficient a for {province!r}: the source "
                          "publishes a = 0.25 in the Gulf Coast and a = 0.35 in the Rocky "
                          "Mountains, and no value elsewhere")
            else:
                entry["constants"] = {"a": FERTL_A[prov_key]}

        # 5. shale gate
        if reason is None and spec.get("shale_role"):
            corrected = spec["shale_role"] == "corrected"
            if very_salty is True and corrected:
                reason = ("Where formation water is very salty, shale has less effect on "
                          "the formation's resistivity. Therefore, calculated water "
                          "saturations without correction for shale are close to true "
                          "formation water saturation. (#50)")
            elif very_salty is True and not corrected:
                entry["flags"].append(
                    "applicable because the formation water is very salty (#50)")
            elif vshale is None:
                entry["flags"].append(
                    "vshale was not supplied; Hilchie's (1978) 10-15% threshold decides "
                    "between corrected and uncorrected saturation and could not be applied")
            elif vshale <= VSHALE_NEGLIGIBLE and corrected:
                reason = (f"Vshale {vshale:.3f} is at or below {VSHALE_NEGLIGIBLE:.2f}: "
                          "'for shale to significantly affect log-derived water "
                          "saturations, shale content must be greater than 10 to 15%' "
                          "(Hilchie, 1978, #49)")
            elif vshale > VSHALE_SIGNIFICANT and not corrected:
                reason = (f"Vshale {vshale:.3f} exceeds {VSHALE_SIGNIFICANT:.2f}, above "
                          "which Hilchie (1978) states shale significantly affects "
                          "log-derived water saturations (#49)")
            elif VSHALE_NEGLIGIBLE < vshale <= VSHALE_SIGNIFICANT:
                entry["flags"].append(
                    f"Vshale {vshale:.3f} lies inside Hilchie's own 10-to-15% band, which "
                    "the source does not narrow; both the corrected and uncorrected "
                    "families are reported")

        # 6. required curves
        if reason is None:
            missing, _ = _curves_present(available_curves, spec.get("required_curves", ()))
            if missing:
                reason = ("required measurement(s) not in available_curves: "
                          + ", ".join(missing))

        if reason is None:
            entry["reason"] = "no stated limit in the source excludes it for these inputs"
            entry["flags"] = tuple(entry["flags"])
            applicable.append(entry)
        else:
            entry["reason"] = reason
            entry["flags"] = tuple(entry["flags"])
            excluded.append(entry)

    if not applicable:
        return Refusal(
            reason=(f"no correlation published at {ASQUITH} ch. 7 applies to rock_type="
                    f"{rock_type!r}, fluid={fluid!r} with the inputs given; "
                    f"{len(excluded)} were excluded by stated limits"),
            needed=tuple(f"{e['name']}: {e['reason']}" for e in excluded)
            + ((("unrecognised curve mnemonic(s): " + ", ".join(unrecognised_curves)),)
               if unrecognised_curves else ()),
            source="; ".join(dict.fromkeys(e["anchor"] for e in excluded)),
        )

    if vshale is None and very_salty is None:
        result_flags.append("neither vshale nor a salinity indicator was supplied, so the "
                            "shale gate could not be applied to the saturation family")

    anchors = tuple(dict.fromkeys([e["anchor"] for e in applicable + excluded]
                                  + ([A_RESISTIVITY] if laterologs else [])))
    return Quantity(
        value=float(len(applicable)),
        unit="records",
        method="correlation_selector v1 (Asquith & Krygowski 2004, ch. 7)",
        source="; ".join(anchors),
        inputs={
            "rock_type": rock_type, "canonical_rock_type": rock_key,
            "rock_class": rock_class,
            "fluid": fluid, "canonical_fluid": fluid_key,
            "vshale": vshale, "rw_ohmm_at_80f": rw_ohmm_at_80f, "nacl_ppm": nacl_ppm,
            "very_salty": very_salty,
            "province": province, "available_curves": available_curves,
            "at_irreducible": at_irreducible,
            "well_geometry": well_geometry,
            "applicable": tuple(applicable),
            "not_applicable": tuple(excluded),
        },
        assumptions={
            "vshale_thresholds": (VSHALE_NEGLIGIBLE, VSHALE_SIGNIFICANT),
            "vshale_threshold_source": "Hilchie (1978) via Asquith & Krygowski #49",
            "salinity_thresholds": {"rw_ohmm_at_80f": SALTY_RW_OHMM_80F,
                                    "nacl_ppm": SALTY_NACL_PPM},
            "salinity_threshold_source": "Hilchie (1978) via Asquith & Krygowski #50",
        },
        flags=tuple(dict.fromkeys(result_flags)),
    )
