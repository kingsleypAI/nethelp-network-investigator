import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import CasesView from "./components/CasesView";
import Console, { LogLine } from "./components/Console";
import DatacentreView from "./components/DatacentreView";
import KnowledgeBase from "./components/KnowledgeBase";
import LoadingScreen from "./components/LoadingScreen";
import NavPanel, { NavKey } from "./components/NavPanel";
import SummaryPanel from "./components/SummaryPanel";
import TopBar from "./components/TopBar";
import Workspace from "./components/Workspace";
import type { Analysis, EvidenceInput } from "./types";

const TITLES: Record<NavKey, string> = {
  investigate: "ANALYSIS WORKSPACE",
  cases: "PREVIOUS CASES",
  datacentres: "DATACENTRE INTELLIGENCE",
  kb: "KNOWLEDGE BASE",
};

export default function App() {
  const [nav, setNav] = useState<NavKey>("investigate");
  const [lines, setLines] = useState<LogLine[]>([]);
  const [result, setResult] = useState<Analysis | null>(null);
  const [regions, setRegions] = useState<string[]>([]);
  const [samples, setSamples] = useState<Record<string, EvidenceInput[]>>({});
  const [claudeEnabled, setClaudeEnabled] = useState(false);
  const [toastMsg, setToastMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const log = useCallback((m: string, cls = "") => {
    setLines((prev) => [...prev, { t: new Date().toTimeString().slice(0, 8), m, cls }]);
  }, []);

  const toast = useCallback((m: string) => {
    setToastMsg(m);
    setTimeout(() => setToastMsg(""), 1600);
  }, []);

  useEffect(() => {
    log("NetHelp diagnostic core initialising…", "head");
    Promise.all([api.regions(), api.samples(), api.config()])
      .then(([r, s, c]) => {
        setRegions(r);
        setSamples(s);
        setClaudeEnabled(c.claudeEnabled);
        log(`Backend online · ${r.length} regions · Claude enrich ${c.claudeEnabled ? "ON" : "OFF"}.`, "info");
        log("Standing by for evidence.", "ok");
      })
      .catch((e) => log("Backend unreachable: " + e.message + " (start the FastAPI server)", "err"));
  }, [log]);

  const onResult = (a: Analysis) => { setResult(a); setBusy(false); };

  return (
    <>
      <LoadingScreen />
      <TopBar busy={busy} claudeEnabled={claudeEnabled} />
      <div className="shell">
        <NavPanel active={nav} onNav={setNav} />

        <div className="panel" id="center">
          <div className="phead"><span className="dot" /><span>{TITLES[nav]}</span></div>
          <div className="pbody">
            {nav === "investigate" && (
              <Workspace regions={regions} samples={samples} result={result}
                onResult={onResult} log={log} toast={toast} />
            )}
            {nav === "cases" && (
              <CasesView log={log} onOpen={(a) => { setResult(a); setNav("investigate"); }} />
            )}
            {nav === "datacentres" && <DatacentreView />}
            {nav === "kb" && <KnowledgeBase />}
          </div>
        </div>

        <SummaryPanel r={result} />
        <Console lines={lines} />
      </div>

      <div className={"toast" + (toastMsg ? " show" : "")}>{toastMsg}</div>
      <div className="kp-badge">MADE BY <b>KP</b></div>
    </>
  );
}
