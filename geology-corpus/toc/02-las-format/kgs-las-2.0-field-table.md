# kgs-las-2.0-field-table

**Covers:** A reference table/specification for the LAS 2.0 (Log ASCII Standard) file format as documented by the Kansas Geological Survey, covering section structure, required header fields, and mnemonics.

**Authoritative for:** LAS 2.0 required section order and meaning of ~V, ~W, ~C, ~P, ~O, ~A section delimiters, Mandatory mnemonics in the ~Well Information block (e.g. STRT, STOP, STEP, NULL, WELL, API, location fields), Conventional LAS null/no-data values such as -999.25, Parsing and validating LAS 2.0 ASCII well log files

**Not good for:** LAS 3.0 or LAS 1.2 syntax differences, or vendor binary log formats (DLIS, LIS), Interpreting curve data or petrophysical calculation from log values, Curve mnemonic semantics beyond the header (tool physics, service-company naming), Geological, stratigraphic, or basin-specific content of any kind

**Scope:** Purely a data-format/file-structure reference tied to the LAS 2.0 standard as applied in Kansas Geological Survey holdings; no geographic, stratigraphic, or interpretive scope, and field conventions may differ for non-KGS or non-US log libraries.

_2 segments._

---

### LAS 2.0 file structure and required header fields  `02-las-format/kgs-las-2.0-field-table#1` (chars 143-4852)
Answers: What sections are required in an LAS 2.0 file? · What does ~V, ~W, ~C, ~P, ~O, and ~A mean in a LAS file? · Which mnemonics are required in the ~Well Information section? · What are common LAS null values? · What does WRAP mean in the LAS version section? · How should the ASCII log data section be formatted in LAS 2.0? · What is the difference between LAS 1.2, 2.0, and 3.0? · Who created the LAS standard and when? · Where do I find the CWLS LAS specification document? · What date format should the DATE field use in a LAS header?
Entities: LAS, Log ASCII Standard, Canadian Well Logging Society, CWLS, LIS, ~V, ~VERSION INFORMATION SECTION, ~W, WELL INFORMATION SECTION, ~C, ~CURVE INFORMATION SECTION, ~P, ~PARAMETER INFORMATION SECTION, ~O, ~OTHER, ~A, ~ASCII LOG DATA, VERS, WRAP, STRT, STOP, STEP, NULL, COMP, WELL, FLD, LOC, PROV, CTRY, STAT, CNTY, UWI, API, SRVC, LIC, DATE, -999.25, Shamar-1.las, John R. Victorine, LAS 3.0, LAS 2.0
