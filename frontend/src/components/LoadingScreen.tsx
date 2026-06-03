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
      <div className="robot">
        <svg viewBox="0 0 140 175" width="150" height="186" xmlns="http://www.w3.org/2000/svg">
          <ellipse cx="70" cy="167" rx="34" ry="6" fill="#000" opacity="0.35" />
          <rect x="52" y="131" width="12" height="17" rx="4" fill="#1b2734" stroke="#2a3a4d" strokeWidth="2" />
          <rect x="76" y="131" width="12" height="17" rx="4" fill="#1b2734" stroke="#2a3a4d" strokeWidth="2" />
          <g className="arm-wave">
            <line x1="40" y1="86" x2="22" y2="56" stroke="#22303f" strokeWidth="9" strokeLinecap="round" />
            <circle cx="20" cy="50" r="8" fill="#ffb02e" stroke="#7a5e13" strokeWidth="1.5" />
            <line x1="15" y1="44" x2="12" y2="40" stroke="#ffb02e" strokeWidth="2.4" strokeLinecap="round" />
            <line x1="20" y1="42" x2="20" y2="36" stroke="#ffb02e" strokeWidth="2.4" strokeLinecap="round" />
            <line x1="25" y1="43" x2="28" y2="38" stroke="#ffb02e" strokeWidth="2.4" strokeLinecap="round" />
          </g>
          <line x1="100" y1="86" x2="105" y2="114" stroke="#22303f" strokeWidth="9" strokeLinecap="round" />
          <circle cx="106" cy="116" r="7" fill="#22303f" stroke="#2a3a4d" strokeWidth="2" />
          <rect x="40" y="80" width="60" height="54" rx="14" fill="#16202d" stroke="#2a3a4d" strokeWidth="2.5" />
          <rect x="55" y="92" width="30" height="22" rx="4" fill="#0a1018" stroke="#1f2c3a" />
          <g fill="#34d17a">
            <rect className="b1" x="60" y="104" width="4" height="6" rx="1" />
            <rect className="b2" x="68" y="100" width="4" height="10" rx="1" />
            <rect className="b3" x="76" y="96" width="4" height="14" rx="1" />
          </g>
          <rect x="63" y="72" width="14" height="10" rx="3" fill="#1b2734" />
          <rect x="44" y="32" width="52" height="44" rx="13" fill="#1b2734" stroke="#ffb02e" strokeWidth="2.5" />
          <g className="eyes" fill="#34d17a">
            <circle cx="59" cy="52" r="5.5" />
            <circle cx="81" cy="52" r="5.5" />
          </g>
          <path d="M57 61 Q70 71 83 61" fill="none" stroke="#34d17a" strokeWidth="2.4" strokeLinecap="round" />
          <circle cx="49" cy="65" r="1.6" fill="#33485e" />
          <circle cx="91" cy="65" r="1.6" fill="#33485e" />
          <line x1="70" y1="32" x2="70" y2="20" stroke="#33485e" strokeWidth="3" />
          <circle className="tip" cx="70" cy="17" r="4" fill="#ffb02e" />
          <g fill="none" stroke="#ffb02e" strokeWidth="2.4" strokeLinecap="round">
            <path className="sig1" d="M62 13 a11 11 0 0 1 16 0" />
            <path className="sig2" d="M57 8 a18 18 0 0 1 26 0" />
            <path className="sig3" d="M52 3 a25 25 0 0 1 36 0" />
          </g>
        </svg>
      </div>
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
