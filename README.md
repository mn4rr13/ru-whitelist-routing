# ru-whitelist-routing

Daily-built routing for 3x-ui JSON subscriptions (Happ): domains from Russian
mobile-internet whitelists go direct, everything else (including Apple) goes
through the proxy.

Sources: [ancored/ru-mobile-whitelist](https://github.com/ancored/ru-mobile-whitelist),
[hxehex/russia-mobile-internet-whitelist](https://github.com/hxehex/russia-mobile-internet-whitelist).

## Files (`dist/`)

- `happ-profile.json` — paste into "Профиль маршрутизации для JSON-подписки".
  Panel adds a domestic DNS for the direct domains. No bittorrent rule possible.
- `xray-rules.json` — paste into the panel's "JSON rules" field (only used while
  the routing profile field is empty). Adds `bittorrent -> direct`.

3x-ui limits a remote URL to 16 KiB, so these files (~30 KiB) must be pasted
inline; re-paste when the lists change.

## Auto-update on the VPS

`scripts/vps-update.py` is installed as `/usr/local/bin/update-subjson-rules.py`
with a weekly cron (Mondays 04:10). It downloads `dist/xray-rules.json`, writes it into the
`subJsonRules` setting of `/etc/x-ui/x-ui.db` (backup first, last 5 kept) and
restarts `x-ui` only when the rules changed.
