# PIPELINE.md

How work gets done on Terrace. Who does what, where it runs, and what reaches
Hanna.

Status: draft v0.1, 13 Aug 2026. Companion to `SPEC.md`.

---

## 1. The shape

Hanna is project lead and reviewer. Claude Code is the engineer. The pipeline
exists to keep Hanna out of everything except the two things only she can do:
deciding what is correct, and approving what ships.

Three lanes, with different amounts of human involvement:

| Lane | Trigger | Human involvement |
|---|---|---|
| Code | Hanna assigns work | Review and approve the pull request |
| Data | Schedule | None when green, review when red |
| Diagnosis | A failed check | Read the summary, decide |

## 2. Machines

**The host.** A Mac mini M4 Pro, always on, running the Claude Desktop app.
This is the only machine that needs to stay awake. Note that no M5 Pro or M5 Max
Mac mini exists as of August 2026; the current line is M4 and M4 Pro, and
reporting about a successor is rumour with no confirmed window.

Host configuration, all of it required rather than nice to have:

- System Settings, Energy: prevent automatic sleep, start up automatically after
  a power failure, wake for network access
- Automatic login enabled, so an unattended restart returns to a desktop with
  the Claude app running
- Claude Desktop set to launch at login
- Screen Sharing enabled for the occasions when something needs hands
- No monitor required

**The clients.** iPhone, iPad Air, MacBook Pro. None of them need to be awake
for work to happen. They are windows onto the host.

## 3. Dispatch, the primary path

Dispatch pairs the Claude mobile app with Claude Desktop and lets Hanna assign a
new task from anywhere. Claude spawns the session on the host and works while
the phone is in a pocket.

Setup, once: open Claude Desktop, go to the Cowork tab, run Dispatch setup, pair
the phone by QR code. Requires a Pro or Max plan. Pairing persists.

Operating facts that shape how it is used:

- Dispatch **creates**. Remote Control **continues**. A Dispatch-assigned coding
  task appears in the Desktop Code tab with a Dispatch badge, and can then be
  steered from the phone with Remote Control.
- A push notification arrives when the session finishes or needs approval.
- App approvals inside Dispatch-spawned Code sessions expire after 30 minutes
  and re-prompt, rather than lasting the session. Long unattended runs will
  interrupt themselves asking for permission again.
- The Desktop app must be running and the host awake. Dispatch is a remote
  control, not cloud compute.

That approval-expiry behaviour is the reason for the division of labour below.

**What goes to Dispatch:** work Hanna initiates and wants done while away.
Implement a metric from a reviewed notebook. Fix a failing assertion. Draft a
component. Investigate a red check. All bounded, all under an hour.

**What does not go to Dispatch:** anything scheduled, anything long-running,
anything that must complete unattended. Those go to GitHub Actions, which has no
approval prompts and no host dependency.

**Remote Control** is the second surface, for steering something already
running. Start it on the host with `claude remote-control` inside `tmux`, or
turn on auto-connect so every session is reachable. Two limits to design around:
the local process must keep running, and a machine that is awake but offline for
more than roughly ten minutes will time out and exit the session.

**Claude Code on the web** is the fallback when the host is unreachable. Cloud
sessions, no local filesystem, fine for documentation and self-contained work.

## 4. GitHub

### 4.1 Branch protection

`main` is protected. Required status checks, listed in section 4.2. A pull
request is required for every change.

Approval is required only through `CODEOWNERS`, which covers `SPEC.md`,
`CLAUDE.md`, `docs/`, `.claude/`, `pipeline/dbt/`, `pipeline/registry/`,
`pipeline/ingest/`, `web/`, and `.github/`.

The consequence is the whole design: a pull request touching only
`pipeline/data/` and `web/public/data/` needs no approval and merges itself when
the checks pass. A pull request touching anything else waits for Hanna. A data
refresh that tries to change a model is by definition not a data refresh, and it
stops.

### 4.2 Required checks

Every one of these is a spec commitment made executable:

1. `dbt build` including all generic tests
2. The five singular assertions: season match counts, club appearances, source
   agreement, registry coverage, tier honesty
3. Guardrail hook run over the diff, so the constraints hold in CI and not only
   in a local session
4. Computed WCAG contrast audit
5. Em-dash and banned-vocabulary grep
6. Typecheck and lint
7. Web build

