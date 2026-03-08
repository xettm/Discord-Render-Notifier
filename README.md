# Discord Render Notifier for Blender

> 🎨 Rich Discord notifications for Blender renders — with progress tracking, webhook presets, embed themes, and more.

-----

## Features

- ✅ Embed notifications for render **start**, **complete**, and **cancel**
- ⏳ **Frame progress updates** with ETA, elapsed time, and avg time/frame
- 🔗 **Multiple webhook presets** — switch between servers in one click
- 🎨 **Embed color themes** — Default, Neon, Pastel, Mono, or Custom hex
- 📝 **Render note field** — tag each render session with a custom note
- ⏱ **Cooldown timer** — prevent notification spam on quick test renders
- 🏷 Optional **user & role pings** on completion and cancel
- 🖼 Optional **thumbnail URL** per embed
- 🧵 Non-blocking — notifications send in a background thread
- ✔ Works with Blender 3.x and 4.x

-----

## Requirements

- Blender 3.0 or later
- Python `requests` module

If `requests` isn’t installed, the panel will show a warning. Install it by running:

```bash
pip install requests
```

> On some systems you may need to target Blender’s bundled Python:
> `path/to/blender/python/bin/python -m pip install requests`

-----

## Installation

1. Download `discord_render_notifier.py` from this repository
1. Open Blender → **Edit → Preferences → Add-ons → Install…**
1. Select `discord_render_notifier.py`
1. Enable the add-on checkbox

-----

## Setup

### 1. Add a Webhook Preset

1. Go to **Properties → Render tab** (📷 camera icon)
1. Scroll down to **Discord Render Notifier**
1. Open **Webhook Presets** and click **+** to add a new preset
1. Give it a name (e.g. `My Server`) and paste your webhook URL
1. Click **Test Webhook** to verify it’s working

You can add multiple presets and switch between them freely — useful for sending to different servers or channels.

### 2. Configure Mentions (Optional)

Under **Mentions & Identity**:

|Field          |What to put                                     |
|---------------|------------------------------------------------|
|Mention User ID|Your Discord User ID (e.g. `123456789012345678`)|
|Mention Role ID|A Discord Role ID to ping                       |
|Thumbnail URL  |Any image URL to show in embeds                 |
|Render Note    |A short note tagged to every embed this session |

User and role pings are sent on **complete** and **cancel** only — not on start or progress updates.

### 3. Configure Notifications

Under **Notifications**:

- Toggle which events fire a notification (Start / Complete / Cancel)
- Enable **Frame Progress Updates** and set the interval (e.g. every 10 frames)
- Set a **Cooldown** in seconds to prevent spam during quick test renders

> Completion and cancel notifications always bypass the cooldown.

### 4. Customize Embeds

Under **Embed Customization**:

- Choose a **Color Theme**: Default, Neon, Pastel, Mono, or Custom
- In Custom mode, set individual hex colors for Start / Complete / Cancel
- Set a **Custom Footer** (leave blank to use the default Blender version string)

-----

## How to Get a Discord Webhook URL

1. Open your **Discord server settings**
1. Go to **Integrations → Webhooks**
1. Click **New Webhook**
1. Give it a name (e.g. `Blender Render Bot`) and choose a channel
1. Click **Copy Webhook URL**
1. Paste it into a preset inside the add-on

-----

## What Each Notification Looks Like

### 🟡 Render Started

Shows scene name, render engine, resolution, frame range, and output path.

### ⏳ Frame Progress *(if enabled)*

Fires every N frames with a visual progress bar, percentage, ETA, elapsed time, and average time per frame.

```
█████░░░░░  50.0%
Frame: 50 / 100  |  Elapsed: 2m 10s  |  ETA: 2m 8s  |  Avg/Frame: 2.6s
```

### ✅ Render Complete

Shows render time, total frames, output path, average time per frame, and output file size.

### 🚫 Render Cancelled

Shows time spent and how many frames were completed before stopping.

-----

## Notes

- Make sure Blender has internet access
- Webhook URLs should start with `https://discord.com/api/webhooks/` the add-on validates this before sending
- For long animation renders, frame progress updates are sent outside of cooldown so you always get them
- Deleting or changing presets mid-render is safe - the active preset is read at notification time

-----

## Changelog

### v3.0

- Added webhook preset system with UIList
- Added frame progress updates with ETA and progress bar
- Added embed color themes (Default / Neon / Pastel / Mono / Custom)
- Added render note field
- Added cooldown timer
- Added custom footer text
- Completion and cancel bypass cooldown

### v2.0

- Async non-blocking message sending
- Webhook URL validation
- `@persistent` handlers survive file reloads
- Per-frame file size reporting
- Better error messages

### v1.5

- Initial public release
- Start / complete / cancel notifications
- User and role pings