#!/usr/bin/env python3
"""Replay recorded GSMTAP packets to lo:4729 so GSMEvil2 sniffs them with no SDR.

Reads one or more pcaps (captured with `tshark -i lo -f 'udp port 4729 and not
icmp'`), extracts each GSMTAP UDP payload, and re-sends it to 127.0.0.1:4729,
preserving inter-packet timing and looping forever. Multiple pcaps play
back-to-back (concatenated) with a small gap, so a venue with no live 2G can run
the whole demo seamlessly from recordings.

Usage: replay.py rec_879M.pcap [rec_892M.pcap ...]
"""
import socket
import sys
import time

from scapy.all import rdpcap, UDP

GAP_BETWEEN_FILES = 0.5  # seconds


def load(paths):
    """Return [(payload, abs_rel_time)] with a monotonic timeline across files."""
    items = []
    offset = 0.0
    for path in paths:
        pkts = rdpcap(path)
        base = None
        last = 0.0
        for p in pkts:
            if UDP in p and int(p[UDP].dport) == 4729:
                payload = bytes(p[UDP].payload)
                if not payload:
                    continue
                t = float(p.time)
                if base is None:
                    base = t
                last = t - base
                items.append((payload, offset + last))
        offset += last + GAP_BETWEEN_FILES
    return items


def main(paths):
    items = load(paths)
    if not items:
        print("replay: no GSMTAP (udp/4729) packets found in", paths)
        return 1
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    total = items[-1][1]
    print(f"replay: {len(items)} GSMTAP packets, ~{total:.0f}s loop -> 127.0.0.1:4729")
    loops = 0
    while True:
        start = time.time()
        for payload, rel in items:
            now = time.time() - start
            if rel > now:
                time.sleep(rel - now)
            sock.sendto(payload, ("127.0.0.1", 4729))
        loops += 1
        print(f"replay: loop {loops} done")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(main(sys.argv[1:]))
