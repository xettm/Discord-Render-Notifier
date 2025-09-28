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


## How to Get a Discord Webhook URL

1. Open your Discord server settings.
2. Go to Integrations → Webhooks.
3. Click New Webhook.
4. Give it a name (e.g., Blender Render Bot) and choose a channel where messages will be sent.
5. Click Copy Webhook URL.
6. Paste this URL into the add-on’s settings inside Blender.
That’s it! Every time your render is starting or finish, a message will be sent to that Discord channel.

