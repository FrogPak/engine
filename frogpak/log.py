"""Messages that GitHub Actions turns into annotations, and plain text elsewhere."""
import os
import sys

_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"
warnings = []


def _emit(kind, message):
    if _ACTIONS:
        # Unescaped newlines in server-supplied text would start new workflow commands.
        escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::{kind}::{escaped}", file=sys.stderr)
    else:
        print(f"{kind}: {message}", file=sys.stderr)


def info(message):
    print(message, file=sys.stderr)


def notice(message):
    _emit("notice", message)


def warning(message):
    warnings.append(message)
    _emit("warning", message)


def error(message):
    _emit("error", message)


def summary(markdown):
    """Adds Markdown to the workflow run's summary page; does nothing outside GitHub Actions."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as out:
            out.write(markdown.rstrip("\n") + "\n")
