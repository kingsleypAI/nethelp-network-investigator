export type Health = "healthy" | "degraded" | "critical";

export interface Geo {
  region: string | null;
  expectedDc: string | null;
  actualDc: string | null;
  confidence: number;
  method: string;
  note: string | null;
}

export interface Finding {
  kind: string;
  area: string;
  severity: Health | "info";
  confidence: number;
  rootCause: string;
  metrics: Record<string, string | number>;
  firstLossHop?: number;
}

export interface Escalation {
  ready: boolean;
  checks: Record<string, boolean>;
  passed: number;
  total: number;
}

export interface Analysis {
  health: Health;
  rootCause: string;
  confidence: number;
  geo: Geo;
  site: string | null;
  siteSource: string | null;
  findings: Finding[];
  evidence: Record<string, string | number>;
  fixes: { label: string; probability: number }[];
  isp: { name: string; confidence: number; text: string } | null;
  affectedServices: string[];
  customerText: string;
  engineerText: string;
  ticketNotes: string[];
  escalationSummary: string;
  escalation: Escalation;
  enrichedBy?: string;
}

export interface CaseSummary {
  id: number;
  createdAt: string | null;
  site: string;
  siteSource: string | null;
  region: string | null;
  health: Health;
  confidence: number;
  rootCause: string;
  evidenceTypes: string[];
}

export interface SiteGroup {
  site: string;
  count: number;
  worstHealth: Health;
  evidenceTypes: string[];
  cases: CaseSummary[];
}

export interface EvidenceInput {
  name: string;
  text: string;
}
