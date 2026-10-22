"""Separate single-choice VPN field; never add provider IDs to software.selected."""
import json
from pathlib import Path

CATALOG = json.loads(Path(__file__).with_name("catalog.json").read_text())


def available_providers(system):
    if system not in ("x86_64-linux", "aarch64-linux"):
        raise ValueError("Unsupported target architecture")
    return [dict(p, available=system in p["platforms"]) for p in CATALOG["providers"]]


def render_selection(provider, system):
    """Render only validated constants. Credentials and profile paths are not input."""
    providers = {p["id"]: p for p in available_providers(system)}
    if provider is not None:
        if not isinstance(provider, str) or provider not in providers:
            raise ValueError("Choose one known VPN provider, or None")
        if not providers[provider]["available"]:
            raise ValueError("VPN client unavailable for target architecture")
    value = "null" if provider is None else json.dumps(provider)
    return "{ ... }: { nascent.vpn.provider = " + value + "; }\n"
