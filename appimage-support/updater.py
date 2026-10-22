"""Allowlisted GitHub release discovery, Nix validation and atomic app activation."""
import argparse
import base64
import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import uuid


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    os.replace(temporary, path)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def switch(app_dir, generation):
    temporary = app_dir / "current.next"
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(generation.relative_to(app_dir))
    os.replace(temporary, app_dir / "current")


def validate_pin(pin, repository):
    if not re.fullmatch(r"[a-z][a-z0-9-]*", pin["id"]):
        raise ValueError("invalid application ID")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid repository")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,127}", pin["version"]):
        raise ValueError("unsupported release tag")
    prefix = f"https://github.com/{repository}/releases/download/"
    if not pin["url"].startswith(prefix) or urllib.parse.urlsplit(pin["url"]).query:
        raise ValueError("source URL is outside the allowlisted release repository")
    if not re.fullmatch(r"sha256-[A-Za-z0-9+/]{43}=", pin["hash"]):
        raise ValueError("require an explicit SHA-256 SRI hash")
    if pin["platform"] not in ("x86_64-linux", "aarch64-linux"):
        raise ValueError("unsupported platform")


def discover(app):
    repository = app["repository"]
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/releases/latest",
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": "nascentOS-appimage-watchdog",
                 "X-GitHub-Api-Version": "2022-11-28"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("release metadata exceeds size limit")
    release = json.loads(raw)
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("refusing draft or prerelease")
    tag = release["tag_name"]
    filename = app["assetName"].replace("{tag}", tag)
    assets = [a for a in release["assets"] if a["name"] == filename]
    if len(assets) != 1:
        raise ValueError("expected exactly one matching release asset")
    asset = assets[0]
    if not 0 < asset["size"] <= app["maxBytes"]:
        raise ValueError("release asset exceeds configured size limit")
    digest = asset.get("digest") or ""
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("GitHub did not publish a SHA-256 digest; review manually")
    expected = (f"https://github.com/{repository}/releases/download/"
                f"{urllib.parse.quote(tag, safe='')}/{urllib.parse.quote(filename, safe='')}")
    if asset["browser_download_url"] != expected:
        raise ValueError("asset URL does not match selected repository, tag and filename")
    pin = dict(app["pin"], version=tag, url=expected,
               hash="sha256-" + base64.b64encode(bytes.fromhex(digest[7:])).decode())
    validate_pin(pin, repository)
    return pin


def run(command):
    # No shell, credentials, mutable channels, flake lock updates or app execution.
    subprocess.run(command, check=True, timeout=5400)


def save_context(config, generation):
    write_json(generation / "build-context.json", {
        "nixpkgsPath": config["nixpkgsPath"], "recipePath": config["recipePath"]})
    # Retain evaluation inputs even after old system generations are collected.
    for key, name in (("nixpkgsPath", "nixpkgs"), ("recipePath", "recipe")):
        run(["nix-store", "--realise", config[key], "--add-root",
             str(generation / name), "--indirect"])


def initialize(config, app_dir, app):
    generations = app_dir / "generations"
    generations.mkdir(parents=True, exist_ok=True)
    if not (app_dir / "current").exists():
        seed = generations / ("seed-" + uuid.uuid4().hex)
        seed.mkdir()
        write_json(seed / "pin.json", app["pin"])
        save_context(config, seed)
        # Register every generation as an indirect GC root, including the seed.
        run(["nix-store", "--realise", app["initialPackage"],
             "--add-root", str(seed / "package"), "--indirect"])
        switch(app_dir, seed)


def update_one(config, app_dir, app):
    if (app_dir / "hold").exists():
        return {"state": "held", "checkedAt": now()}
    pin = discover(app)
    current = json.loads((app_dir / "current/pin.json").read_text())
    if pin == current:
        return {"state": "current", "checkedAt": now(), "pin": pin}
    # A vendor re-upload under the same tag needs explicit review.
    if pin["version"] == current["version"]:
        raise ValueError("upstream changed an existing version; refusing replacement")
    candidate = app_dir / "generations" / uuid.uuid4().hex
    candidate.mkdir()
    write_json(candidate / "pin.json", pin)
    save_context(config, candidate)
    run(["nix-build", config["buildFile"], "--argstr", "nixpkgsPath",
         config["nixpkgsPath"], "--argstr", "pinPath", str(candidate / "pin.json"),
         "--out-link", str(candidate / "package")])
    executable = candidate / "package/bin" / pin["id"]
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError("built package is missing the expected executable")
    # This verifies packaging only. A GUI health check needs an app-specific test.
    write_json(candidate / "validated.json", {"validatedAt": now()})
    if app["autoActivate"]:
        switch(app_dir, candidate)
    return {"state": "activated" if app["autoActivate"] else "staged",
            "checkedAt": now(), "generation": candidate.name, "pin": pin}


def rollback(app_dir):
    current = (app_dir / "current").resolve()
    # Only previously activated generations are eligible; staged builds aren't history.
    history = json.loads((app_dir / "history.json").read_text())
    previous = next((name for name in reversed(history) if name != current.name), None)
    if previous is None:
        raise ValueError("no previous activated generation")
    target = app_dir / "generations" / previous
    if not (target / "package").exists():
        raise ValueError("previous generation is unavailable")
    (app_dir / "hold").touch()
    switch(app_dir, target)
    return {"state": "rolled-back-held", "generation": previous, "checkedAt": now()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("command", choices=["update", "status", "rollback", "resume"])
    parser.add_argument("app", nargs="?")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    apps = config["apps"]
    if args.app is not None and args.app not in apps:
        parser.error("application is not in the declarative allowlist")
    if args.command in ("rollback", "resume") and args.app is None:
        parser.error("this command requires an application ID")
    root = Path(config["stateDir"])
    if args.command == "status":
        for name in ([args.app] if args.app else apps):
            path = root / name / "status.json"
            print(json.dumps({"app": name, **(json.loads(path.read_text()) if path.exists()
                  else {"state": "seed", "pin": apps[name]["pin"]})}))
        return 0
    root.mkdir(parents=True, exist_ok=True)
    failures = False
    with (root / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for name in ([args.app] if args.app else apps):
            app_dir = root / name
            try:
                app = apps[name]
                validate_pin(app["pin"], app["repository"])
                if app["pin"]["id"] != name:
                    raise ValueError("pin ID differs from allowlist key")
                initialize(config, app_dir, app)
                history_path = app_dir / "history.json"
                history = json.loads(history_path.read_text()) if history_path.exists() else []
                active = (app_dir / "current").resolve().name
                if not history or history[-1] != active:
                    history.append(active)
                # Record initial/current generation before any activation.
                write_json(history_path, history)
                if args.command == "rollback":
                    result = rollback(app_dir)
                elif args.command == "resume":
                    (app_dir / "hold").unlink(missing_ok=True)
                    result = {"state": "resumed", "checkedAt": now()}
                else:
                    result = update_one(config, app_dir, app)
                active = (app_dir / "current").resolve().name
                if history[-1] != active:
                    history.append(active)
                write_json(history_path, history)
                write_json(app_dir / "status.json", result)
                print(f"{name}: {result['state']}", flush=True)
            except Exception as error:
                failures = True
                app_dir.mkdir(parents=True, exist_ok=True)
                result = {"state": "failed", "checkedAt": now(), "error": str(error)}
                write_json(app_dir / "status.json", result)
                print(f"{name}: {error}", file=sys.stderr, flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
