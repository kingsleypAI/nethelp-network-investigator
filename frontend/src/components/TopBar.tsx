import { useEffect, useState } from "react";

export default function TopBar({ busy, claudeEnabled }: { busy: boolean; claudeEnabled: boolean }) {
  const [clock, setClock] = useState("--:--:--");
  useEffect(() => {
    const t = setInterval(() => setClock(new Date().toTimeString().slice(0, 8)), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="topbar">
      <div className="logo">
        <span className="mark">◈</span>
        <span>NetHelp</span> <b>NETWORK INVESTIGATOR</b>
      </div>
      <div className="sub">VoIP · UCaaS · CONTACT CENTRE DIAGNOSTICS</div>
      <div className="spacer" />
      {claudeEnabled && <div className="stat"><span className="led" /> CLAUDE ENRICH</div>}
      <div className="stat">
        <span className={"led" + (busy ? " amber" : "")} /> {busy ? "ANALYSING" : "ENGINE ONLINE"}
      </div>
      <div className="stat">{clock}</div>
    </div>
  );
}
