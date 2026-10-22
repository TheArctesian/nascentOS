"""Bounded speech/text -> desktop intent. Model responses are data, never code."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request

ACTIONS = {"browser.open", "browser.close", "none"}
ADDRESS = re.compile(r"0x[0-9a-fA-F]+\Z")
PHRASES = {
    "pull up my browser": "browser.open",
    "open my browser": "browser.open",
    "open browser": "browser.open",
    "close my browser": "browser.close",
    "close browser": "browser.close",
}
SCHEMA = {"type": "object", "properties": {"action": {"type": "string", "enum": sorted(ACTIONS)}},
          "required": ["action"], "additionalProperties": False}
BROWSER_CONFIG = Path(os.environ.get('NASCENT_DATA_DIR', '/etc/nascentos')) / 'software-runtime.json'
BROWSER_CLASSES = {
    'firefox': {'firefox', 'firefox-esr', 'org.mozilla.firefox'},
    'chromium': {'chromium', 'chromium-browser'},
}


def browser_classes(run):
    selected = json.loads(BROWSER_CONFIG.read_text()).get('browser') if BROWSER_CONFIG.exists() else 'firefox'
    if selected is None:
        default = run(['xdg-settings', 'get', 'default-web-browser'], check=True,
                      capture_output=True, text=True).stdout.strip().lower()
        selected = {'firefox.desktop': 'firefox', 'org.mozilla.firefox.desktop': 'firefox',
                    'chromium.desktop': 'chromium', 'chromium-browser.desktop': 'chromium'}.get(default)
    return BROWSER_CLASSES.get(selected, set())


def validate(value):
    if not isinstance(value, dict) or set(value) != {"action"}:
        raise ValueError("Intent must contain exactly one action field")
    if not isinstance(value["action"], str) or value["action"] not in ACTIONS:
        raise ValueError("Unknown desktop action")
    return value


def route(text, model=None):
    normalized = " ".join(text.lower().strip().rstrip(".!?").split())
    if not normalized or len(text) > 2000:
        raise ValueError("Provide a short desktop command")
    if model is None:
        return {"action": PHRASES.get(normalized, "none")}
    payload = json.dumps({"model": model, "stream": False, "format": SCHEMA,
                          "options": {"temperature": 0, "num_predict": 64},
                          "messages": [
                              {"role": "system", "content": "Classify the user's desktop request as browser.open, browser.close or none. Only explicit requests to open or close the browser qualify. Return JSON matching the schema."},
                              {"role": "user", "content": text}]}).encode()
    request = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=payload,
                                     headers={"Content-Type": "application/json"})
    # No proxy or redirects to external services; use the explicitly local runtime.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=30) as response:
        body = response.read(65537)
    if len(body) > 65536:
        raise ValueError("Model response too large")
    return validate(json.loads(json.loads(body)["message"]["content"]))


def browser_windows(run=subprocess.run):
    classes = browser_classes(run)
    if not classes:
        raise ValueError('The desktop default browser has no supported close target; nothing executed')
    response = run(["hyprctl", "-j", "clients"], check=True, capture_output=True, text=True)
    clients = json.loads(response.stdout)
    if not isinstance(clients, list):
        raise ValueError("Unexpected compositor client response")
    return [client for client in clients if isinstance(client, dict)
            and str(client.get("class", "")).lower() in classes
            and isinstance(client.get("address"), str) and ADDRESS.fullmatch(client["address"])]


def execute(intent, window=None, run=subprocess.run, launch=subprocess.Popen):
    action = validate(intent)["action"]
    if window is not None and not ADDRESS.fullmatch(window):
        raise ValueError("Invalid window address")
    if action == "none":
        raise ValueError("No supported desktop action recognized; nothing executed")
    if action == "browser.open":
        if window is not None:
            raise ValueError("Window selection applies only to close")
        launch(["nascent-browser"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Requested selected/default browser launch"
    windows = browser_windows(run)
    if window is None:
        if len(windows) != 1:
            choices = [{"address": item["address"], "title": item.get("title", "")} for item in windows]
            raise ValueError("Expected one selected browser window; use windows and --window to select explicitly: " + json.dumps(choices))
        window = windows[0]["address"]
    elif window not in {item["address"] for item in windows}:
        raise ValueError("Selected address is not a current selected browser window")
    # Address is validated hex and verified against live Firefox clients; no focus changes.
    command = 'hl.dsp.window.close({window="address:' + window + '"})'
    run(["hyprctl", "dispatch", command], check=True, capture_output=True, text=True)
    return "Requested normal close for browser " + window


def transcribe(model, audio):
    if not Path(model).is_file() or not Path(audio).is_file():
        raise ValueError("Supply existing Whisper model and audio files")
    with tempfile.TemporaryDirectory(prefix="nascent-voice-") as directory:
        output = Path(directory) / "transcript"
        subprocess.run(["whisper-cli", "-m", model, "-f", audio, "-otxt", "-of", str(output)], check=True)
        return output.with_suffix(".txt").read_text()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="Opt-in local Ollama intent model; must already be available")
    parser.add_argument("--window", help="Explicit current selected browser window address for close")
    parser.add_argument("--dry-run", action="store_true", help="Print validated intent without executing")
    sub = parser.add_subparsers(dest="source", required=True)
    sub.add_parser("windows", help="List targetable selected browser windows")
    sub.add_parser("text").add_argument("text")
    audio = sub.add_parser("audio", help="Transcribe a supplied file; no always-listening process")
    audio.add_argument("whisper_model")
    audio.add_argument("audio_file")
    args = parser.parse_args()
    try:
        if args.source == "windows":
            print(json.dumps(browser_windows(), indent=2))
            return
        text = args.text if args.source == "text" else transcribe(args.whisper_model, args.audio_file)
        intent = route(text, args.model)
        print(json.dumps(intent) if args.dry_run else execute(intent, args.window))
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
