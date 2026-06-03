import { useEffect, useRef } from "react";

export interface LogLine {
  t: string;
  m: string;
  cls: string;
}

export default function Console({ lines }: { lines: LogLine[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines]);
  return (
    <div className="panel" id="console">
      <div className="phead"><span className="dot" />LIVE DIAGNOSTIC CONSOLE</div>
      <div id="consoleBody" ref={ref}>
        {lines.map((l, i) => (
          <div key={i} className={"cl " + l.cls}>
            <span className="t">{l.t}</span>
            <span className="m">{l.m}{i === lines.length - 1 ? <span className="cur" /> : null}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
