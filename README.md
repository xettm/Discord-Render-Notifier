# Discord Render Notifier for Blender

🎨 Sends a Discord notification when a Blender render is finished and optional user/role pings.

## Features

- Discord embed notification on render complete or cancel
- Ping multiple users or roles
- Works with Blender 3.x / 4.x

## Installation

1. Download or clone this repository:
2. Open Blender → Edit → Preferences → Add-ons → Install…
3. Select discord_render_notifier.py from the repository
4. Enable the add-on checkbox

## Usage

1. Go to the Render Properties Tab (camera icon)
2. Scroll down to Discord Render Notifier
3. Fill in your:
. Webhook URL (from Discord)
. Mention Users (optional, comma-separated Discord User IDs)
. Mention Roles (optional, comma-separated Discord Role IDs)

5. Render your scene:
. Finished renders send a Discord embed + notifier

## Notes
. Make sure Blender has internet access

