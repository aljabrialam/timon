import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(level=logging.INFO)

REPO = Path(__file__).resolve().parent.parent
VENV_PYTHON = REPO / ".venv" / "bin" / "python"
ENGINE_PYTHON = os.environ.get("TIMON_PYTHON") or (
    str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
)

HELP = (
    "Timón (paper only). Commands:\n"
    "• `@Timon hello` — link check\n"
    "• `@Timon status` — session, kill switch, ledger integrity\n"
    "This bot never places orders."
)

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


def run_timon(*args):
    result = subprocess.run(
        [ENGINE_PYTHON, "-m", "timon", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip()[-800:])
    return json.loads(result.stdout)


def status_text():
    session = run_timon("session")
    kill = run_timon("killswitch", "state/state.json")
    ledger = run_timon("verify")
    return "\n".join(
        [
            f"*{session['et']}* ({session['sgt']})",
            f"session {session['session']} · can_enter {session['can_enter']} · flatten {session['must_flatten']}",
            f"kill switch {kill['action']} — {', '.join(kill['reasons'])}",
            f"ledger {'ok' if ledger['ok'] else 'BROKEN'} · {ledger['entries']} entries",
            "No orders placed.",
        ]
    )


def reply(text, say):
    parts = text.split(maxsplit=1)
    command = parts[1].strip().lower() if len(parts) > 1 else ""
    if command == "hello":
        say("Hello from Timón. Slack link OK. No trades placed.")
    elif command == "status":
        try:
            say(status_text())
        except Exception as exc:
            say(f"Status failed: {exc}")
    else:
        say(HELP)


@app.event("app_mention")
def handle_app_mention(event, say):
    reply(event.get("text", ""), say)


@app.event("message")
def handle_direct_message(event, say):
    if event.get("channel_type") == "im" and not event.get("bot_id"):
        reply(event.get("text", ""), say)


if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
