import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Analysis, EvidenceInput } from "../types";
import ResultsView from "./ResultsView";

function guessType(text: string, name = "") {
  name = name.toLowerCase();
  if (name.includes("pingplotter") || /pingplotter/i.test(text)) return "PINGPLOTTER";
  if (/loss%\s+snt|wrst|stdev|\bmtr\b/i.test(text)) return "MTR";
  if (/^\s*target\s*:/im.test(text) && /loss\s*%/i.test(text)) return "PINGPLOTTER";
  if (/utility test|sbc|reachability|"sbc"|"reachability"/i.test(text)) return "8x8 UTIL";
  if (/traceroute|\bhop\b|\bms\b/i.test(text)) return "TRACE";
  if (/ping|packets/i.test(text)) return "PING";
  try { const j = JSON.parse(text); if (j && (j.region || j.dns || j.ports || j.sbc)) return "8x8 UTIL"; return "JSON"; } catch { /* */ }
  return "LOG";
}

interface Props {
  regions: string[];
  samples: Record<string, EvidenceInput[]>;
  result: Analysis | null;
  onResult: (a: Analysis) => void;
  log: (m: string, cls?: string) => void;
  toast: (m: string) => void;
}

export default function Workspace({ regions, samples, result, onResult, log, toast }: Props) {
  const [tab, setTab] = useState<"input" | "results">("input");
  const [files, setFiles] = useState<EvidenceInput[]>([]);
  const [paste, setPaste] = useState("");
  const [site, setSite] = useState("");
  const [region, setRegion] = useState("");
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { if (result) setTab("results"); }, [result]);

  function addFiles(list: FileList | null) {
    if (!list) return;
    Array.from(list).forEach((f) => {
      const reader = new FileReader();
      reader.onload = () => {
        setFiles((prev) => [...prev, { name: f.name, text: String(reader.result) }]);
        log(`Ingested ${f.name} (${f.size} bytes)`, "ok");
      };
      reader.readAsText(f);
    });
  }

  async function run() {
    const inputs = [...files];
    if (paste.trim()) inputs.push({ name: "pasted-input", text: paste.trim() });
    if (!inputs.length) { log("No evidence supplied — investigation aborted.", "err"); toast("Add evidence first"); return; }
    setBusy(true);
    setTab("results");
    const steps: [string, string][] = [
      [`Reading ${inputs.length} evidence source(s)…`, "info"],
      ["Parsing traceroute / MTR / ping tables…", ""],
      ["Resolving region & expected datacentre…", "info"],
      ["Running VoIP / DNS / routing / firewall detectors…", ""],
      ["Correlating evidence & ranking root cause…", "info"],
    ];
    for (const [m, c] of steps) { log(m, c); await new Promise((r) => setTimeout(r, 150)); }
    try {
      const res = await api.analyze({ inputs, regionOverride: region || undefined, siteId: site || undefined });
      const a = res.analysis;
      log(`ROOT CAUSE → ${a.rootCause}`, a.health === "critical" ? "err" : a.health === "degraded" ? "warn" : "ok");
      log(`Confidence ${a.confidence}% · Escalation ${a.escalation.ready ? "READY" : "NOT READY"} · case #${res.caseId}`, "head");
      onResult(a);
    } catch (e) {
      log("Backend error: " + (e as Error).message, "err");
      toast("Analysis failed — is the backend running?");
    } finally {
      setBusy(false);
    }
  }

  function loadSample(name: string) {
    setFiles(samples[name].map((f) => ({ ...f })));
    setPaste("");
    log("Loaded sample case: " + name, "info");
  }

  function clearAll() {
    setFiles([]); setPaste(""); setSite(""); setRegion("");
    log("Workspace cleared.", "warn");
  }

  return (
    <>
      <div className="tabbar">
        <div className={"tab" + (tab === "input" ? " active" : "")} onClick={() => setTab("input")}>◰ EVIDENCE INTAKE</div>
        <div className={"tab" + (tab === "results" ? " active" : "")} onClick={() => setTab("results")}>◳ INVESTIGATION RESULTS</div>
      </div>

      {tab === "input" ? (
        <div style={{ padding: 12 }}>
          <div className="lbl" style={{ marginBottom: 6 }}>1 · Site / Customer ID (so you can pinpoint whose test it is)</div>
          <div className="row" style={{ marginBottom: 14 }}>
            <input type="text" value={site} onChange={(e) => setSite(e.target.value)}
              placeholder="e.g. Acme Corp · London  (blank = auto-detect from diagnostics)"
              style={{ flex: 1, minWidth: 240, background: "#0d141d", color: "var(--txt)", border: "1px solid var(--edge2)", borderRadius: 5, padding: "7px 9px", fontFamily: "var(--mono)", fontSize: 11 }} />
          </div>

          <div className="lbl" style={{ marginBottom: 6 }}>2 · Region (auto-detected, override if VPN/SD-WAN/Citrix)</div>
          <div className="row" style={{ marginBottom: 14 }}>
            <select value={region} onChange={(e) => setRegion(e.target.value)}>
              <option value="">⊙ Auto-detect</option>
              {regions.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
            {region && <span className="lbl" style={{ color: "var(--blue)" }}>▣ Override active</span>}
          </div>

          <div className="lbl" style={{ marginBottom: 6 }}>3 · Upload diagnostics</div>
          <div className={"dropzone" + (drag ? " drag" : "")}
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => { e.preventDefault(); setDrag(false); addFiles(e.dataTransfer.files); }}>
            <b>⬆ DROP FILES OR CLICK TO UPLOAD</b>
            <small>Traceroute · MTR · Ping · 8x8 Utility Test · Firewall logs · PingPlotter export</small>
            <input ref={fileRef} type="file" multiple hidden accept=".txt,.log,.csv,.json,.mtr,.out"
              onChange={(e) => addFiles(e.target.files)} />
          </div>

          <div className="filelist">
            {files.map((f, i) => (
              <div className="fileitem" key={i}>
                <span className="tag">{guessType(f.text, f.name)}</span>
                <span>{f.name}</span>
                <span className="x" onClick={() => setFiles(files.filter((_, j) => j !== i))}>✕</span>
              </div>
            ))}
          </div>

          <div className="lbl" style={{ margin: "14px 0 6px" }}>4 · …or paste diagnostics</div>
          <textarea value={paste} onChange={(e) => setPaste(e.target.value)}
            placeholder="Paste traceroute / MTR / ping / 8x8 utility test output here…" />

          <div className="lbl" style={{ margin: "14px 0 6px" }}>Load a sample case</div>
          <div className="row">
            {Object.keys(samples).map((k) => (
              <span className="chip" key={k} onClick={() => loadSample(k)}>◆ {k}</span>
            ))}
          </div>

          <div className="row" style={{ marginTop: 18 }}>
            <button className="btn primary" onClick={run} disabled={busy}>▶ RUN INVESTIGATION</button>
            <button className="btn ghost" onClick={clearAll}>CLEAR</button>
          </div>
        </div>
      ) : (
        <div style={{ padding: 12 }}>
          <ResultsView r={result} toast={toast} />
        </div>
      )}
    </>
  );
}
