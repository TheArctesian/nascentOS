"""Pure selection rules shared by the GUI, privilege helper and installer job."""
import hashlib
import json
import re

from nascent_optional_profiles import validate_gaming, validate_vpn

SYSTEMS = ("x86_64-linux", "aarch64-linux")


def load_manifest(path):
    manifest = json.loads(path.read_text())
    if manifest.get("schemaVersion") != 1 or manifest.get("system") not in SYSTEMS:
        raise ValueError("Unsupported software catalog")
    apps = manifest.get("apps", [])
    ids = [app["id"] for app in apps]
    if not apps or len(ids) != len(set(ids)):
        raise ValueError("Empty or duplicate software catalog")
    for app in apps:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", app["id"]):
            raise ValueError("Invalid software identifier")
        if app["kind"] not in ("package", "web", "manual"):
            raise ValueError("Invalid software type")
        if not isinstance(app.get("available"), bool):
            raise ValueError("Catalog has no evaluated availability")
    return manifest


def digest(manifest):
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()


def defaults(manifest):
    return [app["id"] for app in manifest["apps"]
            if app.get("default") and app["available"] and app["kind"] == "package"
            and not app["proprietary"]]


def validate(manifest, value):
    if (not isinstance(value, dict)
            or not {"selected", "acceptedProprietary"}.issubset(value)
            or set(value) - {"selected", "acceptedProprietary", "vpn", "gaming"}):
        raise ValueError("Invalid selection record")
    selected, accepted = value["selected"], value["acceptedProprietary"]
    for values in (selected, accepted):
        if (not isinstance(values, list) or any(not isinstance(x, str) for x in values)
                or len(values) != len(set(values))):
            raise ValueError("Selections must be unique software identifiers")
    apps = {app["id"]: app for app in manifest["apps"]}
    if set(selected) - apps.keys():
        raise ValueError("Unknown selected software")
    for name in selected:
        app = apps[name]
        if app["kind"] != "package" or not app["available"]:
            raise ValueError(f"{app['name']} cannot be installed on {manifest['system']}")
    if sum(apps[name].get("group") == "Passwords" for name in selected) > 1:
        raise ValueError("Choose at most one password manager")
    optional = {}
    if "vpn" in value:
        optional["vpn"] = validate_vpn(value["vpn"], manifest["system"])
    if "gaming" in value:
        optional["gaming"] = validate_gaming(value["gaming"], manifest["system"])
    required = {name for name in selected if apps[name]["proprietary"]}
    if optional.get("gaming", {}).get("steam"):
        required.add("steam")
    if set(accepted) != required:
        raise ValueError("Confirm each selected proprietary application")
    return {"selected": sorted(selected), "acceptedProprietary": sorted(accepted), **optional}
