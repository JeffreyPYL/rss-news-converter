from __future__ import annotations

# Some outlets' edges (e.g. CBC's Akamai front) reset the connection when a
# request carries httpx's default User-Agent ("python-httpx/x.y") — a real
# browser UA fetches the exact same content instantly, still over HTTP/1.1.
# Shared across every outbound httpx.Client in infrastructure/ rather than
# duplicated per adapter, since it must stay identical everywhere it's used.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
