# Prompt — sync a prototype to the latest designmd components

Paste this into a Claude Code session, replacing `<PROTOTYPE>` with the target
(e.g. `features/rob/index.html`). It refreshes a prototype's inlined design
system and, crucially, does the analysis `inline.py` can't: deciding which
designmd state to inline, catching breaking changes, and verifying the result.

Prototypes **inline** the design system into one `<style>` block (bounded by the
`/* === tokens.css === */` marker) plus an icon sprite and inline logo.
`designmd/inline.py` refreshes all three in place and is idempotent — it leaves
every other `<style>` block, all markup, and all JS untouched. This prompt wraps
that tool with the judgment a blind re-inline would miss.

---

You are syncing `<PROTOTYPE>` to the current designmd component library. Work
locally; do not commit, push, or open a PR unless I explicitly ask.

**1. Establish the source state.** In `designmd/`, run `git status --short` on
`tokens.css semantic.css components.css devtools.css icons.svg assets/logo.svg`.
- If they're clean, inline as-is.
- If any are **modified/uncommitted**, show me the diff and treat that work as
  unreleased by default. Inline the **committed HEAD** instead (stash the WIP:
  `git stash push -m "…" <files>`, inline, then `git stash pop`). Only inline the
  working tree if I tell you that WIP is ready. Note the branch — designmd may
  not be on `main`.

**2. Find the drift, and the breaking changes.** Before inlining, diff the
prototype's inlined block against the designmd source you chose. Sort what you
find into:
- **Safe refreshes** — a component's rules changed (e.g. the avatar gained its
  chamfered corner), or a new component was added (progress bar). These flow in
  cleanly.
- **Breaking changes** — a class the prototype's *markup* uses was **renamed or
  removed** in designmd. `inline.py` only swaps CSS; it will not touch markup, so
  a removed class silently strips styling off live elements. For every class that
  disappeared from the source, `grep` the prototype's markup for it. Example from
  a past sync: designmd removed `.topbar-avatar` in favour of `.avatar.avatar-md`,
  but `rob` still had `<a class="topbar-avatar">` — inlining that removal would
  have left an unstyled link. **List these for me before proceeding**; each needs
  a matching markup edit, which is a separate decision.

**3. Back up, then inline.** Copy the prototype to the scratchpad first. Then run
`python3 designmd/inline.py <PROTOTYPE>` (with the stash dance from step 1 if
inlining committed state).

**4. Verify the scope is contained.** Diff post-inline against the backup. Every
hunk must fall inside the design-system `<style>` block or the icon sprite
region — nothing in the feature-specific `<style>` blocks, the markup, or the JS.
If a hunk lands outside those, stop and show me: the prototype's inlined block may
have been hand-edited and drifted from a clean inline.

**5. Verify it renders.** Serve the prototype (`.claude/server.mjs`, or the
project's preview) and load it in the browser. For each component that changed,
confirm it renders correctly — computed styles *and* a screenshot (a tiny avatar
won't show a corner cut; render a large sample if needed). Confirm the
prototype's own behaviour still works (open its modals, exercise its JS) and the
console is error-free.

**6. Report.** Tell me: which components refreshed, which new ones arrived, any
breaking changes that still need a markup edit, and the before/after file size.
Leave it uncommitted unless I asked otherwise.

---

## Notes

- **Why committed-by-default:** an uncommitted designmd edit is unreleased and may
  be half-finished (the `.topbar-avatar` migration above was mid-flight). Shipping
  it into a prototype spreads work-in-progress the same way committing a whole
  dirty file would.
- **`inline.py` is idempotent** — re-running it re-inlines the latest CSS without
  ballooning the file, and detects the existing block via its markers. Safe to run
  repeatedly.
- **Batch:** the tool takes multiple paths (`python3 inline.py a.html b.html …`).
  To sync every prototype, run steps 2 and 4–5 per file — the breaking-change and
  render checks are per-prototype, since each has different markup.
- **What the tool deliberately skips:** any `<style>` block that isn't the
  design-system one, so a feature's one-off overrides survive.
