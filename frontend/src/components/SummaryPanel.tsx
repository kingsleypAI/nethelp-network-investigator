import type { Analysis } from "../types";

const COLORS: Record<string, string> = { healthy: "#34d17a", degraded: "#ffb02e", critical: "#ff4d4d" };

export default function SummaryPanel({ r }: { r: Analysis | null }) {
  if (!r) {
    return (
      <div className="panel" id="right">
        <div className="phead"><span className="dot" />ISSUE SUMMARY</div>
        <div className="pbody">
          <div className="empty" style={{ fontSize: 11 }}><div><div className="big">◈</div>AWAITING<br />ANALYSIS</div></div>
        </div>
      </div>
    );
  }
  const c = COLORS[r.health];
  const circ = 2 * Math.PI * 52;
  const off = circ * (1 - r.confidence / 100);
  return (
    <div className="panel" id="right">
      <div className="phead"><span className="dot" />ISSUE SUMMARY</div>
      <div className="pbody">
        <div className="gauge">
          <svg className="ring" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="52" fill="none" stroke="#1f2c3a" strokeWidth="10" />
            <circle cx="60" cy="60" r="52" fill="none" stroke={c} strokeWidth="10" strokeLinecap="round"
              strokeDasharray={circ} strokeDashoffset={off} transform="rotate(-90 60 60)"
              style={{ filter: `drop-shadow(0 0 6px ${c})` }} />
            <text x="60" y="56" textAnchor="middle" fill="#fff" fontSize="22" fontFamily="monospace" fontWeight="700">{r.confidence}%</text>
            <text x="60" y="74" textAnchor="middle" fill="#7d909f" fontSize="9" fontFamily="monospace" letterSpacing="2">CONFIDENCE</text>
          </svg>
        </div>
        <div className="summline"><span className="k">SITE / CUSTOMER</span><span className="v">{r.site || "Unidentified"}</span></div>
        <div className="summline"><span className="k">SEVERITY</span><span className="v"><span className={"badge " + r.health}>{r.health.toUpperCase()}</span></span></div>
        <div className="summline"><span className="k">REGION</span><span className="v">{r.geo.region || "—"}</span></div>
        <div className="summline"><span className="k">DATACENTRE</span><span className="v">{r.geo.expectedDc || "—"}</span></div>
        <div className="summline"><span className="k">AFFECTED</span><span className="v">{r.affectedServices.join(", ") || "None"}</span></div>
        <div className="summline"><span className="k">ESCALATE</span><span className="v" style={{ color: r.escalation.ready ? "#34d17a" : "#ffb02e" }}>{r.escalation.ready ? "READY" : "NOT READY"}</span></div>
        <div style={{ marginTop: 12 }} className="lbl">ROOT CAUSE</div>
        <div style={{ fontSize: 12, lineHeight: 1.5, marginTop: 4, color: "#fff" }}>{r.rootCause}</div>
        <div style={{ marginTop: 14 }} className="lbl">TOP FIX</div>
        <div style={{ fontSize: 12, marginTop: 4, color: "var(--amber)" }}>
          {r.fixes[0] ? `${r.fixes[0].label} (${r.fixes[0].probability}%)` : "—"}
        </div>
      </div>
    </div>
  );
}
