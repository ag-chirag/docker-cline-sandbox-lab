# Run Cline inside a Docker Shell sandbox

**Yes: Cline CLI can run inside a local Docker Shell sandbox.** This disposable Flask project demonstrates it adding a health endpoint, testing the application, and committing on a sandbox branch with tool auto-approval enabled. The sandbox cannot read the tested synthetic host marker outside its shared project. The host project stays at the starting revision until you explicitly fetch and apply the sandbox branch.

Docker's **Shell** sandbox is used because Cline is not a built-in sandbox agent in the Docker version tested here. Cline is installed and run inside the sandbox, rather than as a host editor extension.

## Requirements

- Docker Desktop with Docker Sandboxes CLI (`sbx`), Git, and a terminal. The recorded run used macOS 15.4.1 on Apple silicon, Docker 29.2.1, `sbx` 0.46.0, and a Linux ARM64 Shell sandbox.
- Cline CLI 3.0.74 installed inside the sandbox. Its Shell image already included Node/npm, Python 3.14.4, and uv 0.13.4.
- A Cline-supported model provider you can authenticate inside the sandbox. This run used **Sign in with ChatGPT** (`openai-codex`) and `gpt-5.6-terra`. The provider can use subscription limits or incur charges; choose access you are authorized to use. No credential belongs in a command, file, recording, or Git commit.
- Access to this repository while it is private.

Check the installed tools:

```sh
sbx version
docker version
git --version
```

## Start from a clean project

```sh
git clone https://github.com/ag-chirag/docker-cline-sandbox-lab.git
cd docker-cline-sandbox-lab
git switch -c demo-baseline 0352eea5c7ceaac3a5fab07a6edce67542368be8
git show eedd7d251fde13710d803e3fe4aa49a05f4170da:prompts/health-route.txt | shasum -a 256
git status --short
git rev-parse HEAD
```

The published repository includes Cline's finished code. The `git switch` command checks out the **baseline** commit so you can replay the task on an application that initially serves only `GET /`. The prompt is absent from that baseline tree. The `git show` command reads it from the pinned delivery commit already present in the clone; its SHA-256 output should be `83b40a65ecea054aeb4551a9e25bd77f5358ee8c868904f86deb6958ef2d0535`. The baseline also includes `project-marker.txt`, which contains synthetic test data. Create another synthetic marker in a disposable host directory outside the project:

```sh
mkdir -p /private/tmp/docker-cline-sandbox-boundary
printf 'OUTSIDE-MARKER-CLINE-2026-11-05\n' > /private/tmp/docker-cline-sandbox-boundary/outside-marker.txt
```

Use only synthetic markers for this boundary check; do not point the example at personal files.

## Create the private-copy sandbox

From the repository root:

```sh
sbx create --clone --name cline-flask-lab shell "$PWD"
sbx ls
sbx exec cline-flask-lab git switch -C main 0352eea5c7ceaac3a5fab07a6edce67542368be8
sbx exec cline-flask-lab git config user.name 'Cline Sandbox'
sbx exec cline-flask-lab git config user.email 'cline-sandbox@localhost'
sbx exec cline-flask-lab bash -lc 'npm install -g cline@3.0.74'
sbx exec cline-flask-lab cline --version
sbx exec cline-flask-lab cline --help
sbx exec cline-flask-lab bash -lc 'uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt'
```

`--clone` gives the sandbox its own Git working copy. The explicit `git switch` inside it ensures the baseline regardless of which branch the clone initially selects. The repository-local Git identity lets Cline commit without adding your personal address or changing global Git settings. The host repository is mounted read-only as a source, and `sbx` adds a temporary Git remote for fetching work back to the host. Fetching allows review; it does not automatically merge the sandbox branch into your host branch. The `.venv` directory is ignored by Git. The Shell image's system Python lacked `ensurepip`, so the recorded run used its preinstalled `uv` rather than `python -m venv`.

Authenticate a provider from inside the sandbox:

```sh
sbx exec -it cline-flask-lab cline auth
```

For the recorded route, choose **Sign in with ChatGPT**, finish the browser sign-in, select **GPT-5.6 Terra**, and verify Cline reports that setup is complete. Cline's CLI option for unattended tool approval is `--auto-approve true`. That controls Cline's tool prompts; Docker's sandbox boundary is a separate control. If Docker pauses a required provider connection, inspect `sbx policy approval ls` and respond only to a domain you recognize for your chosen provider. This run did not change the global network policy.

## Run and review the bounded task

The [exact prompt](prompts/health-route.txt) asks Cline to create `cline/health-route`, add and test `GET /health`, try both marker reads, and commit without pushing. From the **host** repository root, read that prompt from the pinned delivery commit, even though your working tree is on the baseline. Check its hash before invoking Cline:

