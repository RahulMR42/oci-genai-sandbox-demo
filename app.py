"""Interactive OCI Generative AI Sandbox tutorial, served by Streamlit."""

from __future__ import annotations

import os
import json
from html import escape

import streamlit as st
from dotenv import load_dotenv

from services.oci_openai import OciOpenAIConfig, run_prompt
from services.oci_sandbox import run_hybrid_web_research, run_langgraph_research, run_package_model_artifact, run_single_turn

load_dotenv(override=True)

st.set_page_config(page_title="OCI Sandbox Lab", page_icon="◈", layout="wide")

DEFAULT_COMPARTMENT = "ocid1.compartment.oc1..aaaaaaaa75igkvdlzgwy5kly2cyjysezlkmsw436b3uvjeir4mffyz2k2dyq"


def value(name: str, fallback: str = "") -> str:
    return os.getenv(name, fallback)


def apply_oracle_theme() -> None:
    st.markdown(
        """
        <style>
        :root { --oracle-red: #c74634; --ink: #172033; --mist: #f4f6f9; --line: #d7dce5; --navy: #101827; }
        .stApp { background: var(--mist); color: var(--ink); }
        [data-testid="stSidebar"] { background: var(--navy); }
        [data-testid="stSidebar"] * { color: #f8f7f5 !important; }
        [data-testid="stSidebar"] input { color: #161513 !important; background: #fff !important; }
        .hero { background: linear-gradient(110deg, #101827, #253552); border-left: 7px solid var(--oracle-red); color: #fff;
                 padding: 2.3rem 2.6rem 2.1rem; margin: .3rem 0 1.7rem; }
        .eyebrow { color: #f3695a; font-size: .78rem; font-weight: 700; letter-spacing: .13em;
                   text-transform: uppercase; margin-bottom: .6rem; }
        .hero h1 { font-size: 2.65rem; line-height: 1.06; margin: 0 0 .7rem; color: #fff; }
        .hero p { color: #dedad5; font-size: 1.08rem; max-width: 47rem; margin: 0; }
        .step-card { background: #fff; border: 1px solid var(--line); border-radius: 4px; border-top: 4px solid var(--oracle-red);
                     min-height: 154px; padding: 1.15rem 1.15rem .85rem; margin-bottom: 1.25rem; box-shadow: 0 2px 6px rgba(16,24,39,.05); }
        .step-number { color: var(--oracle-red); font-weight: 800; font-size: .8rem; letter-spacing: .1em; }
        .step-card h3 { margin: .35rem 0 .45rem; font-size: 1.12rem; }
        .step-card p { color: #59544f; font-size: .92rem; }
        .run-badge { background: #e6f4ea; border-radius: 99px; color: #176b3a; display: inline-block;
                     font-size: .7rem; font-weight: 750; letter-spacing: .07em; padding: .22rem .5rem; text-transform: uppercase; }
        .label-chip { background: #eef1f6; border: 1px solid #d7dce5; border-radius: 99px; color: #40506a; display: inline-block;
                      font: 650 .69rem/1.1 Inter, sans-serif; margin: .1rem .22rem .35rem 0; padding: .25rem .48rem; }
        .stButton > button[kind="primary"] { background: var(--oracle-red); border-color: var(--oracle-red); }
        .stTabs [data-baseweb="tab"] { font-weight: 650; }
        .stTabs [aria-selected="true"] { color: var(--oracle-red); }
        .tutorial-heading { border-bottom: 1px solid var(--line); margin: .5rem 0 1.2rem; padding-bottom: .75rem; }
        .tutorial-heading h2 { color: var(--ink); font-size: 1.9rem; margin: .25rem 0; }
        .session-card { background: #fff; border: 1px solid var(--line); padding: 1.15rem; margin: .6rem 0; }
        .session-card h4 { color: var(--oracle-red); font-size: .78rem; letter-spacing: .09em; margin: 0 0 .7rem; text-transform: uppercase; }
        .live-log { background: #0b1020; border: 1px solid #253552; border-radius: 4px; color: #f4f6f9;
                    font: .82rem/1.45 ui-monospace, SFMono-Regular, Menlo, monospace; height: 350px;
                    overflow-y: scroll; scrollbar-gutter: stable; padding: 1rem; scroll-behavior: smooth; }
        .live-log::-webkit-scrollbar { width: 10px; }
        .live-log::-webkit-scrollbar-track { background: #0b1020; }
        .live-log::-webkit-scrollbar-thumb { background: #596579; border-radius: 8px; }
        .execution-entry { border-left: 3px solid #596579; margin: 0 0 1rem; padding: .65rem .8rem; white-space: pre-wrap; }
        .execution-entry.command { border-left-color: #d66a57; background: #171d2c; }
        .execution-entry.output { border-left-color: #5dbb8a; background: #101d20; }
        .execution-entry.activity { border-left-color: #6797d6; background: #111827; }
        .execution-label { color: #c8d5e8; display: block; font: 700 .7rem/1.3 Inter, sans-serif; letter-spacing: .08em; margin-bottom: .35rem; text-transform: uppercase; }
        .console-copy { background: #fff; border: 1px solid #b9c2d0; border-radius: 4px; color: #172033 !important; cursor: pointer; display: block;
                            font: 600 .88rem/1.2 Inter, sans-serif; padding: .55rem .65rem; text-align: center; text-decoration: none; }
        .console-copy:hover { border-color: var(--oracle-red); color: var(--oracle-red) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def console_entry_type(event: str) -> tuple[str, str]:
    if event.startswith("OCI SDK → run_sandbox_command"):
        return "command", "▶ Command"
    if "← command exit" in event or event.startswith("Local executor ←"):
        return "output", "↳ Output"
    if event.startswith("ERROR:"):
        return "output", "⚠ Error"
    return "activity", "● Activity"


def console_markup(entries: list[str], element_id: str, extra_class: str = "") -> str:
    cards = []
    for item in entries:
        style, label = console_entry_type(item)
        cards.append(f'<div class="execution-entry {style}"><span class="execution-label">{label}</span>{escape(item)}</div>')
    content = "".join(cards) or "<span class=\"execution-label\">Ready</span>No execution events have arrived yet."
    return (
        f'<div id="{element_id}" class="live-log {extra_class}">{content}</div>'
        f'<script>const c=document.getElementById("{element_id}"); if(c) c.scrollTop=c.scrollHeight;</script>'
    )


def main() -> None:
    apply_oracle_theme()

    with st.sidebar:
        st.markdown("### OCI Sandbox Lab")
        st.caption("Tutorial workspace · local configuration")
        st.divider()
        st.markdown("**Connection settings**")
        region = st.text_input("Region", value=value("OCI_REGION", "us-chicago-1"))
        compartment_id = st.text_input(
            "Compartment OCID", value=value("OCI_COMPARTMENT_ID", DEFAULT_COMPARTMENT)
        )
        project_id = st.text_input(
            "Generative AI Project OCID",
            value=value("OCI_SANDBOX_PROJECT_ID"),
            key="sandbox_project_id",
        )
        model = st.text_input("Validation model", value=value("OCI_MODEL_ID", "openai.gpt-oss-120b"))
        artifact_model = st.text_input(
            "Artifact model", value=value("OCI_ARTIFACT_MODEL_ID", value("OCI_MODEL_ID", "openai.gpt-oss-120b"))
        )
        api_key = st.text_input(
            "OCI Generative AI API key", value=value("OCI_GENAI_API_KEY"), type="password"
        )
        st.caption("Credentials stay in this browser session and are never saved by the app.")

    st.markdown(
        """
        <section class="hero">
          <div class="eyebrow">Oracle Cloud Infrastructure</div>
          <h1>GenAI Sandbox Lab</h1>
          <p>Build confidence with OCI sandbox concepts through short, hands-on tutorials—then validate that your project can reach an OCI-hosted model.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    overview, tutorial, validate, resources = st.tabs(
        ["Overview", "⭐ Sandbox tutorial", "Validate access", "Resources"]
    )

    with overview:
        st.subheader("A clear path from setup to a safe experiment")
        first, second, third = st.columns(3)
        cards = [
            ("01 · PREPARE", "Choose the boundary", "Use a dedicated compartment and Generative AI project. These define ownership, access, and billing scope."),
            ("02 · SANDBOX", "Create a disposable workspace", "Provision a GenAI Sandbox for an isolated, short-lived experiment. Keep secrets and application work outside the sandbox image."),
            ("03 · VALIDATE", "Prove the connection", "Send a small test request to an OCI-hosted model before moving on to a larger sandbox tutorial."),
        ]
        for column, (number, heading, copy) in zip((first, second, third), cards):
            with column:
                st.markdown(
                    f'<div class="step-card"><div class="step-number">{number}</div><h3>{heading}</h3><p>{copy}</p></div>',
                    unsafe_allow_html=True,
                )
        st.info("This app is a tutorial companion. It does not create or delete OCI resources; use it to understand the workflow and validate project access.")

    with tutorial:
        st.subheader("OCI GenAI Sandbox tutorials")
        st.caption("Each tutorial exposes the command sequence before anything is provisioned.")
        tutorials = {
            "Single-turn command": {
                "tag": "5 MIN · FIRST RUN",
                "labels": ["sandbox", "command", "beginner"],
                "summary": "Create a disposable sandbox, run one shell command, read stdout, then stop it.",
                "trace": [
                    "Create — client.create_sandbox(project_id, CreateSandboxDetails(...))",
                    "Ready — client.get_sandbox(sandbox_id) → RUNNING",
                    "Execute — client.run_sandbox_command_and_wait(sandbox_id, command='pwd && ls -la')",
                    "Clean up — client.stop_sandbox(sandbox_id, StopSandboxDetails(is_force=False))",
                ],
                "code": """created = client.create_sandbox(project_id, CreateSandboxDetails(\n    display_name=\"single-turn-demo\", runtime=\"python-3.11\",\n    shape=\"SMALL\", expiration_duration=\"PT10M\",\n)).data\nwait_until_running(client, created.id)\nresult = client.run_sandbox_command_and_wait(\n    created.id, RunSandboxCommandDetails(command=\"pwd && ls -la\", timeout=\"PT2M\")\n).data\nprint(result.output.stdout)\nclient.stop_sandbox(created.id, StopSandboxDetails(is_force=False))""",
                "language": "python",
            },
            "Multi-turn workspace": {
                "tag": "10 MIN · STICKY SESSION",
                "labels": ["sandbox", "session", "workspace"],
                "summary": "Keep one sandbox ID across turns so files from the first command remain available to the next.",
                "trace": [
                    "Create once — client.create_sandbox(...) → sandbox_id",
                    "Turn 1 — run_and_wait(command=\"echo draft > /workspace/brief.txt\")",
                    "Turn 2 — run_and_wait(command=\"cat /workspace/brief.txt\")",
                    "End session — client.stop_sandbox(sandbox_id, ...)",
                ],
                "code": """# Persist sandbox_id with the user session.\nclient.run_sandbox_command_and_wait(\n    sandbox_id,\n    RunSandboxCommandDetails(command=\"echo 'draft plan' > /workspace/brief.txt\", timeout=\"PT2M\"),\n)\nnext_turn = client.run_sandbox_command_and_wait(\n    sandbox_id, RunSandboxCommandDetails(command=\"cat /workspace/brief.txt\", timeout=\"PT2M\")\n).data\nprint(next_turn.output.stdout)""",
                "language": "python",
            },
            "Agent + OCI sandbox": {
                "tag": "20 MIN · AGENTS API",
                "labels": ["openai-agent", "sandbox", "executor"],
                "summary": "Connect a self-hosted Agents API session to OCI compute; the executor runs agent commands inside the sandbox.",
                "trace": [
                    "Session — create a self-hosted Agents API session with /workspace",
                    "Sandbox — create OCI sandbox and wait for RUNNING",
                    "Executor — install Codex and start codex exec-server",
                    "Agent turn — stream session events and retrieve artifacts from /workspace",
                    "Clean up — stop/delete sandbox, then delete the Agents API session",
                ],
                "code": """npm install -g @openai/codex\ncodex exec-server --environment-id \"$ENVIRONMENT_ID\" \\\n+  --environment-key \"$OPENAI_EXECUTOR_API_KEY\"\n\n# Keep OPENAI_API_KEY in the application. Pass only the executor\n# key into the sandbox as CODEX_API_KEY.""",
                "language": "bash",
            },
            "BYOC sandbox image": {
                "tag": "30 MIN · LIMITED AVAILABILITY",
                "labels": ["custom", "byoc", "container"],
                "summary": "Run a sandbox from a vetted custom image when the standard Python runtime does not include your required tools or dependencies.",
                "trace": [
                    "Build — create and scan a minimal image with only required tools",
                    "Publish — push the approved image to your OCI Container Registry path",
                    "Provision — create the sandbox with the BYOC image configuration",
                    "Verify — run a version check and a least-privilege smoke command",
                    "Clean up — stop the sandbox and retain image provenance outside the session",
                ],
                "code": """# Build and publish an approved, minimal image.\ndocker build -t <region>.ocir.io/<tenancy>/<repo>/sandbox-tools:1.0 .\ndocker push <region>.ocir.io/<tenancy>/<repo>/sandbox-tools:1.0\n\n# BYOC is limited-availability. Use the Oracle-provided beta SDK schema\n# for the image reference supplied to CreateSandboxDetails, then create\n# the sandbox and run an explicit smoke command such as: python --version.""",
                "language": "bash",
            },
            "Package + model artifact": {
                "tag": "15 MIN · ARTIFACT RETURN",
                "labels": ["python", "artifact", "model"],
                "summary": "Install a Python dependency, call an OCI-hosted model from the isolated workspace, then return a generated artifact to the application.",
                "trace": [
                    "Create — start one sandbox for the application request",
                    "Prepare — install the approved Python package inside /workspace",
                    "Run — execute the program and write /workspace/result.json",
                    "Return — read the result file through the sandbox file/command API",
                    "Clean up — stop the sandbox after the artifact is collected",
                ],
                "code": """# The app injects OCI credentials from Vault or Resource Principal; never embed a key.\npython -m pip install --quiet pydantic\npython - <<'PY'\nimport json\nfrom openai import OpenAI\n\nclient = OpenAI(\n    base_url=\"https://inference.generativeai.<region>.oci.oraclecloud.com/openai/v1\",\n    api_key=runtime_oci_api_key(),  # retrieve at runtime, not from source\n    project=\"<sandbox-enabled-project-ocid>\",\n)\nresponse = client.responses.create(model=\"<approved-oci-model>\", input=\"Summarize this job.\")\nopen(\"/workspace/result.json\", \"w\").write(json.dumps({\"result\": response.output_text}))\nPY\ncat /workspace/result.json  # returned to the application as the job artifact""",
                "language": "bash",
            },
            "LangGraph research worker": {
                "tag": "10 MIN · LIVE AGENT WORKFLOW",
                "labels": ["langgraph", "multi-agent", "sandbox"],
                "summary": "Run a stateful LangGraph worker in a dedicated sandbox, persist intermediate research files, and return a structured report.",
                "trace": [
                    "Prepare — install langgraph and the approved tool dependencies",
                    "Plan — graph routes a question through research, synthesis, and review nodes",
                    "Execute — each node writes evidence and intermediate state under /workspace",
                    "Return — application retrieves report.json and node-level execution logs",
                    "Resume — reconnect to the same sandbox ID for an approved follow-up turn",
                ],
                "code": """python -m pip install langgraph openai\n# Research node: configured OCI artifact model.\n# Editor node: openai.gpt-oss-20b.\n# Define a StateGraph with research → editor nodes.\n# Invoke the graph and return the resulting report to the application.\n# Keep credentials in Vault/Resource Principal—not graph source or prompts.""",
                "language": "bash",
            },
            "Hybrid web research relay": {
                "tag": "15 MIN · MULTI-AGENT HANDOFF",
                "labels": ["openai-agent", "multi-agent", "web-search", "local-agent", "sandbox"],
                "summary": "A local planner delegates public-web research to a sandbox worker, then a separate local reviewer turns the returned evidence into a concise answer.",
                "trace": [
                    "Local session A — planner produces a constrained public-web query",
                    "Sandbox session B — worker retrieves public evidence and writes a research memo",
                    "Handoff — application validates the JSON memo returned from the sandbox",
                    "Local session C — reviewer synthesizes only the passed evidence",
                    "Teardown — stop the sandbox after the one bounded research task",
                ],
                "code": """# Local planner session
query = local_model("Create a narrow public-web research query")

# OCI sandbox worker session: urllib retrieves public evidence; OCI model writes memo.
python -m pip install --quiet openai
python sandbox_web_worker.py --query "$QUERY" > memo.json

# Independent local reviewer session receives only memo.json.
answer = local_model(f"Synthesize this validated evidence: {memo_json}")""",
                "language": "python",
            },
            "CSV policy audit": {
                "tag": "8 MIN · DATA CHECK",
                "labels": ["python", "data", "policy", "sandbox"],
                "summary": "Create a small resource inventory in the sandbox, validate ownership fields, and return a machine-readable audit result.",
                "trace": [
                    "Create — provision one disposable sandbox workspace",
                    "Write — create a sample inventory under /workspace",
                    "Audit — run a Python policy check against the file",
                    "Return — stream the JSON audit result to the application",
                    "Clean up — stop the short-lived sandbox",
                ],
                "code": '''printf 'name,owner\\nmodel-api,platform\\nreport-job,\\n' > /workspace/inventory.csv
python -c "import csv, json; rows=list(csv.DictReader(open('/workspace/inventory.csv'))); print(json.dumps({'missing_owner':[r['name'] for r in rows if not r['owner']]}))"''',
                "language": "bash",
            },
            "Release test gate": {
                "tag": "8 MIN · BUILD VALIDATION",
                "labels": ["python", "testing", "release", "sandbox"],
                "summary": "Build a tiny isolated application artifact, execute its test gate, and return the command result before release approval.",
                "trace": [
                    "Create — start a clean sandbox for the release check",
                    "Write — generate a small application module in /workspace",
                    "Test — run the isolated assertion gate",
                    "Return — collect stdout and exit status for approval",
                    "Clean up — stop the sandbox after validation",
                ],
                "code": '''printf 'def add(left, right): return left + right\\n' > /workspace/calculator.py
python -c "from pathlib import Path; exec(Path('/workspace/calculator.py').read_text()); assert add(2, 3) == 5; print('release gate passed')"''',
                "language": "bash",
            },
        }
        runnable_tutorials = {"Single-turn command", "Multi-turn workspace", "Package + model artifact", "LangGraph research worker", "Hybrid web research relay", "CSV policy audit", "Release test gate"}
        if "selected_tutorial" not in st.session_state:
            st.session_state.selected_tutorial = None
        if st.session_state.selected_tutorial is None:
            search_text = st.text_input(
                "Search tutorials or labels",
                placeholder="Try: openai-agent, langgraph, custom, workspace…",
            ).strip().lower()
            matching_tutorials = [
                (name, details)
                for name, details in tutorials.items()
                if not search_text or search_text in " ".join(
                    [name, details["summary"], details["tag"], *details["labels"]]
                ).lower()
            ]
            st.caption("Filter by title, description, or labels such as openai-agent, langgraph, custom, sandbox, and web-search.")
            if not matching_tutorials:
                st.info("No tutorials match that search. Try a broader label such as `sandbox` or `multi-agent`.")
            for row_start in range(0, len(matching_tutorials), 2):
                columns = st.columns(2, gap="large")
                for column, (name, details) in zip(columns, matching_tutorials[row_start:row_start + 2]):
                    with column:
                        run_badge = '<span class="run-badge">Run enabled</span>' if name in runnable_tutorials else ''
                        labels = "".join(f'<span class="label-chip">{escape(label)}</span>' for label in details["labels"])
                        st.markdown(
                            f'<div class="step-card"><div class="step-number">{details["tag"]}</div><h3>{name}</h3>{run_badge}<div>{labels}</div><p>{details["summary"]}</p></div>',
                            unsafe_allow_html=True,
                        )
                        if st.button("Open tutorial", key=f"tutorial-{name}", use_container_width=True):
                            st.session_state.selected_tutorial = name
                            st.rerun()
        else:
            if st.button("← All tutorials"):
                st.session_state.selected_tutorial = None
                st.rerun()
            selected_name = st.session_state.selected_tutorial
            selected = tutorials[selected_name]
            header_text, header_action = st.columns((4, 1))
            with header_text:
                labels = "".join(f'<span class="label-chip">{escape(label)}</span>' for label in selected["labels"])
                st.markdown(f'<div class="tutorial-heading"><div class="step-number">{selected["tag"]}</div><h2>{selected_name}</h2><div>{labels}</div><p>{selected["summary"]}</p></div>', unsafe_allow_html=True)
            with header_action:
                should_run = False
                if selected_name in runnable_tutorials:
                    should_run = st.button("Run tutorial", type="primary", use_container_width=True)
            session_column, execution_column = st.columns((1, 1.25), gap="large")
            with session_column:
                with st.expander("Session lifecycle", expanded=False):
                    for index, item in enumerate(selected["trace"], start=1):
                        st.markdown(f"`{index}` {item}")
                with st.expander("Session boundary", expanded=False):
                    st.write("One sandbox ID maps to one isolated workspace. Keep that ID for follow-up turns; stop it when the user session ends.")
                if selected_name == "Multi-turn workspace":
                    with st.expander("What this covers", expanded=False):
                        st.write("Sticky sandbox ID, durable `/workspace` state, ordered command turns, stdout collection, and explicit session teardown. It does not yet cover snapshots, forks, file-upload APIs, or concurrent users.")
            with execution_column:
                with st.expander("Actual code", expanded=False):
                    st.code(selected["code"], language=selected["language"])
                if selected_name in runnable_tutorials:
                    st.caption("Use the Run tutorial button above to create a short-lived OCI sandbox and stream the real API events below.")
                elif selected_name == "Agent + OCI sandbox":
                    st.warning("Live Agents API execution requires OPENAI_API_KEY and OPENAI_EXECUTOR_API_KEY plus the Oracle sandbox beta SDK. These are intentionally not present in this local configuration.")
                else:
                    st.info("This workflow reuses the same sandbox across turns. Run the single-turn tutorial first to verify OCI sandbox access.")
            st.warning("OCI GenAI Sandboxes are limited-availability. Use the Oracle-provided beta SDK and a sandbox-enabled project before provisioning.")
            executable = selected_name in runnable_tutorials
            if executable:
                # Clear pre-console session content once after a console layout upgrade.
                if st.session_state.get("execution_console_layout") != 5:
                    for key in list(st.session_state):
                        if key.startswith(("tutorial_log_", "tutorial_commands_", "tutorial_timeline_")):
                            del st.session_state[key]
                    st.session_state.execution_console_layout = 5
                timeline_key = f"tutorial_timeline_{selected_name}"
                console_title, console_action = st.columns((5, 1))
                with console_title:
                    st.markdown("#### Live execution console")
                with console_action:
                    st.markdown(
                        '<button class="console-copy" onclick="navigator.clipboard.writeText(document.getElementById(\'execution-console\').innerText)">⧉ Copy console</button>',
                        unsafe_allow_html=True,
                    )
                console_panel = st.empty()

                def render_console(entries: list[str]) -> None:
                    console_panel.markdown(
                        console_markup(entries, "execution-console"),
                        unsafe_allow_html=True,
                    )

                timeline: list[str] = []
            if executable and should_run:
                commands = None
                if selected_name == "Multi-turn workspace":
                    commands = [
                        "echo 'draft plan' > /workspace/brief.txt",
                        "cat /workspace/brief.txt",
                    ]
                elif selected_name == "CSV policy audit":
                    commands = [
                        "printf 'name,owner\\nmodel-api,platform\\nreport-job,\\n' > /workspace/inventory.csv",
                        "python -c \"import csv, json; rows=list(csv.DictReader(open('/workspace/inventory.csv'))); print(json.dumps({'missing_owner':[r['name'] for r in rows if not r['owner']]}))\"",
                    ]
                elif selected_name == "Release test gate":
                    commands = [
                        "printf 'def add(left, right): return left + right\\n' > /workspace/calculator.py",
                        "python -c \"from pathlib import Path; exec(Path('/workspace/calculator.py').read_text()); assert add(2, 3) == 5; print('release gate passed')\"",
                    ]
                try:
                    artifact_payload = None
                    if selected_name == "Hybrid web research relay":
                        event_stream = run_hybrid_web_research(
                            project_id, region, value("OCI_CLI_PROFILE", "DEFAULT"), api_key, artifact_model, compartment_id
                        )
                    elif selected_name == "LangGraph research worker":
                        event_stream = run_langgraph_research(project_id, region, value("OCI_CLI_PROFILE", "DEFAULT"), api_key, artifact_model)
                    elif selected_name == "Package + model artifact":
                        event_stream = run_package_model_artifact(
                            project_id, region, value("OCI_CLI_PROFILE", "DEFAULT"), api_key, artifact_model
                        )
                    else:
                        event_stream = run_single_turn(
                            project_id, region, value("OCI_CLI_PROFILE", "DEFAULT"), commands
                        )
                    for event in event_stream:
                        timeline.append(event)
                        if selected_name == "Package + model artifact" and "ARTIFACT_JSON=" in event:
                            artifact_payload = event.split("ARTIFACT_JSON=", 1)[1].strip()
                        if selected_name == "Hybrid web research relay" and "SANDBOX_MEMO=" in event:
                            artifact_payload = event.split("SANDBOX_MEMO=", 1)[1].strip()
                        render_console(timeline)
                    if selected_name == "Package + model artifact" and artifact_payload:
                        artifact = json.loads(artifact_payload)
                        timeline.append("Local executor → parse result.json and summarize with default model")
                        summary = run_prompt(
                            OciOpenAIConfig(region, compartment_id, project_id, model, api_key),
                            f"Summarize this sandbox artifact in one concise sentence: {artifact['result']}",
                        )
                        timeline.append(f"Local executor ← default-model summary: {summary}")
                    if selected_name == "Hybrid web research relay" and artifact_payload:
                        memo = json.loads(artifact_payload)
                        timeline.append("Local reviewer session C → synthesize the sandbox evidence")
                        review = run_prompt(
                            OciOpenAIConfig(region, compartment_id, project_id, model, api_key),
                            "Write one concise answer based only on this sandbox research memo: " + memo["memo"],
                        )
                        timeline.append(f"Local reviewer output ← {review}")
                except Exception as exc:
                    timeline.append(f"ERROR: {exc}")
                st.session_state[timeline_key] = timeline
            if executable:
                current_timeline = st.session_state.get(timeline_key, [])
                render_console(current_timeline)

    with validate:
        st.subheader("Validate OCI project access")
        st.write("This small request verifies the project credentials that you will use while following sandbox tutorials. It does not create a sandbox.")
        prompt = st.text_area(
            "Test prompt",
            value="Reply with: OCI sandbox project access verified.",
            height=104,
        )
        if st.button("Validate OCI access", type="primary"):
            missing = [
                label
                for label, current in (("Generative AI Project OCID", project_id), ("Generative AI API key", api_key))
                if not current
            ]
            if missing:
                st.error("Add " + " and ".join(missing) + " in the sidebar or .env file.")
            else:
                config = OciOpenAIConfig(region, compartment_id, project_id, model, api_key)
                try:
                    with st.spinner("Validating OCI project access…"):
                        output = run_prompt(config, prompt)
                    st.success("OCI project access validated.")
                    st.markdown(output)
                except Exception as exc:
                    st.error(f"OCI validation failed: {exc}")

    with resources:
        st.subheader("Your tutorial context")
        st.table(
            [
                {"Resource": "Compartment", "Value": compartment_id, "Why it matters": "Sandbox ownership boundary"},
                {"Resource": "Region", "Value": region, "Why it matters": "Feature and model availability"},
                {"Resource": "Generative AI Project", "Value": project_id or "Add during setup", "Why it matters": "Sandbox and model project context"},
                {"Resource": "API key", "Value": "Configured locally" if api_key else "Add during setup", "Why it matters": "Validates model access"},
            ],
            hide_index=True,
        )
        st.markdown("#### What this tutorial app does not do")
        st.write("It does not provision persistent infrastructure, store credentials, or remove resources. Each runnable lab creates only a short-lived sandbox and explicitly requests its stop when complete.")
        st.markdown("#### References")
        st.markdown(
            "- [OCI provider guide for OpenAI environments](https://developers.openai.com/api/docs/guides/agents-api/environments/providers/oci)\n"
            "- [OpenAI Agents SDK: orchestration patterns](https://openai.github.io/openai-agents-python/multi_agent/)\n"
            "- [Oracle GenAI Sandboxes User Guide (internal)](https://confluence.oraclecorp.com/confluence/pages/viewpage.action?pageId=20677439262)"
        )


if __name__ == "__main__":
    main()
