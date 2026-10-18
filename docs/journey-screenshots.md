# Journey Intelligence launch screenshots

The `/journey-intelligence` page currently ships **without product imagery**.
Placeholder frames were removed deliberately: a public launch page should not
carry mock product UI. Add the images below once captured, then drop the
"needs imagery" note from the release checklist.

All screens live in the application (`ntmapp`), not in this repository.

## Ground rules

1. **Use a dedicated demo account.** Never screenshot a real customer, a real
   colleague, or your own live account. Create a fresh account, seed it with
   the fictional data below, and delete it afterwards.
2. **No real personal data.** No real names, companies, email addresses, phone
   numbers, logos, deal values or dates tied to a real engagement.
3. **Check the chrome.** Browser profile avatar, bookmarks bar, notification
   badges, the account email in the app header and any usage figures all leak.
   Capture in a clean browser profile at 1440×900, zoom 100%.
4. **Light mode**, no text selection, no hover tooltips, no open menus.
5. Export PNG, then run the result past a second pair of eyes before it is
   committed. Commit to `assets/img/` and reference with descriptive `alt`.

## Seed data (fictional — use verbatim)

Journey: **"Northwind Logistics — platform rollout"** (type: client engagement)

| # | Meeting title | Date | What it should contain |
|---|---|---|---|
| 1 | Discovery call | 2026-01-14 | Requirements captured; one integration concern raised |
| 2 | Technical review | 2026-02-04 | Integration approach agreed; delivery risk raised |
| 3 | Commercial discussion | 2026-02-25 | Commercial terms discussed; technical concern resolved |
| 4 | Rollout planning | 2026-03-18 | Go-live date confirmed; training action assigned |

Participants: **A. Fletcher**, **R. Osei**, **M. Lindqvist** (all fictional).

## Screens to capture

### 1. Journey timeline and overview — **primary launch image**
- **Where:** `/dashboard/journeys/[id]` (the overview panel)
- **Shows:** all four meetings in chronological order with their confirmed
  outcome markers.
- **Used for:** the "Inside a Journey" section of `/journey-intelligence`.
- **Capture note:** confirm at least two outcomes first (see screen 2) so the
  timeline is not visually empty.

### 2. Confirmed outcome tracking
- **Where:** `/dashboard/journeys/[id]` → outcome controls on a meeting
- **Shows:** an outcome moved to a confirmed state, with its status label.
- **Used for:** the "Confirmed outcomes" card.
- **Capture note:** outcomes are a **Free** capability — capture this on the
  free demo account so the image matches what the copy promises.

### 3. Journeys list with the Free allowance visible
- **Where:** `/dashboard/meetings` → Journeys panel
- **Shows:** two Journeys on a Free account (the Free maximum).
- **Used for:** optional supporting image for the Free/Pro section.

### 4. Effectiveness and coaching panel — **Pro evidence required**
- **Where:** `/dashboard/journeys/[id]` → coaching panel
- **Shows:** effectiveness movement across meetings plus evidence-backed
  coaching claims.
- **Prerequisite:** this panel is assembled from assessment evidence written by
  **Advanced AI Learn, which is Pro-only**. The demo account must be on a paid
  plan and must have run Learn over the Journey, or the panel renders empty.
- **Caption requirement:** any use of this image on the marketing site must say
  the evidence behind it is produced by a Pro capability. Do not present it as
  a Free-plan screen.

### 5. Upgrade prompt at a Free limit
- **Where:** attempt to create a third Journey on the Free demo account
- **Shows:** the in-app prompt at the point the Free cap is reached.
- **Used for:** supports the "Reaching a Free limit" callout.

## After capture

- Save as `assets/img/journey-<screen>.png`, max 1600px wide, compressed.
- Add `<img>` with meaningful `alt` describing what the screen shows.
- Re-run `python3 scripts/validate.py` (it fails on any `<img>` without `alt`).
- Delete the demo account.
