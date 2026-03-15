# 🚀 Surah Mission Control

A lightweight, iPad-friendly Quran memorization tracker for kids. Built as a single HTML file — no app store, no account, no internet required after setup. Each family's data lives privately on their own device.

---

## What It Does

Surah Mission Control helps children track their Quran memorization progress through a space-themed card dashboard. Each Surah (chapter) gets its own mission card showing its current status, review history, and a rocket that reflects how the memorization is going.

The app has two modes: **Explorer Mode** (for the child) and **Parent Mode** (password protected). This keeps the experience child-friendly while giving parents control over what gets marked as complete.

---

## The Cards

Every Surah card shows:

- **Surah number, English name, Arabic name (e.g. الفاتحة), and English meaning**
- **A rocket** whose animation reflects the card's status — floating means launched, still means grounded
- **Fuel gauge** — 3 tappable segments the child fills in to show how well they know the Surah (1/3, 2/3, or fully fuelled)
- **Launched** — a checkmark box confirming the Surah is memorized (parent only)
- **Re-test dots** — 6 circles to track revision sessions, with the date of the last retest shown automatically
- **Repair** — a 🔧 wrench flag the child can tap to signal the Surah needs work. A cross-hatch pattern appears on the rocket body when repair is active

### Card Status Colors

| Status | Meaning |
|--------|---------|
| Green border | Launched — fully memorized |
| Red border | Repair — needs attention |
| Default | In progress or under review |

---

## What the Child Can Do

- View all Surah cards and their current status
- Fill or unfill the **fuel gauge** segments to show confidence level
- Tap **Re-test dots** to log a revision session (automatically records today's date)
- Tap **Repair** to flag a Surah that needs fixing
- Pick a **rocket color** for each card using the color picker
- **Search** cards by name or number
- **Filter** cards by status: All, Launched, Repair, Re-test, In Progress

---

## What the Parent Can Do

Everything the child can do, plus:

- **Mark a Surah as Launched** (memorized and confirmed)
- **Add new Surahs** to the tracker from the full built-in list of all 114 Surahs
- **Remove Surahs** from the tracker
- **Exit parent mode** to hand the device back to the child

### Parent Access

Parent mode is protected by a PIN code. To get the PIN, contact the developer.

---

## Adding Surahs

In Parent Mode, a **+ Add Surah** card appears at the end of the dashboard. Tapping it opens a searchable list of all 114 Surahs showing:

- Surah number
- Arabic name
- English transliteration
- English meaning

Surahs already on the dashboard are highlighted in green and can be tapped again to remove them. Search by number, English name, or meaning.

---

## How the Repair Flow Works

The repair system is designed to encourage regular revision without tying it to specific dates:

1. Child (or parent) taps **Repair** on a card → rocket goes stationary, red warning stripes appear
2. Child revises the Surah and taps a **Re-test dot** → repair flag clears automatically, last retest date updates
3. Parent can spot Surahs that haven't been retested recently by comparing the "Last Retest" dates across cards

---

## Getting It on an iPad

### Option 1 — Safari (simplest)
1. Download the `index.html` file
2. AirDrop or email it to the iPad
3. Open in Safari → tap Share → **Add to Home Screen**

### Option 2 — GitHub Pages (recommended for sharing)
1. Upload `index.html` to a GitHub repository
2. Enable GitHub Pages under Settings → Pages
3. Share the URL — each person who opens it gets their own private tracker on their device

---

## Data & Privacy

All data is stored locally on the device using `localStorage`. Nothing is sent to any server. Each device maintains its own independent tracker — there is no shared database or account system. Families who use the same hosted URL each have completely separate data.

---

## Tech Stack

- Plain HTML, CSS, and JavaScript — no frameworks, no dependencies
- All 114 Surah names (Arabic, English, meaning) are embedded directly in the file
- Works fully offline once loaded
- Optimized for iPad Safari but works in any modern browser

---

## Future Ideas

- In-app PIN change for families sharing the hosted version
- Multiple theme packs (plants, stars, planets) for different visual preferences
- Juz (part) grouping and progress overview
- Export / backup data
- Audio playback integration

---

*Built with ❤️ for a little boy memorizing the Quran.*
