import { useEffect, useRef, useState } from "react";

const STEPS: [string, string][] = [
  ["POWERING UP DIAGNOSTIC CORE", "BOOT"],
  ["MOUNTING DATACENTRE MAP · 14 REGIONS", "LOAD"],
  ["CALIBRATING LATENCY THRESHOLDS", "CALIB"],
  ["SPINNING UP PACKET-LOSS ANALYSERS", "SPIN"],
  ["ARMING FIREWALL / DNS / ISP DETECTORS", "ARM"],
  ["SYNCHRONISING SBC ENDPOINTS", "SYNC"],
  ["OPERATIONS CENTRE ONLINE", "READY"],
];

/** Industrial cold-start boot screen. Calls onDone when finished, then fades out. */
export default function LoadingScreen({ onDone }: { onDone?: () => void }) {
  const [idx, setIdx] = useState(0);
  const [done, setDone] = useState(false);
  const [gone, setGone] = useState(false);
  const timer = useRef<number>();

  useEffect(() => {
    if (idx < STEPS.length) {
      const last = idx === STEPS.length - 1;
      timer.current = window.setTimeout(() => setIdx((i) => i + 1), last ? 520 : 240 + Math.random() * 160);
    } else {
      const t1 = window.setTimeout(() => setDone(true), 420);
      const t2 = window.setTimeout(() => { setGone(true); onDone?.(); }, 1070);
      return () => { clearTimeout(t1); clearTimeout(t2); };
    }
    return () => clearTimeout(timer.current);
  }, [idx, onDone]);

  if (gone) return null;
  const pct = Math.round((Math.min(idx, STEPS.length) / STEPS.length) * 100);
  const status = idx >= STEPS.length ? "ONLINE" : STEPS[idx][1];
  const shown = STEPS.slice(0, idx).slice(-5);

  return (
    <div id="boot" className={done ? "done" : ""}>
      <div className="boot-core"><span className="gear" /><span className="gear r" />◈</div>
      <div className="boot-title"><span>Net</span>Help</div>
      <div className="boot-sub">NETWORK INVESTIGATOR · DIAGNOSTIC CORE</div>
      <div className="boot-barwrap">
        <div className="boot-bar"><i style={{ width: `${pct}%` }} /></div>
        <div className="boot-meta"><span>{status}</span><span>{pct}%</span></div>
      </div>
      <div className="boot-log">
        {shown.map(([msg], i) => {
          const isLast = idx === STEPS.length && i === shown.length - 1;
          return (
            <div key={msg}>
              <span className={isLast ? "ok" : "am"}>{isLast ? "✓" : "▸"}</span> <b>{msg}…</b>
            </div>
          );
        })}
      </div>
      <div className="boot-foot">INDUSTRIAL NETWORK OPERATIONS CENTRE</div>
    </div>
  );
}
