# rrc-g10-tape-user-manual

**Covers:** User manual and record-layout documentation for the Railroad Commission of Texas Form G-10 (Gas Well Status Report) magnetic tape dataset (GSE10), covering tape physical specs, the WLW619A1 COBOL record layout, and a field-by-field data dictionary.

**Authoritative for:** byte positions, lengths, and COBOL PIC clauses of fields in the 130-byte G-10 tape record, record length, block size, tape density, and character set of the GSE10 dataset, meaning, units, and coding of G-10 fields such as daily gas volume, condensate, shut-in wellhead pressure, and test dates, valid RRC district codes and date formats as used in the G-10 file, how to parse or load legacy RRC G-10 gas well status tape data

**Not good for:** actual gas production or deliverability values for any specific well or field (this is a format spec, not a data set), geological, stratigraphic, or reservoir interpretation, gas well deliverability testing theory, back-pressure/flow-after-flow test methods, or IPR calculation, oil well or other RRC form layouts (P-1, W-2, G-1, etc.) beyond G-10, regulatory allowable/proration rules or how G-10 filings are adjudicated, modern RRC online query systems, APIs, or current-format data downloads

**Scope:** Texas only, Railroad Commission of Texas administrative reporting; legacy mainframe magnetic-tape era (fixed-length EBCDIC/COBOL records), so field definitions and district codes reflect the vintage of that tape release rather than present-day RRC data services. Applies to gas well status reporting, not oil wells or non-Texas jurisdictions.

_3 segments._

---

### RRC Form G-10 Gas Well Status Report tape — title page, TOC, and general/physical tape specs  `09-gas-deliverability/rrc-g10-tape-user-manual#0` (chars 0-2857)
Answers: What is on the Railroad Commission of Texas G-10 gas well status tape? · What record types are in the Gas Well Status Report (Form G-10) file? · What is the record length and block size of the GSE10 dataset? · What tape density and character set does the RRC G-10 tape use? · What does a cycle date mean in the RRC oil and gas system? · Which publication number covers the G-10 tape user manual?
Entities: RAILROAD COMMISSION OF TEXAS, TEXAS NATURAL GAS INFORMATION SYSTEM, GAS WELL STATUS REPORT (FORM G-10), GSA018, GAS SCHEDULE SYSTEMS, IBM 2003-116, GSE10, EBCDIC, AUSTIN, TEXAS 78711-2967, COBOL FILE LAYOUT

### G-10 tape record layout (WLW619A1) field positions and COBOL picture clauses  `09-gas-deliverability/rrc-g10-tape-user-manual#1` (chars 2857-5599)
Answers: What is the record layout of the RRC Form G-10 tape file? · What byte position is the shut-in wellhead pressure in the G-10 record? · How long is a G-10 tape record? · What are the field names and PIC clauses in the G10-TAPE-RECORD? · Where do I find daily gas, condensate, and water volumes in the G-10 file? · What changed in the G-10 file for the Year 2000 conversion?
Entities: WLW619A1, FORM G-10 RECORDS, G10-TAPE-RECORD, G10-ID, G10-DST, G10-RRCID, G10-TST-DATE, G10-DLY-GAS, G10-DLY-COND, G10-DLY-WTR, G10-SIWH-PRESS, G10-POTE, G10-SHUT-CD, G10-GAS-GRAV, G10-CON-GRAV, G10-RATIO, G10-FLOW-PRESS, G10-BHP, G10-SHUT-PRESS, G10-LATE-TST, G10-CORR-CD, G10-SHUT-DATE, G10-COMN-CD, G10-OPR, G10-WH-PRES-TEST-DATE, G10-EFF-DATE, FILLER, RECORD LENGTH: 130 BYTES, YEAR 2000 CONVERSION

### G-10 segment field dictionary (GSE10 record, 130 bytes)  `09-gas-deliverability/rrc-g10-tape-user-manual#2` (chars 5599-9830)
Answers: What does each field in the RRC G-10 tape record mean? · What are the valid RRC district codes in the G-10 file? · What units are G10-DLY-GAS, condensate, and pressures reported in? · What is the date format for G-10 test date fields? · What gas/liquid ratio defines a gas well in Texas? · What is the difference between G10-SIWH-PRESS, G10-FLOW-PRESS, and G10-SHUT-PRESS? · What is the RRC identification number for a gas well? · What does the G-10 late test or corrected code flag indicate? · How long is the GSE10 record and what is the tape ID for G-10 records?
Entities: PROD.COPYLIB(WLW619A1), WELLROOT G-10 SEGMENT, GSE10, G10-ID, G10-DST, G10-RRCID, G10-TST-DATE, G10-DLY-GAS, G10-DLY-COND, G10-DLY-WTR, G10-SIWH-PRESS, G10-POTE, G10-SHUT-CD, G10-GAS-GRAV, G10-CON-GRAV, G10-RATIO, G10-FLOW-PRESS, G10-BHP, G10-SHUT-PRESS, G10-LATE-TST, G10-CORR-CD, G10-SHUT-DATE, G10-COMN-CD, G10-OPR, G10-WH-PRES-TEST-DATE, G10-EFF-DATE, RRC, MCF, BBL, PSI, MMDDCCYY, 7B, 7C, 8A
