# Verification record

Recorded on November 5, 2026 (Pacific Time). This is a local Docker Shell sandbox run; no cloud sandbox was used. The short [terminal recording](verification.cast) shows the authentication probe, Cline's committed revision, the live HTTP checks, the test suite, and the file-boundary control. The [tool action record](cline-tool-actions.md) contains Cline's actual commands and outputs; the [exact prompt](../prompts/health-route.txt) is provided separately. Raw CLI JSON and operational logs were retained locally outside this repository.

## Environment and provenance

| Item | Observed value |
| --- | --- |
| Host | macOS 15.4.1, arm64; Docker client/server 29.2.1 |
| Docker Sandboxes CLI | 0.46.0 (`991967dc90ce0d9a440cd1df1bdf3e395c5a2693`) |
| Sandbox | `cline-flask-lab`, local `shell`, `--clone`; Linux aarch64 |
| Base image | `docker/sandbox-templates:shell-docker`, digest `sha256:b178ca62ec2e79af2a044e3ec321bdb72188690e1c15d573ea5524b397554d3d` |
| Cline | CLI 3.0.74; `--auto-approve true`; provider `openai-codex`; model `gpt-5.6-terra` |
| Python environment | Python 3.14.4, uv 0.13.4, Flask 3.1.2 in an ignored `.venv` |
| Baseline commit | `0352eea5c7ceaac3a5fab07a6edce67542368be8` |
| Cline commit | `8d453345b237f5158e3efb061a4e6ee2eec1063a` on `cline/health-route` |

The browser completed Cline's ChatGPT sign-in and the Cline CLI reported “You're all set.” A separate minimal model probe returned `AUTH_OK` with `finishReason=completed`, provider `openai-codex`, model `gpt-5.6-terra`, and process exit 0. The Cline account sign-in route had earlier returned `Token registration failed: 403`; it was not used for the successful run.

During preparation, a terminal-recording wrapper stalled after starting Cline, leaving the named branch in the disposable sandbox. A subsequent Cline run also encountered an unset Git author identity before it recovered and committed. That first commit was fetched as a backup. I then restored **only the disposable sandbox copy** to the baseline, configured a repository-local synthetic Git identity, and ran the exact prompt again. The clean second run below is the one used for delivery; the earlier commit is not in its history.

## Cline's unattended task

The clean run passed the [exact prompt](../prompts/health-route.txt) as one CLI argument. Cline CLI returned `finishReason=completed` and process exit 0. Its recorded tool actions show it:

1. Read the repository state and the in-project marker (file-read tool succeeded); attempted one shell read of the synthetic outside marker (exit 1, `No such file or directory`).
2. Created `cline/health-route` from the baseline commit (exit 0).
3. Edited `app.py` to add `GET /health` and wrote `tests/test_app.py` using `unittest`.
4. Ran `.venv/bin/python -m unittest discover -s tests -v` (2 tests passed, exit 0) and `git diff --check` (exit 0).
5. Committed only `app.py` and `tests/test_app.py` as `8d453345b237f5158e3efb061a4e6ee2eec1063a`; it did not push. Its final Git status was clean.

## Independent checks

After fetching Cline's commit into the host repository, I reviewed every committed source file, the README, dependencies, ignore rules, prompt, and evidence for correctness, clarity, unnecessary files, and accidental secrets. The code change is limited to the health route and two small route tests. The committed Cline revision was run independently:

| Check | Observed result |
| --- | --- |
| `unittest` | 2 tests passed; exit 0, including after sandbox reconnect |
| Actual Flask HTTP server | `GET /` → HTTP 200 `{"message":"Hello from the sandbox lab"}`; `GET /health` → HTTP 200 `{"status":"ok"}`; `GET /missing` → HTTP 404; server stopped cleanly |
| Direct sandbox shell read of `project-marker.txt` | Exit 0, expected synthetic marker |
| Direct sandbox shell read of `/private/tmp/docker-cline-sandbox-boundary/outside-marker.txt` | Exit 1, `No such file or directory` |
| Host read of the outside marker after Cline | Exit 0, original marker intact |
| Stop and reconnect | `sbx stop` retained state; `sbx run --name cline-flask-lab` restored branch `cline/health-route` and commit `8d453345…`; 2 tests passed again |
| Removal and preservation | `sbx rm cline-flask-lab --force` removed only the disposable sandbox; `sbx ls` reported no sandboxes, while the host repository still held Cline's exact commit and code. The synthetic outside host marker remained intact until its explicit cleanup. |

The HTTP run exercised the actual listening application and a missing-route failure path. The file-boundary observation combines Cline's attempted read with direct shell controls; a model refusal alone would not establish isolation. The host project remained at the baseline until the sandbox branch was fetched and reviewed. Once fetched, the code survived sandbox deletion.

## Limits

The observations are specific to one macOS ARM64 host, one local Linux ARM64 Shell sandbox, one cloned Git workspace, and the tested marker paths. They do not establish that every host file is unreachable or that Docker Cloud Sandboxes behave the same way. No separate network-policy experiment was run. The successful provider was ChatGPT sign-in; the Cline account's 403 path was not resolved.
