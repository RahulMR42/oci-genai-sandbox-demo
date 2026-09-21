# Infrastructure setup

This folder is intentionally separate from the Streamlit tutorial. It establishes durable OCI resources; the app only invokes a model.

## Target

All resources belong to this compartment in Chicago:

```text
OCI_REGION=us-chicago-1
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..aaaaaaaa75igkvdlzgwy5kly2cyjysezlkmsw436b3uvjeir4mffyz2k2dyq
```

## 1. Get sandbox access, configure user-principal authentication, and add IAM permission

GenAI Sandboxes is limited availability. Request access for the tenancy and whitelist `us-chicago-1` before provisioning. The setup identity needs these policies:

```text
allow group <group-name> to manage generative-ai-sandbox in compartment <compartment-name>
allow group <group-name> to manage generative-ai-project in compartment <compartment-name>
```

Configure the OCI **user-principal** profile named `DEFAULT` in `~/.oci/config`. It must contain the normal user, tenancy, fingerprint, region, and `key_file` values for an OCI API signing key. This project does not use `oci session authenticate` or session tokens.

## 2. Create a sandbox-enabled OCI Generative AI Project

Use the bootstrap script. It creates an OCI Generative AI Project for the tutorial and an API key for local validation. The Oracle GenAI Sandbox beta SDK provisions the managed, isolated sandbox environment under this project context; OCI's OpenAI-compatible Containers integration is a separate path.

```bash
./infra/bootstrap_sandbox_project.sh --apply
```

Copy both printed variables into the root `.env` file:

```dotenv
OCI_GENAI_PROJECT_ID=ocid1.generativeaiproject.oc1.us-chicago-1...
OCI_SANDBOX_PROJECT_ID=ocid1.generativeaiproject.oc1.us-chicago-1...
```

The script installs the current internal preview `oci` SDK into `.venv-infra`; this is necessary because the public SDK may not include the Sandbox API namespace yet.

### Manual alternative

If you need a model-only project without a sandbox, authenticate locally with the OCI CLI, then run:

```bash
oci generative-ai generative-ai-project create \
  --compartment-id "$OCI_COMPARTMENT_ID" \
  --display-name oci-ai-in-5 \
  --query 'data.id' --raw-output
```

Copy the returned OCID to `OCI_GENAI_PROJECT_ID` in the root `.env` file.

## 3. Create an OCI Generative AI API key

Create a Generative AI API key in the OCI Console or CLI, in the same compartment and region. Grant the key permission to use the required model/project, then store one key secret only in `OCI_GENAI_API_KEY` in `.env`.

This is an OCI service key. Do not use an OpenAI API key, and do not commit the OCI secret.

## 4. API-key IAM

The operator who creates the project needs a policy equivalent to:

```text
allow group <group-name> to manage generative-ai-project in compartment <compartment-name>
```

API-key access must also receive the OCI Generative AI API-key permission required for the selected model/project. Restrict this to the model and environment used by the tutorial.

## Why there is no Terraform here yet

Project retention, model selection, and API-key secret rotation are account decisions. The documented OCI CLI workflow keeps those explicit and avoids placing generated key secrets in Terraform state. Add Terraform only once your team has settled those policies.
