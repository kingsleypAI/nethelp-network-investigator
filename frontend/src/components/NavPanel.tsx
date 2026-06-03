export type NavKey = "investigate" | "cases" | "datacentres" | "kb";

const ITEMS: { key: NavKey; ic: string; label: string; section: string }[] = [
  { key: "investigate", ic: "⊕", label: "NEW INVESTIGATION", section: "OPERATIONS" },
  { key: "cases", ic: "≡", label: "PREVIOUS CASES", section: "OPERATIONS" },
  { key: "datacentres", ic: "⌖", label: "DATACENTRE DB", section: "INTELLIGENCE" },
  { key: "kb", ic: "✦", label: "KNOWLEDGE BASE", section: "INTELLIGENCE" },
];

export default function NavPanel({ active, onNav }: { active: NavKey; onNav: (k: NavKey) => void }) {
  let lastSection = "";
  return (
    <div className="panel" id="nav">
      <div className="phead"><span className="dot" />CONTROL</div>
      <div className="pbody">
        {ITEMS.map((it) => {
          const header = it.section !== lastSection ? <div key={it.section} className="navsec">{it.section}</div> : null;
          lastSection = it.section;
          return (
            <div key={it.key}>
              {header}
              <button className={"navbtn" + (active === it.key ? " active" : "")} onClick={() => onNav(it.key)}>
                <span className="ic">{it.ic}</span>{it.label}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
