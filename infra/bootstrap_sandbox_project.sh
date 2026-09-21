#!/usr/bin/env bash
# Creates one sandbox-enabled OCI Generative AI Project and a dedicated API key.
# Usage: ./infra/bootstrap_sandbox_project.sh --apply

set -euo pipefail

readonly DEFAULT_COMPARTMENT_ID="ocid1.compartment.oc1..aaaaaaaa75igkvdlzgwy5kly2cyjysezlkmsw436b3uvjeir4mffyz2k2dyq"
readonly PROJECT_NAME="${OCI_SANDBOX_PROJECT_NAME:-oci-ai-in-5-sandbox}"
readonly API_KEY_NAME="${OCI_SANDBOX_API_KEY_NAME:-oci-sandbox-demo-key}"
readonly REGION="${OCI_REGION:-us-chicago-1}"
readonly COMPARTMENT_ID="${OCI_COMPARTMENT_ID:-$DEFAULT_COMPARTMENT_ID}"
readonly PROFILE="DEFAULT"
readonly VENV_DIR="${OCI_SANDBOX_VENV:-.venv-infra}"
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ENV_FILE="$PROJECT_ROOT/.env"

if [[ "${1:-}" != "--apply" ]]; then
  cat <<EOF
Dry run: this command will create a sandbox-enabled OCI Generative AI Project and API key.
Target compartment: $COMPARTMENT_ID
Target region:      $REGION
Project name:       $PROJECT_NAME

Before applying, request GenAI Sandbox limited-availability access and configure
the DEFAULT user-principal profile in ~/.oci/config (user, tenancy, fingerprint,
region, and key_file).

Run again with --apply after installing the Oracle-provided beta SDK wheel.
EOF
  exit 0
fi

if ! command -v python3 >/dev/null; then
  echo "python3 is required." >&2
  exit 1
fi

if [[ ! -f "$HOME/.oci/config" ]]; then
  echo "OCI configuration was not found. Configure the DEFAULT user-principal profile in ~/.oci/config." >&2
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi

if [[ -n "${OCI_SANDBOX_SDK_WHEEL:-}" ]]; then
  "$VENV_DIR/bin/pip" install --upgrade "$OCI_SANDBOX_SDK_WHEEL"
elif ! "$VENV_DIR/bin/python" -c 'import oci.generative_ai_sandbox' >/dev/null 2>&1; then
  echo "Install the Oracle-provided sandbox beta SDK wheel first, for example: OCI_SANDBOX_SDK_WHEEL=/path/to/oci-beta.whl $0 --apply" >&2
  exit 1
fi

if ! "$VENV_DIR/bin/python" -c 'import oci' >/dev/null 2>&1; then
  env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
    "$VENV_DIR/bin/pip" install \
    --trusted-host=artifactory.oci.oraclecorp.com \
    -i https://artifactory.oci.oraclecorp.com/api/pypi/global-dev-pypi/simple \
    -U 'oci>=2.186.1,<3'
fi

existing_api_key=""
if [[ -f "$ENV_FILE" ]]; then
  existing_api_key="$(sed -n 's/^OCI_GENAI_API_KEY=//p' "$ENV_FILE" | head -n 1)"
fi

OCI_REGION="$REGION" \
OCI_COMPARTMENT_ID="$COMPARTMENT_ID" \
OCI_CLI_PROFILE="$PROFILE" \
OCI_SANDBOX_PROJECT_NAME="$PROJECT_NAME" \
OCI_SANDBOX_API_KEY_NAME="$API_KEY_NAME" \
OCI_EXISTING_APP_API_KEY="$existing_api_key" \
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
  "$VENV_DIR/bin/python" - <<'PY'
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import oci
from oci.generative_ai import GenerativeAiClient
from oci.generative_ai.models import (
    CreateApiKeyDetails,
    CreateGenerativeAiProjectDetails,
    KeyDetails,
    ManagedSandboxOutboundNetworkingConfig,
    SandboxAllowAllNetworkPolicy,
    SandboxConfig,
)

region = os.environ["OCI_REGION"]
compartment_id = os.environ["OCI_COMPARTMENT_ID"]
profile = os.environ["OCI_CLI_PROFILE"]
project_name = os.environ["OCI_SANDBOX_PROJECT_NAME"]
api_key_name = os.environ["OCI_SANDBOX_API_KEY_NAME"]
existing_api_key = os.environ.get("OCI_EXISTING_APP_API_KEY")
endpoint = f"https://generativeai.{region}.oci.oraclecloud.com"
config = oci.config.from_file(profile_name=profile)
oci.config.validate_config(config)
client = GenerativeAiClient(config=config, service_endpoint=endpoint)

projects = client.list_generative_ai_projects(compartment_id=compartment_id).data
for existing in projects.items:
    if existing.display_name == project_name and getattr(getattr(existing, "sandbox_config", None), "is_enabled", False):
        project_id = existing.id
        break
else:
    created = client.create_generative_ai_project(
        CreateGenerativeAiProjectDetails(
            compartment_id=compartment_id,
            display_name=project_name,
            description="Project for OCI GenAI Sandbox tutorials.",
            sandbox_config=SandboxConfig(
                is_enabled=True,
                sandbox_outbound_networking_config=ManagedSandboxOutboundNetworkingConfig(
                    network_policy=SandboxAllowAllNetworkPolicy(),
                ),
            ),
        )
    ).data
    project_id = created.id

deadline = time.monotonic() + 600
while time.monotonic() < deadline:
    project = client.get_generative_ai_project(project_id).data
    if project.lifecycle_state == "ACTIVE":
        break
    if project.lifecycle_state == "FAILED":
        raise RuntimeError(f"Project creation failed: {project_id}")
    print(f"Project state: {project.lifecycle_state}; waiting…")
    time.sleep(10)

else:
    raise TimeoutError("Project did not reach ACTIVE within 10 minutes.")

if existing_api_key:
    print(f"OCI_GENAI_PROJECT_ID={project_id}")
    print(f"OCI_SANDBOX_PROJECT_ID={project_id}")
    print("Reused the API key already configured in .env.")
    raise SystemExit(0)

created_key = client.create_api_key(
    CreateApiKeyDetails(
        compartment_id=compartment_id,
        display_name=api_key_name,
        description="Local credential for OCI Containers API sandbox tutorials.",
        key_details=[
            KeyDetails(
                key_name=api_key_name,
                time_expiry=datetime.now(timezone.utc) + timedelta(days=90),
            )
        ],
    )
).data

secret = next((item.key for item in created_key.keys or [] if item.key), None)
if not secret:
    raise RuntimeError("OCI created the API key but did not return its one-time secret.")

print(f"OCI_GENAI_PROJECT_ID={project_id}")
print(f"OCI_SANDBOX_PROJECT_ID={project_id}")
print(f"OCI_GENAI_API_KEY={secret}")
print("Project is ACTIVE; API key created with a 90-day expiry.")
PY
