from app.engine.parsers import parse_8x8_utility, parse_ping, parse_traceroute


def test_mtr_parse():
    tr = parse_traceroute(
        "HOST: pc  Loss%   Snt   Last   Avg  Best  Wrst StDev\n"
        "  1.|-- 192.168.1.1  0.0%  10  0.8  0.9  0.7  1.2  0.1\n"
        "  3.|-- core.lon.bt.net  4.2%  10  34.0  34.0  30.0  60.0  5.0"
    )
    assert tr is not None
    assert tr.hops[0].hop == 1
    assert tr.hops[1].loss == 4.2
    assert tr.hops[1].host == "core.lon.bt.net"


def test_pingplotter_table_parse():
    tr = parse_traceroute(
        "Target: lon.8x8.com\nHop  IP   Loss%  Avg\n"
        "  3  core.virginmedia.net     4.2%   34.0\n"
        "  5  edge.lon.8x8.com         4.6%   286.0"
    )
    assert tr is not None
    hops = {h.hop: h for h in tr.hops}
    assert hops[3].loss == 4.2
    assert hops[5].avg == 286.0


def test_classic_traceroute_with_timeout():
    tr = parse_traceroute(
        "traceroute to x\n 1  192.168.0.1  1.1 ms 1.0 ms 1.2 ms\n 2  * * *\n"
        " 3  edge.fra.8x8.com  28.0 ms 28.1 ms 27.9 ms"
    )
    hops = {h.hop: h for h in tr.hops}
    assert hops[2].loss == 100.0
    assert hops[3].avg == 28.0


def test_utility_json():
    u = parse_8x8_utility('{"region":"Germany","dns":"PASS","ports":{"rtp":"blocked"}}')
    assert u is not None
    assert u.region == "Germany"
    assert u.ports["rtp"] == "blocked"


def test_utility_text():
    u = parse_8x8_utility("8x8 Utility Test\nDNS: WARNING\nJitter: 42\nMOS: 3.2")
    assert u.dns == "WARNING"
    assert u.jitter == 42
    assert u.mos == 3.2


def test_ping_linux():
    p = parse_ping("64 bytes ...\n3 packets transmitted, 3 received, 0% packet loss\n"
                   "rtt min/avg/max/mdev = 10.1/12.3/15.0/1.2 ms")
    assert p.loss == 0.0
    assert p.avg == 12.3
