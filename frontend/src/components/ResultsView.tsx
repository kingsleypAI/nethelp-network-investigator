import { useEffect, useState, type ReactNode } from "react";
import type { Analysis } from "../types";

const HMAP: Record<string, [string, string, string]> = {
  healthy: ["🟢", "h-healthy", "HEALTHY"],
  degraded: ["🟡", "h-degraded", "DEGRADED"],
  critical: ["🔴", "h-critical", "CRITICAL"],
};

function guessType(text: string, name = "") {
  name = name.toLowerCase();
  if (name.includes("pingplotter") || /pingplotter/i.test(text)) return "PINGPLOTTER";
  if (/loss%\s+snt|wrst|stdev|\bmtr\b/i.test(text)) return "MTR";
  if (/^\s*target\s*:/im.test(text) && /loss\s*%/i.test(text)) return "PINGPLOTTER";
  if (/utility test|sbc|reachability/i.test(text)) return "8x8 UTIL";
  if (/traceroute|\bhop\b|\bms\b/i.test(text)) return "TRACE";
  if (/ping|packets/i.test(text)) return "PING";
  return "LOG";
}

function vClass(v: string | number) {
  const s = String(v);
  if (/blocked|fail|critical|warning/i.test(s)) return "bad";
  if (/ok|pass|open/i.test(s)) return "ok";
  return "";
}

function copy(text: string, toast: (m: string) => void) {
  navigator.clipboard.writeText(text).then(() => toast("Copied to clipboard"));
}

