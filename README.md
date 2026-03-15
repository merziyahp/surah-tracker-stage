# 🚀 Surah Mission Control

A lightweight, iPad-friendly Quran memorization tracker for kids. Built as a single HTML file — no app store, no account, no internet required after setup. Each family's data lives privately on their own device.

---

## What It Does

Surah Mission Control helps children track their Quran memorization progress through a space-themed card dashboard. Each Surah (chapter) gets its own mission card showing its current status, revision history, and a rocket that reflects how the memorization is going.

The app has two modes: **Explorer Mode** (for the child) and **Parent Mode** (PIN protected). This keeps the experience child-friendly while giving parents full control over what gets confirmed.

If you're using the app and have feedback, bugs to report, or feature ideas, we'd love to hear from you — **[share your feedback here](https://docs.google.com/forms/d/e/1FAIpQLSe4FYnzAj8nc-klaGET2_VohJ43K9liFUlEuhxk1nF8rbS8bg/viewform)**. ⭐

---

## The Cards

Every Surah card shows:

- **Surah number, English name, Arabic name (e.g. الفاتحة), and English meaning**
- **A rocket** whose animation reflects the card's status — floating means launched, still means grounded or in repair
- **Fuel gauge** — shows how well-maintained the Surah is (see below)
- **Launched** — a checkmark box confirming the Surah is memorized (parent only)
- **Re-fuel dots** — 6 circles tracking revision sessions, with the date of the last session shown automatically
- **Repair** — a 🔧 wrench flag to signal the Surah needs work

### Card Status

| Border | Meaning |
|--------|---------|
| Green | Launched — fully memorized |
| Red | Repair — needs attention |
| Default | In progress |

---

## The Fuel Gauge

The fuel gauge is the heart of the revision system. It works differently depending on whether a Surah is in progress or launched.

### In Progress (3 segments, manual)
While a child is learning a Surah, the fuel gauge has 3 segments that the child taps manually to show their confidence level. The parent confirms when it's ready to launch.

### Launched (5 segments, automatic)
Once a Surah is launched, the fuel gauge becomes automatic. It starts full and **slowly drains as other Surahs get re-fuelled** — not by calendar time, but by activity. If you keep revising the same few Surahs and neglect others, those neglected rockets quietly run low on fuel, making it easy to spot which ones need attention.

**Drain rate:**
- With fewer than 12 launched Surahs — lose 1 segment every 2 re-fuel sessions elsewhere
- With 12 or more launched Surahs — lose 1 segment every 5 re-fuel sessions elsewhere

The rate adjusts automatically as your tracker grows, so the system stays fair whether you have 5 Surahs or 50.

**Refuelling:**
A parent logs a revision session by tapping a Re-fuel dot on a card. This immediately tops the fuel back to full and resets that Surah's drain clock. If the session revealed a problem, the parent or child flags it for Repair — the fuel stays full either way, since the Surah was tested.

**Frozen in Repair:**
A Surah in repair does not drain. It's already flagged for attention, so there's no need to penalise it further. Fuel resumes draining normally once repair is cleared.

---

## The Revision Flow

```
In Progress → Launched → (optional) Re-fuel → (optional) Repair → back to Launched
```

1. Child learns a Surah, fills the manual fuel gauge as confidence grows
2. Parent tests the child and taps **Launched** to confirm memorization — fuel expands to 5 segments, rocket starts floating
3. Over time, fuel drains as other Surahs get revised
4. Parent sits down with the child for a revision session, taps a **Re-fuel dot** — fuel tops back up, date is recorded
5. If the revision reveals the child has forgotten parts, parent or child taps **Repair** — rocket goes stationary, launched box shows ⚠️ with a red card border
6. Child works on it until the parent is satisfied — parent clears Repair, rocket goes back to Launched and fuel fills to full

---

## What the Child Can Do

- View all Surah cards and their current status
- Fill or unfill the **fuel gauge** on in-progress cards to show confidence
- Tap **Repair** to flag a launched Surah that needs fixing
- Pick a **rocket color** for each card using the color picker
- **Search** cards by name or number
- **Filter** cards by status: All, Launched, Repair, In Progress

---

## What the Parent Can Do

Everything the child can do, plus:

- **Mark a Surah as Launched** — confirms memorization, expands fuel to 5 segments
- **Log Re-fuel sessions** — tap revision dots to record a session and top up fuel
- **Clear Repair** — marks a Surah as fixed and restores it to launched
- **Add new Surahs** — from the full built-in list of all 114 Surahs
- **Remove Surahs** — tap an already-added Surah in the picker to remove it
- **Exit parent mode** — hands the device back to the child

### Parent Access

Parent mode is protected by a PIN code. To get the PIN, contact the developer.

---

## Adding Surahs

In Parent Mode, a **+ Add Surah** card appears at the end of the dashboard. Tapping it opens a searchable list of all 114 Surahs showing the number, Arabic name, English name, and English meaning. Surahs already on the dashboard are highlighted and can be tapped again to remove them.

---

## Getting It on an iPad

### GitHub Pages (recommended)
1. The app is hosted at a public URL
2. Open the URL in Safari on the iPad
3. Tap the Share button → **Add to Home Screen**
4. It appears on the home screen and opens full-screen like a native app

Each family who uses the same URL gets their own completely private tracker — data never leaves their device.

---

## Data & Privacy

All data is stored locally on the device. Nothing is sent to any server. Each device maintains its own independent tracker — there is no shared database or account system. Families using the same hosted URL each have completely separate, private data.

---

## Tech Stack

- Plain HTML, CSS, and JavaScript — no frameworks, no dependencies, no build step
- All 114 Surah names (Arabic, English, meaning) embedded directly in the file
- Works fully offline once loaded
- Optimized for iPad Safari but works in any modern browser

---

## Future Ideas

- In-app PIN change for families sharing the hosted version
- Juz (part) grouping and progress overview
- Export / backup data
- Multiple visual themes (plants, stars, planets)
- Audio playback integration

---

*Built with ❤️ for a little boy memorizing the Quran.*
