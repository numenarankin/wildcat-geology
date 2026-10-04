/**
 * Pure, framework-free rendering of a proposed Orion write into a plain-English
 * view a non-technical operator can read — a title, the record's fields as
 * labelled rows, and any batch of rows as a small table. NEVER raw JSON, never
 * tool names or field keys.
 *
 * Extracted from the `ApprovalCard` component so (a) the copy/logic can be unit-
 * tested without React and (b) a Layer-0 conformance test can assert that EVERY
 * write tool has a registered human-readable title (the "70-year-old operator"
 * bar) — `hasRegisteredApprovalTitle`.
 */

/**
 * The argument every approval-gated tool takes for the card's headline: one
 * line, written by the model in the same call, naming the exact record and the
 * change ("Set Roy Corbett 4 casing pressure to 120 psi on Sep 30"). The static
 * titles below only say what KIND of write it is, which is not enough to say
 * yes or no to. Added to each schema by `resilient()` in `tools.ts`, and
 * stripped there before the tool body runs, so no tool ever sees it.
 *
 * The field rows stay under it as the ground truth: the summary is the model's
 * account of the write, the rows are the write.
 */
export const APPROVAL_SUMMARY_KEY = "summary";

/** Plain-English action title for a single-record write, keyed by tool name. */
export const ACTION_TITLES: Record<string, string> = {
  add_well_comment: "Post a field note",
  create_task: "Create a task",
  update_task: "Update a task",
  create_well: "Register a new well",
  update_well: "Update well details",
  create_lease: "Create a lease",
  update_lease: "Update lease details",
  assign_well_to_lease: "Assign a well to a lease",
  assign_tank_to_lease: "Assign a tank to a lease",
  assign_meter_to_lease: "Assign a meter to a lease",
  grant_lease_interest: "Grant an owner interest on a lease",
  update_lease_interest: "Update an interest holding",
  set_operator_interest: "Set the operator's interest on a lease",
  create_meter: "Create a gas meter",
  update_meter: "Update gas meter details",
  record_meter_reading: "Record a gas meter reading",
  update_meter_reading: "Correct a gas meter reading",
  add_meter_wells: "Add wells to a gas meter",
  set_meter_well_allocation: "Set a well's meter allocation %",
  save_meter_allocation: "Save a gas meter's allocation",
  create_gas_campaign: "Create a gas well-test campaign",
  publish_gas_campaign: "Publish a gas well-test campaign",
  add_meter_comment: "Post a note on a gas meter",
  create_injection_well: "Create an injection (SWD) well",
  set_well_type: "Change a well's type",
  update_disposal_reading: "Correct a disposal reading",
  create_water_meter: "Create a water (SWD) meter",
  update_water_meter: "Update water meter details",
  record_swd_meter_reading: "Record a water meter reading",
  update_swd_meter_reading: "Correct a water meter reading",
  create_tank: "Create a tank",
  update_tank: "Update tank details",
  record_tank_reading: "Record a tank gauge reading",
  update_tank_reading: "Correct a tank gauge reading",
  add_tank_comment: "Post a note on a tank",
  add_tank_wells: "Add wells to a tank",
  set_tank_well_allocation: "Set a well's tank allocation %",
  save_tank_allocation: "Save a tank's allocation",
  update_run_ticket: "Correct a run ticket",
  create_battery: "Create a tank battery",
  update_battery: "Update tank battery details",
  save_battery_tanks: "Set a battery's tanks",
  add_battery_wells: "Add wells to a battery",
  set_battery_well_allocation: "Set a well's battery allocation %",
  save_battery_allocation: "Save a battery's allocation",
  create_facility_connection: "Draw a flow connection",
  update_facility_connection: "Change a flow connection",
  save_node_water_split: "Set a node's water split",
  update_production: "Correct a production reading",
  update_well_equipment: "Fix an equipment row",
  create_calendar_event: "Add a calendar event",
  update_calendar_event: "Update a calendar event",
  create_contractor: "Add a contractor",
  update_contractor: "Update a contractor",
  create_service_provider: "Add a service provider",
  update_service_provider: "Update a service provider",
  create_royalty_owner: "Add a royalty owner",
  update_royalty_owner: "Update a royalty owner",
  create_employee: "Add an employee",
  update_employee: "Update an employee",
  create_gatherer: "Add a gatherer",
  update_gatherer: "Update a gatherer",
  create_project: "Create a project",
  set_tank_called_in: "Call in a tank for pickup",
  send_support_message: "Send a message to support",
  mark_support_thread_read: "Mark a support thread read",
  send_team_message: "Send a message to a coworker",
  rename_team_conversation: "Rename a group conversation",
  create_folder: "Create a folder",
  create_inventory_item: "Add an inventory item",
  update_inventory_item: "Update an inventory item",
  create_transaction: "Record a ledger entry",
  update_transaction: "Update a ledger entry",
  remember: "Remember this",
  set_meter_takeaway: "Set where the gas goes",
  create_note: "Save a note",
  create_document: "Create a document",
  edit_document: "Edit a document",
};

