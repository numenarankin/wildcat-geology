/**
 * The API-number range covering one RRC county.
 *
 * The county code IS the API number's leading three digits, so a county is a
 * contiguous range over `api_number` — which is indexed (`wellbore_api_idx`),
 * while `county_code` is not. This is the difference between an index scan and
 * a 1.37M-row sequential scan on every county filter.
 *
 * Moved out of Wildcat's `scout/focus-where.ts` (Recon map filters), which
 * re-exports it from here.
 */
export function countyApiRange(countyCode: number): [string, string] {
  const c = String(countyCode).replace(/\D/g, "").padStart(3, "0");
  return [`${c}00000`, `${c}99999`];
}