export default function ResultsView({ r, toast }: { r: Analysis | null; toast: (m: string) => void }) {
  const [showRaw, setShowRaw] = useState(false);
  const [reviewed, setReviewed] = useState(false);
  useEffect(() => { setShowRaw(false); setReviewed(false); }, [r]);

  if (!r) {
    return (
      <div className="empty"><div><div className="big">◳</div>NO INVESTIGATION RUN YET<br />
        <small>Add evidence and press RUN INVESTIGATION</small></div></div>
    );
  }
  const h = HMAP[r.health];
  const openRaw = () => {
    setShowRaw(true);
    setTimeout(() => document.getElementById("rawSec")?.scrollIntoView({ behavior: "smooth", block: "start" }), 30);
  };
  const dcStatus = r.geo.actualDc && r.geo.actualDc !== r.geo.expectedDc ? "WARNING" : "PASS";
  const ticket = r.ticketNotes.map((n) => "• " + n).join("\n");

  return (
    <div>
      <div className={"health-banner " + h[1]}>
        <span className="scan" /><span className="hicon">{h[0]}</span>
        <div>
          <h2>NETWORK {h[2]}</h2>
          <div style={{ fontFamily: "var(--mono)", fontSize: 11, letterSpacing: 1, opacity: 0.85, margin: "2px 0 4px" }}>
            SITE: {r.site || "Unidentified"}{r.siteSource ? ` · ${r.siteSource}` : ""}
            {r.enrichedBy ? ` · explanation enriched by ${r.enrichedBy}` : ""}
          </div>
          <p>{r.rootCause}</p>
        </div>
        {reviewed && <span className="reviewed-stamp">✓ REVIEWED BY ENGINEER</span>}
      </div>

      {r.reviewFlag?.needed && (
        <div className="review-callout">
          <div className="rc-head">⚠ MANUAL REVIEW RECOMMENDED</div>
          <div className="rc-body">
            The engine is not fully certain. Please open the raw evidence and confirm before acting:
            <ul>{r.reviewFlag.reasons.map((x) => <li key={x}>{x}</li>)}</ul>
          </div>
          <button className="btn" onClick={openRaw}>🔍 REVIEW RAW EVIDENCE</button>
        </div>
      )}

      <Sec title="◈ ROOT CAUSE"><div className="rootcause">{r.rootCause}</div></Sec>

      {Object.keys(r.evidence).length > 0 && (
        <Sec title="▤ EVIDENCE">
          <div className="metrics">
            {Object.entries(r.evidence).map(([k, v]) => (
              <div className="metric" key={k}>
                <div className="k">{k}</div>
                <div className={"v " + vClass(v)}>{v}</div>
              </div>
            ))}
          </div>
        </Sec>
      )}

      {r.geo.region && (
        <Sec title="⌖ GEO / DATACENTRE">
          <div className="metrics">
            <Metric k="Detected Region" v={r.geo.region} />
            <Metric k="Method" v={r.geo.method} small />
            <Metric k="Expected DC" v={r.geo.expectedDc || "—"} />
            <Metric k="Actual DC" v={r.geo.actualDc || "—"} cls={dcStatus === "WARNING" ? "warn" : "ok"} />
          </div>
        </Sec>
      )}

      {r.isp && (
        <Sec title="📡 ISP PATTERN">
          <div className="rootcause" style={{ fontSize: 13, color: "var(--amber)" }}>
            {r.isp.text} <span style={{ color: "var(--dim)" }}>(confidence {r.isp.confidence}%)</span>
          </div>
        </Sec>
      )}

      {r.fixes.length > 0 && (
        <Sec title="★ MOST LIKELY FIXES (RANKED)">
          {r.fixes.map((f) => (
            <div className="fixrow" key={f.label}>
              <span className="name">{f.label}</span>
              <span className="fixbar"><i style={{ width: `${f.probability}%` }} /></span>
              <span className="pct">{f.probability}%</span>
            </div>
          ))}
        </Sec>
      )}

      <Sec title="⚒ ENGINEER FINDINGS"><div className="rootcause" style={{ fontSize: 12.5 }}>{r.engineerText}</div></Sec>

      <Sec title="◎ CONFIDENCE SCORE">
        <div className="confwrap">
          <div className="confbar"><i style={{ width: `${r.confidence}%` }} /></div>
          <div className="confnum">{r.confidence}%</div>
        </div>
      </Sec>

      <Sec title="⇪ ESCALATION READINESS">
        <div className="escbox">
          {Object.entries(r.escalation.checks).map(([k, v]) => (
            <div className="esccheck" key={k}>
              <span className={"mk " + (v ? "yes" : "no")}>{v ? "✓" : "✕"}</span>{k}
            </div>
          ))}
        </div>
        <div className={"escverdict " + (r.escalation.ready ? "go" : "nogo")}>
          READY TO ESCALATE: {r.escalation.ready ? "YES" : "NO"} &nbsp;·&nbsp; {r.escalation.passed}/{r.escalation.total} CRITERIA MET
        </div>
      </Sec>

      <Sec title="⧉ ONE-CLICK COPY">
        <div className="copygrid">
          <button className="btn" onClick={() => copy(r.customerText, toast)}>⧉ Copy Customer Response</button>
          <button className="btn" onClick={() => copy(ticket, toast)}>⧉ Copy Ticket Notes</button>
          <button className="btn full" onClick={() => copy(r.escalationSummary, toast)}>⧉ Copy Escalation Summary</button>
        </div>
        <pre className="out">{r.customerText}</pre>
        <pre className="out">{ticket}</pre>
        <pre className="out">{r.escalationSummary}</pre>
      </Sec>

      <div className="sec" id="rawSec">
        <h3 style={{ color: "var(--blue)" }}>🔍 RAW EVIDENCE · MANUAL REVIEW</h3>
        <div className="c">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <span className="lbl">
              Confirm the engine read the data correctly ({r.rawInputs.length} source{r.rawInputs.length === 1 ? "" : "s"})
            </span>
            <button className="btn sm" onClick={() => setShowRaw((s) => !s)}>SHOW / HIDE</button>
          </div>
          {showRaw && (
            <div style={{ marginTop: 10 }}>
              {r.rawInputs.length ? r.rawInputs.map((f) => (
                <div className="raw-item" key={f.name}>
                  <div className="raw-name">▤ {f.name} <span className="tag">{guessType(f.text, f.name)}</span></div>
                  <pre className="out" style={{ maxHeight: 200 }}>{f.text || "<empty>"}</pre>
                </div>
              )) : <div className="lbl">No raw text captured for this case.</div>}
              <button className="btn" style={{ marginTop: 10 }} disabled={reviewed}
                onClick={() => { setReviewed(true); toast("Marked as manually reviewed"); }}>
                {reviewed ? "✓ REVIEWED" : "✓ MARK AS MANUALLY REVIEWED"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Sec({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="sec">
      <h3>{title}</h3>
      <div className="c">{children}</div>
    </div>
  );
}

function Metric({ k, v, cls, small }: { k: string; v: string | number; cls?: string; small?: boolean }) {
  return (
    <div className="metric">
      <div className="k">{k}</div>
      <div className={"v " + (cls || "")} style={small ? { fontSize: 11 } : undefined}>{v}</div>
    </div>
  );
}
