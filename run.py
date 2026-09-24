"""Start OCI Sandbox Lab with login credentials resolved before Streamlit launches."""

from __future__ import annotations

import os
import secrets
import string
import sys

from dotenv import load_dotenv


def configure_login() -> None:
    """Load configured credentials or create the process-local default password."""
    load_dotenv(override=True)
    os.environ.setdefault("APP_USER", "oci")
    if not os.environ.get("APP_PASSWORD"):
        alphabet = string.ascii_letters + string.digits
        password = "".join(secrets.choice(alphabet) for _ in range(16))
        os.environ["APP_PASSWORD"] = password
        print(f"APP_PASSWORD was not set. Generated startup login password: {password}", flush=True)


if __name__ == "__main__":
    configure_login()
    os.execvpe(
        sys.executable,
        [sys.executable, "-m", "streamlit", "run", "app.py", *sys.argv[1:]],
        os.environ,
    )
