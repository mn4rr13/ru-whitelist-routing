#!/usr/bin/env python3
"""Build routing JSON for 3x-ui JSON subscriptions (Happ clients).

Direct: domains from Russian mobile-internet whitelists. Everything else goes
through the proxy (default catch-all of the panel template).
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

SOURCES = [
    "https://raw.githubusercontent.com/ancored/ru-mobile-whitelist/release/ru-mobile-whitelist-sni.txt",
    "https://raw.githubusercontent.com/hxehex/russia-mobile-internet-whitelist/main/whitelist.txt",
]

# Apple stays on the proxy so push/iMessage work even when whitelists are enforced.
PROXY_ONLY = (
    "apple.com", "icloud.com", "icloud-content.com", "mzstatic.com", "cdn-apple.com",
    "apple-cloudkit.com", "apple.news", "aaplimg.com", "itunes.com", "me.com",
)

DOMAIN_RE = re.compile(r"^(?=.{4,253}$)([a-z0-9_-]{1,63}\.)+[a-z0-9-]{2,63}$")
OUT = Path(__file__).resolve().parent.parent / "dist"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ru-whitelist-routing/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def is_proxy_only(d):
    return any(d == p or d.endswith("." + p) for p in PROXY_ONLY)


def collapse(domains):
    """Drop subdomains already covered by a parent entry (domain: matches subdomains)."""
    kept = set()
    for d in sorted(domains, key=lambda x: x.count(".")):
        parts = d.split(".")
        if not any(".".join(parts[i:]) in kept for i in range(1, len(parts) - 1)):
            kept.add(d)
    return sorted(kept)


def main():
    domains, ok = set(), 0
    for url in SOURCES:
        try:
            text = fetch(url)
        except Exception as e:
            print(f"warn: {url}: {e}", file=sys.stderr)
            continue
        ok += 1
        for line in text.splitlines():
            d = line.split("#")[0].strip().lower().lstrip("*.").removeprefix("domain:")
            if DOMAIN_RE.match(d) and not is_proxy_only(d):
                domains.add(d)
    if not ok or len(domains) < 500:
        sys.exit(f"refusing to write: sources={ok}, domains={len(domains)}")

    direct = ["domain:" + d for d in collapse(domains)]
    OUT.mkdir(exist_ok=True)

    # A: Happ routing profile (field "Профиль маршрутизации для JSON-подписки").
    profile = {
        "Name": "RU whitelist direct",
        "GlobalProxy": "true",
        "DomainStrategy": "AsIs",
        "DirectSites": direct,
        "DirectIp": ["geoip:private"],
    }
    # B: raw xray rules (field "JSON rules"); adds bittorrent -> direct.
    rules = [
        {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
        {"type": "field", "protocol": ["bittorrent"], "outboundTag": "direct"},
        {"type": "field", "domain": direct, "outboundTag": "direct"},
    ]
    (OUT / "happ-profile.json").write_text(json.dumps(profile, ensure_ascii=False, separators=(",", ":")) + "\n")
    (OUT / "xray-rules.json").write_text(json.dumps(rules, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"direct domains: {len(direct)}")


if __name__ == "__main__":
    main()