/** Batch writes: the array field, plus the verb + singular noun for the title. */
export const BATCH_ACTIONS: Record<
  string,
  { key: string; verb: string; noun: string }
> = {
  record_production: {
    key: "readings",
    verb: "Record",
    noun: "production reading",
  },
  add_well_equipment: { key: "fields", verb: "Add", noun: "equipment item" },
  add_well_service: { key: "rows", verb: "Log", noun: "service record" },
  record_run_ticket: { key: "tickets", verb: "Log", noun: "run ticket" },
  record_downtime: { key: "events", verb: "Log", noun: "downtime period" },
  record_well_test: { key: "tests", verb: "Record", noun: "well test" },
  record_disposal_readings: {
    key: "readings",
    verb: "Record",
    noun: "disposal reading",
  },
  set_raster_log_depths: { key: "anchors", verb: "Save", noun: "log depth mark" },
};

/**
 * Does this tool have a hand-written, plain-English approval title? Every write
 * tool MUST — a Layer-0 test enforces it, so a new write tool can't ship with an
 * approval card a field operator can't read. (Field labels fall back to
 * auto-humanization, which is fine; the title is the curated part.)
 */
export function hasRegisteredApprovalTitle(name: string): boolean {
  return name in ACTION_TITLES || name in BATCH_ACTIONS;
}

/** Friendlier labels than a raw key name; anything unlisted is auto-humanized. */
const LABELS: Record<string, string> = {
  meters: "Meters",
  takeaway: "Delivered to",
  gasTakeaway: "Delivered to",
  body: "Note",
  depthFt: "Depth (ft)",
  row: "Pixel row",
  name: "Name",
  title: "Title",
  method: "Method",
  ticketNo: "Ticket #",
  ticketType: "Type",
  grossBbls: "Gross (bbl)",
  netBbls: "Corrected (bbl)",
  apiGravity: "API gravity",
  bsW: "BS&W (%)",
  transporter: "Transport company",
  oilProduction: "Oil (bbl)",
  gasProduction: "Gas (MCF)",
  saltWater: "Water (bbl)",
  oilStock: "Oil stock (bbl)",
  oilSales: "Oil sales (bbl)",
  volumeMcf: "Gas (MCF)",
  eventType: "Type",
  startDate: "From",
  endDate: "To",
  daysApplied: "Days offline",
  testDate: "Test date",
  durationDays: "Duration (days)",
  startAt: "Start",
  endAt: "End",
  oilBbls: "Oil (bbl)",
  gasMcf: "Gas (MCF)",
  waterBbls: "Water (bbl)",
  preTestShutInDays: "Prior shut-in (days)",
  dateDrilled: "Drilled",
  categoryCode: "Category code",
  invoiceNumber: "Invoice #",
  counterparty: "Counterparty",
  allDay: "All day",
  unitCost: "Unit cost",
  wellIds: "Wells",
  content: "Content",
};

/** Money-valued keys get a $ and thousands separators. */
const MONEY_KEYS = new Set([
  "amount",
  "cost",
  "unitCost",
  "price",
  "grossValue",
  "netValue",
  "deducts",
  "taxes",
  "fees",
  "value",
  "lastPayment",
]);

/**
 * Ids the conversation already establishes — noise (esp. UUIDs) in the card. Any
 * key that IS "id" or ends in "Id" (wellId, leaseId, batteryId, readingId,
 * campaignId, ownerId, …) is hidden generically, so a new tool can never surface a
 * raw uuid to the operator just because its param wasn't added to a list.
 */
function isHiddenKey(key: string): boolean {
  return key === "id" || /Id$/.test(key) || key === APPROVAL_SUMMARY_KEY;
}

/**
 * A LIST of ids (`meterIds`, `wellIds`) is the worst version of the same
 * problem: twenty uuids filled a card nobody could read. But dropping the row
 * is worse still — it is the only thing saying HOW MANY records the write
 * touches, and a card that cannot tell one meter from twenty is not consent.
 * So the ids go and the count stays.
 *
 * A tool whose user needs to see WHICH records it means takes their names
 * instead (`set_meter_takeaway`), and then this never fires.
 */
function isIdList(key: string, v: unknown): v is unknown[] {
  return /Ids$/.test(key) && Array.isArray(v);
}

function isEmpty(v: unknown): boolean {
  return v == null || v === "";
}