```sh
PROMPT_COMMIT=eedd7d251fde13710d803e3fe4aa49a05f4170da
PROMPT_SHA256=83b40a65ecea054aeb4551a9e25bd77f5358ee8c868904f86deb6958ef2d0535
test "$(git show "$PROMPT_COMMIT:prompts/health-route.txt" | shasum -a 256 | awk '{print $1}')" = "$PROMPT_SHA256"
PROMPT_WITH_SENTINEL=$(git show "$PROMPT_COMMIT:prompts/health-route.txt"; printf x)
PROMPT_TEXT=${PROMPT_WITH_SENTINEL%x}
sbx exec cline-flask-lab cline -P openai-codex --auto-approve true --json --timeout 600 "$PROMPT_TEXT"
```

The sentinel preserves the prompt's trailing newline when shell command substitution reads the Git object. The recorded run passed the same prompt as a single argument through a local subprocess wrapper to save its JSON events. Its actual tool actions, exit statuses, and test output are in the [sanitized action record](evidence/cline-tool-actions.md). The resulting Cline commit is `8d453345b237f5158e3efb061a4e6ee2eec1063a`; your replay will produce a different commit SHA. The health route returns:

```json
{"status":"ok"}
```

Keep the sandbox attached in another terminal while you fetch so the temporary Git remote is available:

```sh
sbx run --name cline-flask-lab
```

Review the sandbox work from the host repository before applying it:

```sh
git remote -v
git fetch sandbox-cline-flask-lab cline/health-route
git log --oneline --decorate demo-baseline..FETCH_HEAD
git diff --stat demo-baseline..FETCH_HEAD
git diff demo-baseline..FETCH_HEAD
git switch -c reviewed-health FETCH_HEAD
```

Fetching imports Git objects for inspection and leaves the host files unchanged; `git switch` explicitly checks out the reviewed result afterward. If you use another sandbox name, use the remote shown by `git remote -v`. Removing the sandbox will not undo a commit already fetched or applied on the host. In the recorded run, the reviewed Cline commit was fast-forwarded into the host repository before the sandbox was removed.

## Check the file boundary

Run direct shell controls from the host:

```sh
sbx exec cline-flask-lab cat project-marker.txt
sbx exec cline-flask-lab cat /private/tmp/docker-cline-sandbox-boundary/outside-marker.txt
cat /private/tmp/docker-cline-sandbox-boundary/outside-marker.txt
```

In the recorded private-copy run, Cline's file-read tool and a direct shell command both read the project marker successfully (the shell returned exit 0). Cline's shell command and an independent direct shell command both failed to read the host marker under `/private/tmp` (`No such file or directory`, exit 1). The host marker remained intact. A model declining a file read is not itself proof of an OS boundary; the direct shell control separates those observations. These results are specific to this configuration and these paths.

The committed tests also passed after a stop and reconnect. An independent run of the listening Flask server returned HTTP 200 for `/` and `/health`, and HTTP 404 for `/missing`. The short [terminal recording](evidence/verification.cast) contains a printed authentication and task summary followed by verification output; it does not record the live sign-in or full Cline session. The [tool action record](evidence/cline-tool-actions.md) and [verification record](evidence/verification.md) provide the task details. Play the recording with `asciinema play evidence/verification.cast` if you have asciinema installed; viewing the application and replaying the task do not require it.

## Reconnect and clean up

```sh
sbx stop cline-flask-lab
sbx run --name cline-flask-lab
```

Stopping preserves sandbox state. Before deleting the sandbox, fetch and inspect any branch you want to keep. Deletion removes the sandbox's own state; it does not remove commits already fetched into the host repository or undo changes applied there.

```sh
sbx rm cline-flask-lab
rm -f /private/tmp/docker-cline-sandbox-boundary/outside-marker.txt
rmdir /private/tmp/docker-cline-sandbox-boundary
```

`sbx rm` requires confirmation and permanently removes that sandbox. Run it only when you are finished with the sandbox copy. In the recorded run, `sbx ls` reported no sandboxes after removal, while the fetched commit and code remained in the host repository.

## Limits

This is a local Shell sandbox demonstration on one Mac. It does not test Docker Cloud Sandboxes, other host operating systems, or every possible filesystem path; it does not establish universal escape prevention. No separate network-policy comparison was run. The Cline account sign-in path returned `Token registration failed: 403`, so the successful run used ChatGPT sign-in. The Docker CLI, Cline CLI, model provider, and authentication flows may change; check their current help and documentation if commands differ.
