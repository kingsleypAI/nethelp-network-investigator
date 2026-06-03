const KB: [string, string][] = [
  ["Packet loss location", "Loss at hop 1-2 = customer LAN/Wi-Fi. Loss at hop 3 = CPE / ISP gateway. Loss beyond = ISP / backbone. Single-hop loss that does not persist downstream is usually ICMP de-prioritisation, not a real fault."],
  ["Country latency thresholds", "UK→UK <50ms · intra-Europe <80ms · transatlantic <150ms · intercontinental <250ms. Always phrase findings against the regional expectation, never just \"high\"."],
  ["VoIP quality targets", "Jitter <30ms · packet loss <1% · MOS ≥4.0 good, ≥3.6 acceptable. RTP needs UDP 10000-30000 open both ways."],
  ["Required 8x8 ports", "SIP signalling UDP/TCP 5060, TLS 5061, HTTPS 443, RTP media UDP 10000-30000. Disable SIP ALG on the firewall — it commonly breaks signalling."],
  ["Wrong datacentre", "If traffic lands at the wrong DC for the region, suspect DNS, VPN, SD-WAN breakout or ISP routing. Verify DNS and WAN routing policy first."],
  ["ISP congestion signature", "Loss + climbing latency starting at an ISP-named hop (e.g. virginmedia.net) = provider congestion. Escalate to ISP with the trace attached."],
];

export default function KnowledgeBase() {
  return (
    <div style={{ padding: 12 }}>
      {KB.map(([h, p]) => (
        <div className="kbcard" key={h}>
          <h4>✦ {h}</h4>
          <p>{p}</p>
        </div>
      ))}
    </div>
  );
}