### 4.3 The token problem

This is the detail that would otherwise break the whole zero-touch path, so it
is written down rather than discovered.

A pull request opened by a workflow using the default `GITHUB_TOKEN` does not
get normal check runs. <cite index="255-1">Current GitHub behaviour is that
pull_request events with opened, synchronize or reopened activity types created
by GITHUB_TOKEN produce workflow runs in an approval-required state, with a
banner in the merge box that a user with write access must click to start
them.</cite> Historically they did not run at all.

Either way the result is the same for us: the data refresh would open a pull
request, auto-merge would sit waiting for checks that never run, and Hanna would
have to tap a button. That is precisely the human involvement this lane exists
to remove.

The fix is a fine-grained personal access token with contents and pull request
write scope, stored as the `AUTOMATION_TOKEN` secret and used for opening the
pull request. Checks then run normally.

### 4.4 The data lane, end to end

1. Scheduled workflow wakes on cron, or Hanna triggers it manually from the
   GitHub app
2. Ingest fetches each registered source into a dated raw snapshot
3. If nothing changed, the run ends and nothing is opened
4. If something changed, the snapshot and rebuilt artefacts are committed to a
   dated branch
5. A pull request opens using `AUTOMATION_TOKEN`, labelled `data`
6. Auto-merge is enabled immediately
7. Required checks run
8. Green: GitHub merges with no human. Vercel deploys on merge.
9. Red: the pull request stays open, a push notification arrives, and the
   diagnosis lane picks it up

The gates run on the pull request rather than inside the refresh job on purpose.
A failed refresh still produces a visible diff to look at, which is worth more
than a red log.

### 4.5 Paging

Paging stays fully on, at all hours, managed through Focus modes on the Apple
account rather than by suppressing anything at the source.

- GitHub mobile app: notifications for failed workflow runs and for pull
  requests awaiting review
- Claude Code push: enable both proactive notifications and action-required
  notifications through `/config` on the host

## 5. Diagnosis

A red check should arrive as a decision, not a log.

Near term, manual: the notification arrives, Hanna assigns the investigation
through Dispatch from the phone, and reads the summary when it lands.

Later, automatic: a Channel forwards the CI failure into a session on the host,
which diagnoses before Hanna looks. Channels pushes events from a chat app or a
custom source into a local session, which is the right shape for this. Deferred
until the manual version has run enough times to know what a useful summary
contains.

Most failures are one of two kinds and they need opposite responses.
`assert_source_agreement` firing because a source revised a scoreline is a
ten-second approval. The same assertion firing because a parser broke is real
work. The summary exists to tell those apart quickly.

## 6. Automation metrics

Collected automatically, per `docs/DECISIONS.md` D-008. A workflow queries the
GitHub API weekly and on demand, writing to `docs/metrics/automation.json`.

Tracked:

- Merged pull requests, split by whether a human committed to the branch
- Human interventions per pull request: review comments, pushes to the branch,
  and re-requested reviews
- Time from branch creation to merge, and from merge to deployment
- Failed required checks by check name, so the noisy assertion is visible
- Guardrail hook blocks by rule, which is the number that says whether a
  constraint belongs in a hook or in prose

The last two are the ones that will actually change how this project is built. A
constraint that keeps blocking is either wrong or badly explained. A constraint
that never blocks was never needed.

## 7. Build order

1. Repository, context files, branch protection with no checks yet
2. Ingest, dbt, the five assertions, running locally
3. `ci.yml`, then wire its jobs as required checks
4. `CODEOWNERS` and the lane split
5. `AUTOMATION_TOKEN`, then `data-refresh.yml` with auto-merge
6. Vercel deploy on merge
7. Mac mini, Dispatch pairing, Remote Control, push notifications
8. `automation-metrics.yml`
9. Channels for automated diagnosis

Steps 3 through 5 are what turn Hanna from operator into reviewer. Step 7 is
what removes the laptop from the critical path. Everything else is convenience.

## 8. Open items

- The hook payload schema used by `.claude/hooks/guardrails.py` needs verifying
  against the current Claude Code hooks reference before CI depends on it.
- Vercel deployment protection settings are unconfigured. An unlisted subdomain
  is not the same as a private one.
- No decision yet on how long dated raw snapshots are retained. They will grow.
