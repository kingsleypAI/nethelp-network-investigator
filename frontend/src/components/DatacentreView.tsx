import { useEffect, useState } from "react";
import { api } from "../api";

export default function DatacentreView() {
  const [dc, setDc] = useState<any[]>([]);
  const [ports, setPorts] = useState<{ port: string; proto: string; use: string }[]>([]);
  useEffect(() => {
    api.datacentres().then(setDc).catch(() => {});
    api.ports().then(setPorts).catch(() => {});
  }, []);
  return (
    <div style={{ padding: 12 }}>
      <div className="sec">
        <h3>8x8 DATACENTRE / SBC MAP</h3>
        <div className="c">
          <table>
            <thead><tr><th>Region</th><th>Datacentre</th><th>Edge / SBC</th><th>Cluster</th></tr></thead>
            <tbody>
              {dc.map((d) => (
                <tr key={d.region}>
                  <td>{d.region}</td>
                  <td><span className="pill b">{d.dc}</span></td>
                  <td style={{ fontFamily: "var(--mono)", fontSize: 11 }}>{(d.edge || []).join(", ")}</td>
                  <td>{d.cluster}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="sec" style={{ marginTop: 14 }}>
        <h3>REQUIRED 8x8 PORTS</h3>
        <div className="c">
          <table>
            <thead><tr><th>Port</th><th>Protocol</th><th>Use</th></tr></thead>
            <tbody>
              {ports.map((p) => (
                <tr key={p.port}><td><span className="pill g">{p.port}</span></td><td>{p.proto}</td><td>{p.use}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
