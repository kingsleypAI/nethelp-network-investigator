import type { Analysis, CaseSummary, EvidenceInput, SiteGroup } from "./types";

// In dev, Vite proxies /api -> backend. In prod, set VITE_API_URL to the backend origin.
const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => req<{ status: string }>("/health"),
  regions: () => req<string[]>("/meta/regions"),
  datacentres: () => req<any[]>("/meta/datacentres"),
  ports: () => req<{ port: string; proto: string; use: string }[]>("/meta/ports"),
  config: () => req<{ app: string; version: string; claudeEnabled: boolean }>("/meta/config"),
  samples: () => req<Record<string, EvidenceInput[]>>("/meta/samples"),

  analyze: (body: { inputs: EvidenceInput[]; regionOverride?: string; siteId?: string; store?: boolean }) =>
    req<{ caseId: number | null; analysis: Analysis }>("/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  cases: () => req<CaseSummary[]>("/cases"),
  groupedCases: () => req<SiteGroup[]>("/cases/grouped"),
  getCase: (id: number) => req<{ summary: CaseSummary; analysis: Analysis }>(`/cases/${id}`),
};
