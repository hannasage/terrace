# BOOTSTRAP.md

Ordered setup for the Terrace repository. Delete this file once every box is
ticked.

Two rules govern the ordering, and both come from real traps:

1. **Branch protection goes on last.** Protect `main` before the scaffold is
   pushed and Claude Code cannot push the scaffold.
2. **A check cannot be required until it has run once.** GitHub only offers a
   status check in the protection picker after a workflow has reported it, so
   the workflows must run before protection can reference them.

Steps marked **[H]** are Hanna's and happen in a browser or on the host. Steps
marked **[CC]** are handed to Claude Code in a terminal session. Steps marked
**[H+CC]** are a handoff.

---

## Phase 0: accounts and host

- [X] **[H]** Confirm Claude Max is active on the account that will run Claude
      Code. Remote Control and Dispatch both require a claude.ai subscription
      and neither works with API key authentication.
- [X] **[H]** Order the Mac mini M4 Pro. Everything below works on the MacBook
      until it arrives; nothing is blocked on the hardware.
- [X] **[H]** Decide the final project name. `terrace` is a placeholder and it
      appears in the repository name, the subdomain, and `SPEC.md`. Changing it
      later is cheap but tedious.

## Phase 1: repository skeleton

- [X] **[H]** Create the repository on GitHub. Private is fine and can open
      later. Do not initialise with a README, since the scaffold supplies one.
- [X] **[H]** Clone it locally and copy in the ten scaffold files: `SPEC.md`,
      `CLAUDE.md`, `docs/`, `.claude/`, `.github/`, `scripts/`.
- [X] **[H]** Commit and push to `main` directly. This is the only direct push
      to `main` that will happen; after Phase 5 it is impossible.
- [X] **[H]** Run `claude` once in the project directory to accept the
      workspace trust dialog. Remote Control will not start from an untrusted
      directory, and the dialog never saves trust for a home directory.

## Phase 2: verify the guardrails before trusting them

Do this before writing any project code. The hook is the thing that lets you
delegate, so it gets tested rather than assumed.

- [X] **[H]** Read the current Claude Code hooks reference and confirm the
      payload shape and the blocking exit code match `read_payload` and
      `BLOCK_EXIT` in `.claude/hooks/guardrails.py`. Both are noted in the file
      as needing verification. If they have moved, fix them now.
- [X] **[CC]** "Verify the guardrail hook. For each check in
      `.claude/hooks/guardrails.py`, construct a payload that should be blocked
      and one that should pass, run them, and report a table of results. Do not
      modify the hook."
- [X] **[CC]** "Attempt to write a file at `web/app/api/players/route.ts`."
      This should be blocked. If Claude Code succeeds, the hook is not wired.
- [X] **[H]** Confirm the hook is actually firing in session, not only when
      invoked by hand.

## Phase 3: build tooling, no checks yet

- [X] **[CC]** "Create the Python project: `pyproject.toml` with dbt-core,
      dbt-duckdb, duckdb, polars and pytest, managed by uv. Add a `Makefile`
      with the six targets named in `CLAUDE.md`. Do not implement ingest yet."
- [X] **[CC]** "Write `scripts/guardrails_ci.py`. It takes a base SHA, gets the
      changed files, and runs the same checks as `.claude/hooks/guardrails.py`
      against their content. Share the check functions rather than duplicating
      them."
- [X] **[CC]** "Write `scripts/check_registry.py` and `scripts/publish.py`.
      Both may be stubs that exit zero for now, with a TODO naming what they
      will assert."
- [X] **[CC]** "Scaffold the Next.js app in `web/` with
      `@hannasage/projection-ui` and its peer dependencies. A single page that
      renders one component from the package is enough. Add `typecheck`,
      `lint`, `build` and `audit:contrast` scripts. `audit:contrast` may be a
      stub."
- [X] Open a pull request for each of these. They will not have required checks
      yet, so merge them yourself. This is deliberate practice at the review
      loop before it has teeth.

## Phase 4: make the checks real

- [X] **[CC]** "Implement `pipeline/ingest/` for engsoccerdata and
      football-data.co.uk only. Dated immutable snapshots. Fail closed on an
      unknown club name. Do not touch `pipeline/registry/`."
- [ ] **[H]** Seed `pipeline/registry/clubs.yml` by hand with the canonical
      club list. Claude Code is blocked from this file by design, so it will
      report unknown names and stop until you resolve them.
- [ ] **[CC]** "Build the dbt project: staging, core, marts for match results
      only. Then the five singular assertions from
      `.claude/rules/pipeline.md`."
- [ ] **[CC]** "Run the full build and report which assertions fail."
      `assert_source_agreement` and the completeness check on 2022/23 should
      both fire. That is the pipeline working, not breaking. See
      `docs/DECISIONS.md` D-004.
- [ ] **[H]** Decide how the engsoccerdata 2022/23 hole is represented. It is a
      gap, so it stays a gap, and the assertion needs to know that this specific
      absence is known rather than new.
- [X] Confirm `ci.yml` passes end to end on a pull request.

## Phase 5: protection and the lane split

Only now, once every job in `ci.yml` has reported at least once.

- [X] **[H]** Repository Settings, General, Pull Requests: enable **Allow
      auto-merge**. Without this the auto-merge button never appears and the
      data lane cannot work.
- [X] **[H]** Settings, Branches: protect `main`. Require a pull request before
      merging. Require status checks to pass. Select `house style`,
      `guardrails`, `pipeline` and `web` from the picker.
- [X] **[H]** Do **not** enable "Require approvals" globally. Approval comes
      from `CODEOWNERS` per path, which is what allows a data-only pull request
      to merge unattended.
- [ ] **[H]** Confirm `CODEOWNERS` resolves: open a test pull request touching
      `SPEC.md` and check that review is requested automatically.
- [X] **[H]** Open a second test pull request touching only a file under
      `pipeline/data/` and confirm no review is requested.

## Phase 6: the automation token

- [X] **[H]** Create a fine-grained personal access token scoped to this
      repository only, with Contents write and Pull requests write. Nothing
      else.
- [X] **[H]** Store it as the repository secret `AUTOMATION_TOKEN`.
- [X] **[H]** Set a calendar reminder for its expiry. A silently expired token
      looks exactly like a data source that stopped changing.
- [X] **[H]** Trigger `data-refresh` manually from the GitHub app or the
      Actions tab and watch one full cycle: pull request opens, checks run
      without anyone approving them, merge happens unattended.

---

## Known ordering traps

- Protecting `main` before Phase 1 blocks the scaffold push.
- Requiring a check before it has ever run leaves it permanently pending.
- Enabling "Require approvals" globally kills the unattended data lane.
- Using `GITHUB_TOKEN` instead of `AUTOMATION_TOKEN` for `gh pr create` leaves
  auto-merge waiting on checks in an approval-required state.
- Adding `pipeline/data/` to `CODEOWNERS` removes the data lane entirely.
- The `.claude/settings.json` deny list blocks `curl` and `wget`. Ingest goes
  through Python modules, so this should never bite, and if it does the answer
  is a registered ingest module rather than an exception.
