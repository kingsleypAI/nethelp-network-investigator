import { useEffect, useState } from "react";
import { api } from "../api";
import type { Analysis, SiteGroup } from "../types";

export default function CasesView({ onOpen, log }: { onOpen: (a: Analysis) => void; log: (m: string, c?: string) => void }) {
  const [groups, setGroups] = useState<SiteGroup[] | null>(null);

  useEffect(() => {
    api.groupedCases().then(setGroups).catch((e) => log("Could not load cases: " + e.message, "err"));
  }, []);

  async function open(id: number) {
    try {
      const { analysis } = await api.getCase(id);
      onOpen(analysis);
    } catch (e) {
      log("Could not open case: " + (e as Error).message, "err");
    }
  }

  if (!groups) return <div className="empty"><div>LOADING CASES…</div></div>;
  if (!groups.length) return <div className="empty"><div><div className="big">≡</div>NO CASES STORED YET</div></div>;

  return (
    <div style={{ padding: 12 }}>
      {groups.map((g) => (
        <div className="group" key={g.site}>
          <div className="ghead">
            <span className={"badge " + g.worstHealth}>{g.worstHealth.toUpperCase()}</span>
            <b className="gname">{g.site}</b>
            <span className="gcount">{g.count} test{g.count > 1 ? "s" : ""}</span>
            <span className="gtypes">{g.evidenceTypes.map((t) => <span className="etype" key={t}>{t}</span>)}</span>
          </div>
          {g.cases.map((c) => (
            <div className="caseitem" key={c.id} onClick={() => open(c.id)}>
              <div className="top">
                <span>
                  <span className={"badge " + c.health}>{c.health.toUpperCase()}</span>
                  <span className="lbl" style={{ marginLeft: 8 }}>
                    {(c.createdAt || "").replace("T", " ").slice(0, 19)} · {c.confidence}% · {c.region || "—"}
                  </span>
                </span>
                <span className="gtypes">{c.evidenceTypes.map((t) => <span className="etype sm" key={t}>{t}</span>)}</span>
              </div>
              <div className="rc">{c.rootCause}</div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
