# UX copy

How words are written in Operationalize. The components are in `AGENTS.md` and
`dist/kit.json`; this file is the text that goes in them.

It folds in Toptal's earlier **UX Content Style Guide**, which still governs
spelling, numbers, dates and company vocabulary. Where this file departs from
that guide it says so, in [Where this departs from the old guide](#where-this-departs-from-the-old-guide)
— so nobody re-imports a rule from the old document that was dropped on
purpose.

**What to call things** is not here. Product vocabulary — Process, Activity,
Initiative, Project, RoB, Key Result — comes from the product itself: the test
oracle's glossary (`topteam/test-oracle/`, §7 of `00-system-overview.md`),
summarized for prototypes in `features/CONTEXT.md`. It changes with the
product, and designmd is meant to outlive it. This file is about
*how* to write, and should hold for any Toptal product built on the kit.

## The one rule

**Write the words the user would say.** Then cut everything that is not load
bearing. A label is not a sentence, a sentence is not a paragraph, and almost
nothing on a screen needs a paragraph.

---

## Voice: BASE

Toptal's voice is **BASE**. Each quality has a failure mode, and the failure
mode is usually the one a prototype drifts into.

| | Is | Is not |
|---|---|---|
| **Bold** | assertive, independent, confident | brash, intimidating, shocking |
| **Authentic** | human, understanding, real | jargon, hard sell, contrived |
| **Serious** | professional, credible, relevant | boring, stuffy, lecturing |
| **Energetic** | driven, dynamic, intense | exaggerated, aggressive, over the top |

In a work tool, **Serious** leads. The register is a competent colleague telling
you what happened — not a brand, not an assistant, not a friend.

### The brand voice, in the platform

[operationalize.com](https://operationalize.com) is marketing: it is written
to sell. The platform is B2B SaaS that people work in all day, so it doesn't
borrow the site's words. It borrows the site's **habits**. These are how the
brand sounds, and they carry over to every surface below:

| On the site | In the platform |
|---|---|
| **Outcome first.** Features are named by what they get you: *Track the impact of work · Run meetings that drive results.* | Lead with what the user can now do or get, not with how the screen works. |
| **Verb + object.** *Map ownership · Connect meetings · Measure the impact.* | Headings, steps, actions and announcement titles start with a verb. |
| **Confident, no hedging.** *"Operationalize connects processes, people, communication, and metrics."* | State things plainly. No *"may"*, *"try to"*, *"should hopefully"* when the product knows. |
| **Concrete.** It names Zoom, Slack, and Google Calendar, and puts numbers on outcomes: *"80% reduction in time-to-schedule interviews."* | Name the screen, the integration, the count. *"3 processes have no owner"*, not *"Some items need attention"*. |
| **The method, not just the tool.** Built on OKRs, RACI and cadenced meetings that Toptal proved on itself. | Where the user learns something (an empty state, onboarding, a new feature), say *why* in one line, in terms of the framework. |
| **Remove the worry.** *"No credit card or commitment needed."* under every sign-up. | A step that feels permanent gets one reassuring line: *"You can change the owner later."* |
| **People.** *"3,000+ people using Operationalize."* | Never "users" (principle 1). |

What stays on the site is the **volume**, not the voice. These words don't
belong in the platform, not even in a feature announcement:

> *ultimate · command center · world-class · best-in-class · unparalleled ·
> unmatched · seamless(ly) · robust · powerful · transform · unlock ·
> effortless · perfect fit · take full control*

How loud the voice gets depends on the surface. **Errors and confirmations are
the Serious end of BASE**: plain, short, no personality. **Empty states and
onboarding** can teach. **New-feature announcements** are the one place the
Energetic end shows. They are still product copy, so no superlatives.

## Seven principles

1. **People, not users.** Human, empathetic language. Never "users" in the UI —
   say who they are: *owner*, *member*, *assessor*, or just "you". No gendered
   language; "they" when the person is unknown. The one exception is billing,
   where a seat is a seat: *"$49.99 per user, per month"*.
2. **Be concise.** Write for reading speed and embrace the constraint. A short,
   useful line beats a paragraph that explains.
3. **You, not me.** Second person — *"your initiatives"* — by default. First
   person only where the user is naming their own thing: *My profile*, *My
   tasks*. Never mix the two in one place (*"Change your settings in My
   account"* is fine; *"Your my tasks"* is not).
4. **Be clear and straightforward.** Any reading level, no jargon, no slang.
   **What the team calls it internally is not what the user sees** — no code
   names, table names, or ticket shorthand on a screen.
5. **Inspire action.** Specific, goal-oriented verbs. The user should know what
   to do next without hunting for it.
6. **Be positive.** Say what someone *can* do, not what they can't. Avoid
   "never" and "can't" in UI text when a positive form exists: *"Available
   once the cycle launches"*, not *"You can't do this yet."*
7. **Suggestive, not directive.** Help, don't order. *"Add an owner to track
   progress"* — not *"You must add an owner."*

## Tone, in practice

- **Address the user as "you".** Use "we" only for things the company actually
  did: *"We couldn't reach Tableau."* Never "we" for the user's own action.
- **No exclamation marks** — with one exception: a welcome phrase on a first-run
  screen (*"Welcome to Operationalize!"*). Not in success messages, not in
  errors, not anywhere else.
- **No "Oops", "Whoops", "Uh oh", "Sorry about that".** A failure is
  information, not an apology. No humor in errors.
- **No "Please".** *"Enter an end date"* — not *"Please enter an end date"*. It
  reads as pleading, and it is one more word on every field in the product.
- **"Thank you", not "Thanks"** — when thanks are warranted at all.
- **Do not congratulate.** The user filed a form; they do not need "Great job".
- **Never blame.** *"That file isn't a .csv"*, not *"You uploaded the wrong
  file type."*
- **Contractions almost everywhere** — "can't", "won't", "doesn't". They read
  the way people speak and they are shorter. Use judgment where the formal form
  is clearer.

---

## Writing style

### American English

Toptal is an American company. Spell and standardize accordingly.

- **Spelling:** *canceled, color, favor, organization, prioritize, center.*
- **Currency:** US dollars with the dollar sign — *$1,300.75*.
- **Fallback:** when this file is silent, the
  [AP Stylebook](https://www.apstylebook.com) decides.

### Tense and voice

- **Present tense for what the product does:** *"Owners see every key result"*,
  not *"Owners will be able to see…"*.
- **Simple verb forms when past or future is needed:** *"When does the cycle
  start?"*, not *"When will the cycle be starting?"*
- **Active voice:** *"Sam approved the plan"*, not *"The plan was approved by
  Sam."* Passive only when the actor is unknown or irrelevant.

### Punctuation

- **Oxford comma:** *owners, assessors, and members.*
- **Periods on full sentences** — body text, hints, errors, toasts, tooltips.
  **No period** on a label, a heading, a button, a tab, a menu item or a link.
- **En dash with spaces for ranges:** *Oct 3 – Nov 14, 2026*, *5:00 AM – 10:00 PM*.
- **Em dash with no spaces for a break in a sentence:** *"90-day trial—no
  credit card needed."* That is how operationalize.com writes it. Use it
  sparingly in the product; a period is usually better.
- **Acronyms are spelled out once, where something is taught** — onboarding,
  an empty state, a help panel: *OKRs (Objectives and Key Results)*, *RACI
  (Responsible, Accountable, Consulted, Informed)*. Never in chrome, a table
  or a label, where the acronym is the name. Plurals take no apostrophe:
  *OKRs*, *RACIs*.
- **Question marks** only on a real question — a confirmation modal title is one.

## Capitalization

**Sentence case everywhere.** Buttons, headings, menu items, field labels,
column headers, tabs, badges, tags, toasts, modal titles, empty states, links.

> New initiative · End date · In review · Delete process

Capitals only for proper nouns: people, companies, integrations, and named
bodies such as TopTeam. Never Title Case, never ALL CAPS in copy — if something
needs to shout, that is a styling decision, not a spelling one.

- **The things the product manages are common nouns.** Lowercase mid-sentence:
  *"Connect meetings to your processes"*, *"3 initiatives need an owner"*. They
  are capitalized only where sentence case already puts a capital — first word,
  nav item, page title. operationalize.com writes them this way throughout.
- **Acronyms keep their capitals** — *OKR, RACI, KPI* — and so does their
  spelled-out form: *Objectives and Key Results*.
- **Operationalize is always capitalized and is never a verb** in the product.
  The site's *"2,850+ processes Operationalized"* is marketing play.

This is a deliberate departure from the old guide, which used Title Case for
headers, labels and buttons. See the end of this file.

---

## Buttons

**The label names the outcome, as a verb, in the user's words — in one to
three words.** Read it with the heading above it: *"Delete initiative?" →
"Delete initiative"* should make sense as an answer to the question the screen
is asking.

| Use | When |
|---|---|
| **Save** | persisting changes to something that already exists |
| **Create** | making a new thing — *"Create initiative"* |
| **Add** | attaching an existing thing to another — *"Add owner"* |
| **Submit** | sending something for **someone else's** review or approval |
| **Done** | closing a surface where everything already saved as you went |

**Submit is not a generic OK.** It means a thing leaves the user's hands and
someone else now acts on it. If nothing leaves their hands, it is Save or
Create. This is the single most common mislabel.

- **Name the object when there is room.** *"Create initiative"* beats
  *"Create"*; in a modal whose title already says it, *"Create"* is fine.
- **Never OK, Yes, No, or Submit alone in a confirmation.** The buttons are the
  two outcomes: *"Cancel time off"* / *"Keep time off"*. A user who reads only
  the buttons should still choose correctly.
- **Destructive buttons name the destruction** and use `.btn-danger`. *"Delete
  3 initiatives"* — not *"Confirm"*.
- **Cancel is "Cancel"** when it only closes the surface. Not "Nevermind", not
  "Go back". When "Cancel" is itself the destructive verb (*canceling* time
  off), the safe button says what it keeps: *"Keep time off"*.
- **One `.btn-primary` per surface**, and it takes the most specific verb. Every
  other action is `.btn-secondary`.
- **`.btn-icon-only` needs an `aria-label` that reads like the text version** —
  `aria-label="New initiative"`, not `"plus"`. Same for `.topbar-cta`, which
  mirrors a page-head button: give it that button's label.
- **Referring to a control in text, bold its label exactly as it appears:**
  *"Select **Create initiative** to start."* No quotes, no "the X button",
  never "Click here".

## Links vs buttons

A link goes somewhere; a button does something.

- **A link is a phrase, not a sentence** — no period, sentence case.
- **Put the link on the words that name the destination:** *"Profile updated
  Sep 2025 · [Update profile]"*. Never "Click here". Never "Learn more" on its
  own if you can say *"How OKRs are scored"*.

## Headings

**Name the thing or the action the screen is for** — *"Schedule time off"*,
*"Q3 planning"*. Not a greeting, not a sentence, no period.

## Tooltips

**One or two short sentences that explain** — what a term means or why a value
is what it is. Full sentences, with a period.

> *"A time range when you're flexible to meet with your team."*

Never the only place essential information lives: a tooltip is invisible until
hovered and unreachable on touch. If the user must read it to act, it belongs
in a `.field-hint` or on the page.

## Permissions

A permission (an *ability*, in Toptal's admin tools) is named for **what it
lets someone do** — never "Ability to…", never "Grants…".

> **Name:** *Client claim requests: Transfer*
> **Description:** *Confirm or decline client transfer requests.*

`Area: Verb` for the name; the description starts with the verb.

---

## Telling the user something happened

Four components, four different jobs. Picking the wrong one is the most common
copy mistake in a prototype.

| | Use when | Lifetime |
|---|---|---|
| `.toast` | the system finished something the user asked for | transient |
| `.alert` | a condition is true of this page and stays true | until resolved |
| `.modal` | the user must decide before anything else continues | until dismissed |
| `.field.is-error` | one field is wrong | until that field is fixed |

### Toasts

**Success: `[Noun] successfully [past-tense verb].`** As compact as possible,
with a period.

> *Initiative successfully created.* · *Changes successfully saved.* ·
> *3 rows successfully imported.*

- `.toast-success` **timed** for anything routine. Do not make someone dismiss
  confirmation that a thing worked.
- Anything **reversible gets `.toast-action` with Undo**, and then it must be
  persistent or long-timed — an Undo that vanishes in 5 seconds is decoration.
- **Error toasts follow the error rule below** — say the expectation was not
  met, then what to do. `.toast-error` is **persistent**: a failure the user
  misses is a failure that happens twice.
- Never put a toast and an inline error on the same event. Pick the one that is
  closer to where the user is looking.

### Alerts

A standing condition, worded as the condition — not as an event.

> *"This cycle has no assessors. Add at least one before launching."*

`.alert-danger` blocks, `.alert-warning` degrades, `.alert-info` informs.
If it will be true again tomorrow, it is an alert, not a toast.

### Modals

**The title is the action as a question: `[Verb] [noun]?`**

> *Delete initiative?* — not *"Are you sure you want to delete this
> initiative?"*

The body says only what the user needs to decide — the consequence, not a
restatement of the title. The buttons are the two outcomes (see Buttons).

### Errors

**Two parts: what happened, then what to do.** In that order, in one or two
short sentences. Every error offers a way out of what looks like a dead end.

> *"That file isn't a .csv. Export the sheet as CSV and upload it again."*
> *"We couldn't reach Tableau. Check the connection, then retry."*
> *"Your profile photo must be at least 400 × 400 pixels."*

- Say what the system did, not what the user did wrong.
- Not overly apologetic, never inauthentic, never funny.
- No error codes unless the user can copy one to support — then put it last and
  make it selectable.
- No stack traces, no "An error occurred", no "Something went wrong" on its own
  — that is the absence of a message.
- A field error (`.field-hint` with `.is-error`) names the fix: *"End date must
  be after the start date."* It replaces the hint; it does not stack with it.
- **Brand voice here is the confidence, nothing more.** The user stays in
  control: say plainly what happened and hand them the next move. A failure is
  not the place for personality.

### Empty states

An empty state is a chance to teach what the screen is for. Three things, in
order: **what isn't here, what could be, the one thing to do.**

> **No initiatives yet**
> Initiatives you own or follow appear here.
> *[Create initiative]*

> **No results**
> Try changing or clearing your filters.
> *[Clear filters]*

Never "No data". Never an empty state without an action, unless there is
genuinely nothing the user can do — and then say why.

**A first-use empty state teaches the method in one line.** This is where the
site's habit of explaining the framework belongs: say what the thing is for,
in outcome terms, then offer the one action.

> **No RACI yet**
> Assign who's accountable, so everyone knows who makes the call.
> *[Add RACI]*

> **No key results linked**
> Link this process to a key result to see the impact of the work.
> *[Link key result]*

A filtered-to-nothing empty state does not teach. It says what to change
(*"No results"* above).

### New features

An in-product announcement (a banner, a "What's new" panel, a callout on the
changed screen) is the one surface where the Energetic end of BASE shows. It is
still product copy: it tells someone who already uses the product what they can
do now.

1. **Title: verb + object, naming the capability.** *Schedule meetings from a
   process.* Not *"Introducing Meeting Scheduling"*, not *"Big news"*.
2. **One sentence of outcome**: what it does for them, concretely. *Connect
   Google Calendar and Zoom, and every invite goes to the process's RACI.*
3. **Where it is**, if it isn't right there: *Find it under Settings ›
   Integrations.*
4. **One action that names the next step**: *[Connect calendar]*. Not *"Learn
   more"* or *"Check it out"*.

> **Schedule meetings from a process**
> Connect Google Calendar and Zoom, and every invite goes to the process's
> RACI.
> *[Connect calendar]* · *Dismiss*

- **"New" goes on the `.badge`, not in the sentence.** The title says what,
  the badge says new.
- **No superlatives and no exclamation marks.** *"A faster way to…"* only if
  it is measurably faster, and then say by how much.
- **Dismissible, and gone once seen or used.** A feature is new once.

### Changelogs

The changelog is read by people checking what changed under them. It is a
record, so it is **Serious**: plain and complete, with no selling.

- **One entry per release, headed by its date**: *Nov 4, 2026*. Optionally a
  short title for a large release: *Nov 4, 2026 — Meeting scheduling*.
- **Group under these headings, in this order:** *Changed* · *New* ·
  *Improved* · *Fixed*. Leave out a group with nothing in it.
- **Each line starts with the area, then what the user can now do**, in present
  tense: *Processes: Link a process to more than one key result.*
- **A fix says what works now, not what was broken:** *Exports: Archived
  processes are included in CSV exports.* Not *"Fixed a bug where…"*.
- **Name screens and controls as they appear**, in bold if it is a control:
  *Select **Export** on any table.*
- **No ticket IDs, branch names, code names or people's names.** Same rule
  as principle 4: what the team calls it internally is not what the reader
  sees.
- **Anything that behaves differently goes under *Changed***, first, and says
  what the reader has to do: *Changed: Meetings now inherit invitees from the RACI.
  Remove manual invitees you no longer need.*

---

## Dates, times and numbers

### Dates

| Format | Example | Use |
|---|---|---|
| Standard | *November 23, 2026* | a prominent, uncrowded place |
| **Medium** | ***Nov 23, 2026*** | **the default** — tables, cards, metadata |
| Short | *2026-11-23* | date pickers only |

- No leading zero, comma before the year.
- **Relative time under a week, absolute after.** *today · yesterday · 3 days
  ago* then the date. The feature directory's `relTime()` is the reference
  implementation.

### Times

| Format | Example |
|---|---|
| Standard | *5:07 PM (UTC-05:00) America – New York City* |
| Medium | *5:07 PM (UTC-05:00)* |
| **Short** | ***5:07 PM*** |

- 12-hour clock with **AM / PM** in capitals, a space before it.
- **Carry the offset when anything is cross-time zone** — Medium or Standard.
  The offset is always two digits: *UTC-05:00*, not *UTC-5:00*.
- **Date and time join with "at":** *Nov 23, 2026 at 5:07 PM*.

### Numbers

- **Numerals, not words:** *4 owners*, not *four owners* — including under ten.
- **Thousands separators always, decimal point a period:** *1,284* ·
  *$1,300.75* · *3,000+*. operationalize.com prints both *3000+* and *3,000+*
  on the same page — the separator is the one to keep. Abbreviate to *1.2k* only in chrome too tight for the real
  number.
- **Hours are decimals:** *7.5 hrs*, not *7 hrs 30 min*.
- **Counts read as a phrase, not a parenthetical**: *"12 initiatives"*, not
  *"Initiatives (12)"*. The exception is `.count-badge`, which is numerals only.
- **Zero is "None", not "0"**, when it is a state rather than a measurement.

- **Rates spell out "per":** *$49.99 per user, per month* · *$129 per hour*.
  Not */mo* or */hr* outside chrome too tight for the words.
- **A figure is written the same way every time it appears.** The site says
  *8+ years*, *over 8 years* and *over eight years* about the same fact; a
  screen that repeats a number repeats it exactly.

### Abbreviations

| Write | For |
|---|---|
| *hrs* | hours, in tight space — spell it out in a sentence |
| *hrs/wk* | hours per week |
| *U.S.* | United States |

---

## Fields

- **Label**: a noun phrase in sentence case, no period. *"End date"*, not
  *"Enter the end date"*.
- **Placeholder**: an example of a valid value — *"e.g. Reduce onboarding time"*.
  **Never the label.** A placeholder disappears when typing starts, so anything
  the user must remember cannot live there.
- **`.field-hint`**: permanent guidance, one line. Not a warning, not an error.
- **Optional is marked, required is not.** Most fields are required; marking
  those is noise. Put *(optional)* in the label.

---

## Spelling and words

### Spellings people get wrong

*time zone* (two words) · *canceled* (one l) · *timesheet* · *startup* ·
*onboarding* · the plural of *talent* is *talent*.

**Account actions are *Log in*, *Log out* and *Sign up*** — what
operationalize.com's own buttons say. Verb two words, noun one: *log in* /
*your login*, *sign up* / *the sign-up form*. Not *Sign in*, *Register* or
*Create account*.

### Hyphens

- *part-time*, *full-time*, *on-site* — always hyphenated.
- **Compound adjectives take a hyphen, the noun does not:** *a front-end
  engineer* / *works on the front end*; *on-demand talent* / *talent, on
  demand*. Same for *back end*, *follow up*, *real time* — *a real-time
  dashboard* / *updates in real time*.
- **A number joined to a unit before a noun is hyphenated:** *a 90-day trial*,
  *a 2-week cadence*. After the noun it is not: *the trial lasts 90 days*.

### Toptal-wide terms

These come from Toptal's talent business and hold across every product.

| Write | Not |
|---|---|
| matcher | recruiter |
| talent specialist | sourcer |
| talent network | marketplace, open marketplace |
| onboarding | talent activation |
| no-risk trial | risk-free trial |
| decline | reject, deny |
| thank you | thanks |

Never describe people as *ninja, wizard, rockstar, superstar, guru, unicorn* or
similar. Never call the Toptal network as a whole *"experts"*.

---

## Never write these

`Click here` · `Please` · `Oops` / `Whoops` / `Uh oh` · `Something went wrong`
(alone) · `An error occurred` · `Are you sure?` as a modal title · `Submit`
where you mean Save · `OK` as a confirm label · `users` in UI text · `Ability
to…` · Title Case · exclamation marks outside a welcome · British spellings · marketing
superlatives (*ultimate*, *world-class*, *seamless*) · *Sign in* ·
`Lorem ipsum` or `Step 1 title` in anything you share

## Checking it

A reviewer reads the screen with no context and answers three questions: what is
this, what can I do, what just happened. If any answer requires the surrounding
UI to explain it, the copy is not finished.

---

## Where this departs from the old guide

Toptal's earlier UX Content Style Guide is the source for most of this file. Four
rules were changed on purpose; the old document is wrong for Operationalize on
these and nowhere else.

| Old guide | This file | Why |
|---|---|---|
| Title Case for headers, labels and buttons | **Sentence case everywhere** | One rule instead of two, and no judgment call per string about what counts as a "label". |
| Exclamation marks in welcome phrases and emails | Welcome phrases only | Operationalize sends no marketing email; the welcome exception is kept. |
| Its error example: *"Sorry, something went wrong. Please try again later."* | No "Sorry", no "Please", no bare "Something went wrong" | The example breaks the guide's own rule: *"provide a reason or a fix."* |
| Its permission example: *"Confirm or reject…"* | *"Confirm or decline…"* | The example breaks the guide's own "decline, not reject". |

Kept from the old guide unchanged, and worth knowing were deliberate: the
`[Noun] successfully [verb].` toast formula, the BASE voice, the seven
principles, American English, every date and time format, and the Toptal-wide
terms.
