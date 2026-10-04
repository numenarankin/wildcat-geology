import "server-only";
import { setGeologyHost, type GeologyHost, type RrcLeaseKey } from "@/lib/host";
import { getSupabaseServer, hasSupabase } from "@/lib/supabase/server";
import { hasRrcDb, rrcQuery } from "@/lib/scout/rrc-db";
import { toPdqDistrict } from "@/lib/scout/rrc-districts";

/**
 * The geology app's host: the engine's ports, filled from the signed-in user's
 * Wildcat account.
 *
 * Every read runs on the user's own Supabase session, so RLS scopes files,
 * wells and leases to their org exactly as it does in Wildcat. There is no
 * service key here, which is why a LAS file whose text is only in storage is
 * downloaded as the user too.
 *
 * Importing this module installs the host. The chat route imports it, so it is
 * in place before any geology call.
 */

/** Wildcat's private file bucket. */
const BUCKET = "files";

/** The last 8 digits of a stored API number, or null when there are fewer. */
function api8(raw: string | null | undefined): string | null {
  const digits = (raw ?? "").replace(/\D/g, "");
  return digits.length >= 8 ? digits.slice(-8) : null;
}

const wildcatHost: GeologyHost = {
  auth: {
    async assertSignedIn() {
      if (!hasSupabase()) throw new Error("Not signed in");
      const sb = await getSupabaseServer();
      const {
        data: { user },
      } = await sb.auth.getUser();
      if (!user) throw new Error("Not signed in");
    },
  },

  files: {
    // Wildcat's `getLasFiles` (lib/kb/files.ts).
    async listLas() {
      if (!hasSupabase()) return [];
      const sb = await getSupabaseServer();
      const { data, error } = await sb
        .from("files")
        .select("id, name")
        .ilike("name", "%.las")
        .order("name");
      if (error) throw new Error(`listLas: ${error.message}`);
      return (data ?? []).map((f) => ({ id: f.id as string, name: f.name as string }));
    },

    // Wildcat's `loadText` (lib/kb/structured.ts).
    async loadText(fileId) {
      if (!hasSupabase()) return null;
      const sb = await getSupabaseServer();
      const { data: file } = await sb
        .from("files")
        .select("name, content, pdf_native_content, derived_content, storage_key")
        .eq("id", fileId)
        .maybeSingle();
      if (!file) return null;
      let text = (
        file.content ||
        file.pdf_native_content ||
        file.derived_content ||
        ""
      ).trim();
      if (!text && file.storage_key) {
        const { data: blob } = await sb.storage.from(BUCKET).download(file.storage_key);
        if (blob) text = (await blob.text()).trim();
      }
      return { name: file.name as string, text };
    },
  },

  wells: {
    // Wildcat's `storedApi` (lib/rrc/link.ts).
    async rrcApi(wellId) {
      if (!hasSupabase()) return null;
      const sb = await getSupabaseServer();
      const { data } = await sb
        .from("wells")
        .select("api_well_no")
        .eq("id", wellId)
        .maybeSingle<{ api_well_no: string | null }>();
      return api8(data?.api_well_no);
    },

    // The first (dominant) answer of Wildcat's `resolveLeaseKeys`: the stored
    // key when a human confirmed one, else the record most of the lease's wells
    // sit on in the mirror.
    async rrcLeaseKey(leaseId) {
      if (!hasSupabase()) return null;
      const sb = await getSupabaseServer();
      const { data: stored } = await sb
        .from("leases")
        .select("rrc_lease_no, rrc_district, rrc_oil_gas_code")
        .eq("id", leaseId)
        .maybeSingle<{
          rrc_lease_no: string | null;
          rrc_district: string | null;
          rrc_oil_gas_code: string | null;
        }>();
      if (stored?.rrc_lease_no && stored.rrc_district && stored.rrc_oil_gas_code) {
        return {
          oilGasCode: stored.rrc_oil_gas_code as "O" | "G",
          districtNo: stored.rrc_district,
          leaseNo: stored.rrc_lease_no,
        };
      }
      if (!hasRrcDb()) return null;

      const { data: wells } = await sb
        .from("wells")
        .select("api_well_no")
        .eq("lease_id", leaseId)
        .not("api_well_no", "is", null);
      const apis = (wells ?? [])
        .map((w) => api8(w.api_well_no as string | null))
        .filter((a): a is string => a !== null);
      if (apis.length === 0) return null;

      const rows = await rrcQuery<{
        oil_gas_code: "O" | "G" | null;
        district: string | null;
        lease_number: string | null;
      }>(
        `select oil_gas_code, district, lease_number, count(*) as wells
           from rrc.wellbore
          where api_number = any($1)
            and on_schedule = 'Y'
            and lease_number is not null
          group by 1, 2, 3
          order by wells desc`,
        [apis]
      );
      for (const hit of rows) {
        if (!hit.oil_gas_code || !hit.district || !hit.lease_number) continue;
        // `rrc.wellbore` reports the real-world district label; `rrc.lease`
        // keys on PDQ's internal code.
        const districtNo = toPdqDistrict(hit.district);
        if (!districtNo) continue;
        const key: RrcLeaseKey = {
          oilGasCode: hit.oil_gas_code,
          districtNo,
          leaseNo: hit.lease_number,
        };
        return key;
      }
      return null;
    },
  },
};

setGeologyHost(wildcatHost);
