# UX copy

How words are written in Operationalize. The components are in `AGENTS.md` and
`dist/kit.json`; this file is the text that goes in them.

**What to call things** is not here. Product vocabulary — Processes, Initiative,
Focus Area, RoB meeting, Key Result — lives in `features/CONTEXT.md`, because it
changes with the product and designmd is meant to outlive it. This file is about
*how* to write, and should hold for any product built on the kit.

## The one rule

**Write the words the user would say.** Then cut everything that is not load
bearing. A label is not a sentence, a sentence is not a paragraph, and almost
nothing on a screen needs a paragraph.

---

## Tone

Professional and plain. The register is a competent colleague telling you what
happened — not a brand, not an assistant, not a friend.

- **Address the user as "you".** Use "we" only for things the company actually
  did: *"We could not reach Tableau."* Never "we" for the user's own action.
- **No exclamation marks.** Not in success messages, not anywhere.
- **No "Oops", "Whoops", "Uh oh", "Sorry about that".** A failure is
  information, not an apology.
- **No "Please".** *"Enter an end date"* — not *"Please enter an end date"*. It
  reads as pleading, and it is one more word on every field in the product.
- **Do not congratulate.** The user filed a form; they do not need "Great job!"
- **Never blame.** *"That file is not a .csv"*, not *"You uploaded the wrong
  file type."*
- **Contractions are fine** — "can't", "won't", "doesn't". They read the way
  people speak and they are shorter.

## Capitalisation

**Sentence case everywhere.** Buttons, headings, menu items, field labels,
column headers, tabs, badges, tags, toasts, modal titles, empty states.

> New initiative · End date · In review · Delete process

Capitals only for proper nouns and product terms that are proper nouns
(Tableau, TopTeam, Initiative when it names the entity). Never Title Case,
never ALL CAPS in copy — if something needs to shout, that is a styling
decision, not a spelling one.

---

## Buttons

**The label names the outcome, as a verb, in the user's words.** Read it with
the heading above it: *"Delete initiative" → "Delete initiative"* should make
sense as an answer to the question the screen is asking.

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
  two outcomes: *"Delete initiative"* / *"Cancel"*. A user who reads only the
  buttons should still choose correctly.
- **Destructive buttons name the destruction** and use `.btn-danger`. *"Delete
  3 initiatives"* — not *"Confirm"*.
- **Cancel is "Cancel".** Not "Nevermind", not "Go back".
- **One `.btn-primary` per surface**, and it takes the most specific verb. Every
  other action is `.btn-secondary`.
- **`.btn-icon-only` needs an `aria-label` that reads like the text version** —
  `aria-label="New initiative"`, not `"plus"`. Same for `.topbar-cta`, which
  mirrors a page-head button: give it that button's label.

## Links vs buttons

A link goes somewhere; a button does something. **Never "Click here"** — put the
link on the words that name the destination. Never "Learn more" on its own if
you can say *"How Key Results are scored"*.

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

Past tense, no question, no period needed on a fragment. The user already knows
what they did — the toast confirms it landed.

> **Saved** · **Initiative created** · **3 rows imported**

- `.toast-success` **timed** for anything routine. Do not make someone dismiss
  confirmation that a thing worked.
- Anything **reversible gets `.toast-action` with Undo**, and then it must be
  persistent or long-timed — an Undo that vanishes in 5 seconds is decoration.
- `.toast-error` is **persistent**. A failure the user misses is a failure that
  happens twice.
- Never put a toast and an inline error on the same event. Pick the one that is
  closer to where the user is looking.

### Alerts

A standing condition, worded as the condition — not as an event.

> *"This cycle has no assessors. Add at least one before launching."*

`.alert-danger` blocks, `.alert-warning` degrades, `.alert-info` informs.
If it will be true again tomorrow, it is an alert, not a toast.

### Errors

**Two parts: what happened, then what to do.** In that order, in one or two
short sentences.

> *"That file is not a .csv. Export the sheet as CSV and upload it again."*
> *"We could not reach Tableau. Check the connection, then retry."*

- Say what the system did, not what the user did wrong.
- No error codes unless the user can copy one to support — then put it last and
  make it selectable.
- No stack traces, no "An error occurred", no "Something went wrong" on its own
  — that is the absence of a message.
- A field error (`.field-hint` with `.is-error`) names the fix: *"End date must
  be after the start date."* It replaces the hint; it does not stack with it.

### Empty states

Three things, in order: **what this is, why it is empty, the one thing to do.**

> **No initiatives yet**
> Initiatives you own or follow appear here.
> *[Create initiative]*

Never "No data". Never an empty state without an action, unless there is
genuinely nothing the user can do — and then say why.

---

## Dates, times and numbers

- **Dates: `Oct 3, 2026`.** Abbreviated month, no leading zero, comma before the
  year. This is already the house format across the prototypes. Spell the month
  out in full — *October 3, 2026* — only in a prominent, uncrowded place.
- **Relative time under a week, absolute after.** *today · yesterday · 3 days
  ago* then the date. The feature directory's `relTime()` is the reference
  implementation.
- **Times carry the zone when anything is cross-timezone**: *2:00 PM CET*.
- **Ranges use an en dash with spaces**: *Oct 3 – Nov 14, 2026*.
- **Counts read as a phrase, not a parenthetical**: *"12 initiatives"*, not
  *"Initiatives (12)"*. The exception is `.count-badge`, which is numerals only.
- **Thousands separators always**: *1,284*. Abbreviate to *1.2k* only in chrome
  too tight for the real number.
- **Zero is "None", not "0"**, when it is a state rather than a measurement.

## Fields

- **Label**: a noun phrase in sentence case. *"End date"*, not *"Enter the end
  date"*.
- **Placeholder**: an example of a valid value — *"e.g. Reduce onboarding time"*.
  **Never the label.** A placeholder disappears when typing starts, so anything
  the user must remember cannot live there.
- **`.field-hint`**: permanent guidance, one line. Not a warning, not an error.
- **Optional is marked, required is not.** Most fields are required; marking
  those is noise. Put *(optional)* in the label.

---

## Never write these

`Click here` · `Please` · `Oops` / `Whoops` / `Uh oh` · `Something went wrong`
(alone) · `An error occurred` · `Are you sure?` as the only question ·
`Submit` where you mean Save · `OK` as a confirm label · Title Case ·
exclamation marks · `Lorem ipsum` or `Step 1 title` in anything you share

## Checking it

A reviewer reads the screen with no context and answers three questions: what is
this, what can I do, what just happened. If any answer requires the surrounding
UI to explain it, the copy is not finished.