export function humanizeKey(key: string): string {
  if (LABELS[key]) return LABELS[key];
  const spaced = key
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/_/g, " ")
    .trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function humanizeToolName(name: string): string {
  const spaced = name.replace(/_/g, " ").trim();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function formatMoney(n: number): string {
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

/**
 * Values that are a code in the database and a phrase in the field. The card is
 * read by the person deciding, so it says what the setting MEANS.
 */
const VALUE_WORDS: Record<string, Record<string, string>> = {
  meters: { all: "Every gas meter" },
  takeaway: {
    transmission: "A transmission line (RRC gas code 2)",
    plant: "A processing plant (RRC gas code 3)",
  },
  gasTakeaway: {
    transmission: "A transmission line (RRC gas code 2)",
    plant: "A processing plant (RRC gas code 3)",
  },
};

/** Render one value as readable text (— for empty). */
function formatValue(key: string, v: unknown): string {
  if (v == null || v === "") return "—";
  if (typeof v === "boolean") return v ? "Yes" : "No";
  if (Array.isArray(v)) {
    if (v.length === 0) return "—";
    if (v.every((x) => typeof x !== "object" || x == null)) {
      // Every one of them, however many. This is the line that says WHAT the
      // write touches, and a list the operator cannot finish reading is a list
      // they cannot say no to. Truncating it was the whole bug.
      const words = VALUE_WORDS[key];
      return v.map((x) => words?.[String(x)] ?? String(x)).join(", ");
    }
    return `${v.length} item${v.length === 1 ? "" : "s"}`;
  }
  if (typeof v === "string" && VALUE_WORDS[key]?.[v]) return VALUE_WORDS[key][v];
  if (typeof v === "number") {
    return MONEY_KEYS.has(key) ? formatMoney(v) : v.toLocaleString();
  }
  if (typeof v === "string") {
    return v.length > 240 ? `${v.slice(0, 240)}…` : v;
  }
  const s = JSON.stringify(v);
  return s.length > 120 ? `${s.slice(0, 120)}…` : s;
}

export interface FieldRow {
  label: string;
  value: string;
}

export interface ApprovalView {
  title: string;
  fields: FieldRow[];
  table?: { columns: string[]; rows: string[][]; total: number };
}

const MAX_TABLE_ROWS = 8;
const MAX_TABLE_COLS = 6;

/** Scalar (non-array) fields of an object as labelled rows, ids + blanks dropped. */
function scalarFields(
  obj: Record<string, unknown>,
  skip: Set<string>,
): FieldRow[] {
  return Object.entries(obj)
    .filter(([k, v]) => !skip.has(k) && !isHiddenKey(k) && !isEmpty(v))
    .map(([k, v]) =>
      isIdList(k, v)
        ? {
            label: humanizeKey(k.replace(/Ids$/, "s")),
            value: `${v.length} selected`,
          }
        : { label: humanizeKey(k), value: formatValue(k, v) },
    );
}

/** Build a compact table from a batch of record objects. */
function buildTable(items: Record<string, unknown>[]): {
  columns: string[];
  rows: string[][];
  total: number;
} {
  const keys: string[] = [];
  for (const it of items) {
    for (const k of Object.keys(it)) {
      if (!isHiddenKey(k) && !keys.includes(k)) keys.push(k);
    }
  }
  // Keep only keys that carry a value in at least one row, capped for width.
  const dataKeys = keys
    .filter((k) => items.some((it) => !isEmpty(it[k])))
    .slice(0, MAX_TABLE_COLS);
  const rows = items
    .slice(0, MAX_TABLE_ROWS)
    .map((it) => dataKeys.map((k) => formatValue(k, it[k])));
  // Header row is humanized for display ("Date", "Gas (MCF)"), keyed on raw keys.
  const columns = dataKeys.map((k) => humanizeKey(k));
  return { columns, rows, total: items.length };
}

/**
 * The model's summary, made to sit on one or two lines of a card: whitespace
 * and newlines collapsed, markdown and wrapping quotes dropped, em dashes made
 * commas, no trailing period, first letter capitalized. Blank comes back
 * undefined so the static title takes over.
 */
export function cleanSummary(raw: unknown): string | undefined {
  if (typeof raw !== "string") return undefined;
  const s = raw
    .replace(/[*`]+/g, "")
    .replace(/\s+/g, " ")
    .replace(/\s*\u2014\s*/g, ", ")
    .trim()
    .replace(/^["'\u201c\u2018]+|["'\u201d\u2019]+$/g, "")
    .replace(/[.\s]+$/, "")
    .trim();
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : undefined;
}

/** Turn a raw tool call into a plain-English, non-technical view. */
export function describeApproval(name: string, input: unknown): ApprovalView {
  const obj =
    input && typeof input === "object"
      ? (input as Record<string, unknown>)
      : {};
  const summary = cleanSummary(obj[APPROVAL_SUMMARY_KEY]);

  const batch = BATCH_ACTIONS[name];
  const batchVal = batch ? obj[batch.key] : undefined;
  if (batch && Array.isArray(batchVal) && batchVal.length > 0) {
    const items = batchVal as Record<string, unknown>[];
    const n = items.length;
    return {
      title: summary ?? `${batch.verb} ${n} ${batch.noun}${n === 1 ? "" : "s"}`,
      fields: scalarFields(obj, new Set([batch.key])),
      table: buildTable(items),
    };
  }

  return {
    title: summary ?? ACTION_TITLES[name] ?? humanizeToolName(name),
    fields: scalarFields(obj, new Set()),
  };
}
