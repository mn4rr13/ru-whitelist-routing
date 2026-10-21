#!/usr/bin/env python3
"""Pull xray-rules.json from GitHub into the 3x-ui subJsonRules setting.

Runs on the VPS from cron. Restarts x-ui only when the rules changed, because
the panel reads subJsonRules at startup.
"""
import json
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request

URL = "https://raw.githubusercontent.com/mn4rr13/ru-whitelist-routing/main/dist/xray-rules.json"
DB = "/etc/x-ui/x-ui.db"
KEEP_BACKUPS = 5


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "vps-update/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        new = json.loads(r.read().decode())
    domains = sum(len(x.get("domain", [])) for x in new)
    if not isinstance(new, list) or domains < 500:
        sys.exit(f"refusing: unexpected payload (domains={domains})")
    value = json.dumps(new, ensure_ascii=False, separators=(",", ":"))

    db = sqlite3.connect(DB, timeout=30)
    row = db.execute("select value from settings where key='subJsonRules'").fetchone()
    if row is None:
        sys.exit("subJsonRules row not found")
    if row[0] == value:
        print("unchanged")
        return

    shutil.copy2(DB, f"{DB}.bak-{int(time.time())}")
    for old in sorted(__import__("glob").glob(f"{DB}.bak-*"))[:-KEEP_BACKUPS]:
        __import__("os").remove(old)
    db.execute("update settings set value=? where key='subJsonRules'", (value,))
    db.commit()
    db.close()
    subprocess.run(["systemctl", "restart", "x-ui"], check=True)
    print(f"updated: {domains} domains, x-ui restarted")


if __name__ == "__main__":
    main()
