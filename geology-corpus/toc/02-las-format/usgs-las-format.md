# usgs-las-format

**Covers:** A reference note on the LAS (Log ASCII Standard) well-log file format, describing its required sections and the differences between LAS 2.0 and 3.0.

**Authoritative for:** structure of a LAS file and which sections are mandatory, contents and purpose of the ~VERSION section, contents and purpose of the ~WELL section (well identification/header parameters), high-level distinction between LAS 2.0 and LAS 3.0, who defines and maintains the standard (CWLS)

**Not good for:** full field-by-field specification or delimiter/wrapping rules of the standard, curve mnemonic dictionaries or tool-specific channel naming conventions, petrophysical interpretation, log QC, or calculation of properties from curves, DLIS, LIS, ASCII vendor formats, or database schemas other than LAS, parsing code, software implementation details, or library documentation, well-specific data, log examples, or basin/field results

**Scope:** Format documentation only, not geology or data: a short overview keyed to LAS 2.0 with mention of 3.0, framed around USGS/CWLS practice. Use it to understand file anatomy before reading logs; consult the official CWLS specification for authoritative syntax details and any post-3.0 revisions.

_2 segments._

---

### LAS format overview and required sections (LAS 2.0 vs 3.0)  `02-las-format/usgs-las-format#1` (chars 151-4233)
Answers: What is the LAS file format and who maintains it? · What sections are required in a LAS 2.0 file? · What does the ~VERSION section contain? · What does the ~WELL section contain? · What's the difference between LAS 2.0 and LAS 3.0? · Are LAS 3.0 files backward compatible with LAS 2.0? · What software can validate that a LAS file meets the spec? · Which version of LAS Certify should I use? · Where do null values and step interval get defined in a LAS file?
Entities: Log ASCII Standard, LAS, Canadian Well Logging Society, CWLS, LAS 2.0, LAS 3.0, ~VERSION, ~WELL, ~CURVE, ~PARAMETER, ~OTHER, ~ASCII, LAS Certify, LAS Certify 2.2.2, LAS Certify 2.4.14.0, Schlumberger, Windows 10, National Geological and Geophysical Data Preservation Program
