bl_info = {
“name”: “Discord Render Notifier”,
“blender”: (3, 0, 0),
“location”: “Properties > Render Tab”,
“category”: “Render”,
“author”: “Dodo”,
“version”: (2, 0),
“description”: “Sends Discord notifications for render start, finish, cancel, and errors”,
}

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.app.handlers import persistent
import time
import threading
import os

# Optional requests import with fallback

try:
import requests
REQUESTS_AVAILABLE = True
except ImportError:
REQUESTS_AVAILABLE = False

# —————————————————————––

# Global State

# —————————————————————––

render_start_time = None
_send_thread = None

# —————————————————————––

# Async Discord Sender (non-blocking)

# —————————————————————––

def _send_in_thread(webhook, payload):
“”“Sends the Discord message in a background thread so Blender doesn’t freeze.”””
try:
response = requests.post(webhook, json=payload, timeout=10)
response.raise_for_status()
print(“✅ Discord notification sent successfully.”)
except requests.exceptions.Timeout:
print(“❌ Discord notification timed out.”)
except requests.exceptions.ConnectionError:
print(“❌ Could not connect to Discord. Check your internet/webhook URL.”)
except Exception as e:
print(f”❌ Failed to send Discord message: {e}”)

def send_discord_message(content=None, embed=None, ping=True):
“””
Sends a message to the Discord webhook asynchronously.
Validates webhook URL format before sending.
“””
if not REQUESTS_AVAILABLE:
print(“⚠️ ‘requests’ module not available. Install it via: pip install requests”)
return

```
scene = bpy.context.scene
webhook = scene.discord_webhook_url.strip()

if not webhook:
    print("⚠️ Discord webhook URL is not set.")
    return

if not webhook.startswith("https://discord.com/api/webhooks/") and \
   not webhook.startswith("https://discordapp.com/api/webhooks/"):
    print("⚠️ Webhook URL looks invalid. Make sure it starts with https://discord.com/api/webhooks/")
    return

mentions = ""
if ping:
    if scene.discord_mention_user.strip():
        mentions += f"<@{scene.discord_mention_user.strip()}> "
    if scene.discord_mention_role.strip():
        mentions += f"<@&{scene.discord_mention_role.strip()}> "

payload = {"content": mentions.strip() if mentions else ""}

if embed:
    # Apply thumbnail if set
    if scene.discord_thumbnail_url.strip():
        embed["thumbnail"] = {"url": scene.discord_thumbnail_url.strip()}
    # Apply footer
    embed["footer"] = {"text": f"Blender {bpy.app.version_string} • Discord Render Notifier v2.0"}
    payload["embeds"] = [embed]

if content:
    payload["content"] = (mentions + content).strip()

# Send in background thread
t = threading.Thread(target=_send_in_thread, args=(webhook, payload), daemon=True)
t.start()
```

# —————————————————————––

# Test Webhook Operator

# —————————————————————––

class DISCORD_OT_test_webhook(bpy.types.Operator):
bl_idname = “discord.test_webhook”
bl_label = “Test Webhook”
bl_description = “Send a test message to verify your webhook is working”

```
def execute(self, context):
    if not REQUESTS_AVAILABLE:
        self.report({'ERROR'}, "'requests' module not installed.")
        return {'CANCELLED'}

    embed = {
        "title": "🔧 Webhook Test",
        "description": "Your Discord Render Notifier is connected and working!",
        "color": 7506394,  # Purple
        "fields": [
            {"name": "Blender Version", "value": bpy.app.version_string, "inline": True},
            {"name": "Scene", "value": context.scene.name, "inline": True},
        ],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    send_discord_message(embed=embed, ping=False)
    self.report({'INFO'}, "Test message sent! Check your Discord channel.")
    return {'FINISHED'}
```

# —————————————————————––

# Copy Webhook Operator

# —————————————————————––

class DISCORD_OT_clear_webhook(bpy.types.Operator):
bl_idname = “discord.clear_webhook”
bl_label = “Clear”
bl_description = “Clear the webhook URL”

```
def execute(self, context):
    context.scene.discord_webhook_url = ""
    self.report({'INFO'}, "Webhook URL cleared.")
    return {'FINISHED'}
```

# —————————————————————––

# Panel

# —————————————————————––

class RENDER_PT_discord_notify(bpy.types.Panel):
bl_label = “Discord Render Notifier”
bl_idname = “RENDER_PT_discord_notify”
bl_space_type = “PROPERTIES”
bl_region_type = “WINDOW”
bl_context = “render”
bl_options = {‘DEFAULT_CLOSED’}

```
def draw_header(self, context):
    layout = self.layout
    layout.label(text="", icon='COMMUNITY')

def draw(self, context):
    layout = self.layout
    scene = context.scene

    # --- Status indicator ---
    if not REQUESTS_AVAILABLE:
        box = layout.box()
        box.alert = True
        box.label(text="⚠ 'requests' not installed!", icon='ERROR')
        box.label(text="Run: pip install requests")
        layout.separator()

    # --- Webhook Settings ---
    box = layout.box()
    box.label(text="Webhook Settings", icon='LINKED')

    row = box.row(align=True)
    row.prop(scene, "discord_webhook_url", text="URL")
    row.operator("discord.clear_webhook", text="", icon='X')

    col = box.column(align=True)
    col.prop(scene, "discord_mention_user", icon='PERSON')
    col.prop(scene, "discord_mention_role", icon='GROUP')

    box.prop(scene, "discord_thumbnail_url", icon='IMAGE_DATA')

    # Test button
    row = box.row()
    row.scale_y = 1.3
    row.operator("discord.test_webhook", icon='CHECKMARK')

    layout.separator()

    # --- Notification Toggles ---
    box = layout.box()
    box.label(text="Notify On...", icon='PREFERENCES')

    col = box.column(align=False)
    col.prop(scene, "discord_notify_on_start",   icon='PLAY')
    col.prop(scene, "discord_notify_on_complete", icon='CHECKMARK')
    col.prop(scene, "discord_notify_on_cancel",   icon='CANCEL')

    layout.separator()

    # --- Render Info ---
    box = layout.box()
    box.label(text="Render Info", icon='RENDER_STILL')
    col = box.column(align=True)
    col.label(text=f"Engine: {scene.render.engine}")
    col.label(text=f"Resolution: {scene.render.resolution_x} × {scene.render.resolution_y}  ({scene.render.resolution_percentage}%)")
    col.label(text=f"Frames: {scene.frame_start} → {scene.frame_end}  ({scene.frame_end - scene.frame_start + 1} total)")
    if scene.render.filepath:
        col.label(text=f"Output: {scene.render.filepath[:40]}{'...' if len(scene.render.filepath) > 40 else ''}")
```

# —————————————————————––

# Render Handlers

# —————————————————————––

@persistent
def render_pre_handler(scene):
global render_start_time
render_start_time = time.time()

```
if not scene.discord_notify_on_start:
    return

total_frames = scene.frame_end - scene.frame_start + 1
res_x = int(scene.render.resolution_x * scene.render.resolution_percentage / 100)
res_y = int(scene.render.resolution_y * scene.render.resolution_percentage / 100)

embed = {
    "title": "🟡 Render Started",
    "color": 3447003,  # Blue
    "fields": [
        {"name": "📁 Scene",        "value": scene.name,                          "inline": True},
        {"name": "🎬 Engine",       "value": scene.render.engine,                 "inline": True},
        {"name": "🖼 Resolution",   "value": f"{res_x} × {res_y}",               "inline": True},
        {"name": "🎞 Frames",       "value": f"{scene.frame_start}–{scene.frame_end} ({total_frames} total)", "inline": True},
        {"name": "📂 Output Path", "value": f"`{scene.render.filepath or 'Not set'}`", "inline": False},
    ],
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}
send_discord_message(embed=embed, ping=False)
```

@persistent
def render_complete_handler(scene):
global render_start_time

```
elapsed_str = "Unknown"
if render_start_time:
    elapsed = time.time() - render_start_time
    elapsed_str = _format_duration(elapsed)
    render_start_time = None

if not scene.discord_notify_on_complete:
    return

total_frames = scene.frame_end - scene.frame_start + 1
output_file = scene.render.frame_path(frame=scene.frame_current)
file_size = _get_file_size(output_file)

embed = {
    "title": "✅ Render Complete!",
    "description": "Your render finished successfully.",
    "color": 3066993,  # Green
    "fields": [
        {"name": "📁 Scene",        "value": scene.name,       "inline": True},
        {"name": "⏱ Render Time",  "value": elapsed_str,      "inline": True},
        {"name": "🎞 Total Frames", "value": str(total_frames), "inline": True},
        {"name": "📂 Output",       "value": f"`{scene.render.filepath or 'Not set'}`", "inline": False},
    ],
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}

if file_size:
    embed["fields"].append({"name": "💾 File Size", "value": file_size, "inline": True})

send_discord_message(embed=embed, ping=True)
```

@persistent
def render_cancel_handler(scene):
global render_start_time

```
elapsed_str = "Unknown"
if render_start_time:
    elapsed = time.time() - render_start_time
    elapsed_str = _format_duration(elapsed)
    render_start_time = None

if not scene.discord_notify_on_cancel:
    return

embed = {
    "title": "🚫 Render Cancelled",
    "description": "The render was stopped before completing.",
    "color": 15158332,  # Red
    "fields": [
        {"name": "📁 Scene",       "value": scene.name, "inline": True},
        {"name": "⏱ Time Spent",  "value": elapsed_str, "inline": True},
        {"name": "🎞 Last Frame",  "value": str(scene.frame_current), "inline": True},
    ],
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}
send_discord_message(embed=embed, ping=True)
```

# —————————————————————––

# Helpers

# —————————————————————––

def _format_duration(seconds):
“”“Formats seconds into a human-readable duration string.”””
seconds = int(seconds)
h = seconds // 3600
m = (seconds % 3600) // 60
s = seconds % 60
if h > 0:
return f”{h}h {m}m {s}s”
elif m > 0:
return f”{m}m {s}s”
else:
return f”{s}s”

def _get_file_size(filepath):
“”“Returns a human-readable file size string, or None if file doesn’t exist.”””
try:
if filepath and os.path.isfile(filepath):
size = os.path.getsize(filepath)
if size >= 1_048_576:
return f”{size / 1_048_576:.1f} MB”
elif size >= 1024:
return f”{size / 1024:.1f} KB”
else:
return f”{size} B”
except Exception:
pass
return None

# —————————————————————––

# Register / Unregister

# —————————————————————––

classes = (
RENDER_PT_discord_notify,
DISCORD_OT_test_webhook,
DISCORD_OT_clear_webhook,
)

def register():
for cls in classes:
bpy.utils.register_class(cls)

```
bpy.types.Scene.discord_webhook_url = StringProperty(
    name="Webhook URL",
    description="Your Discord webhook URL (from Server Settings > Integrations)",
    default="",
    subtype='NONE'
)
bpy.types.Scene.discord_mention_user = StringProperty(
    name="Mention User ID",
    description="Discord User ID to ping on completion/cancel (optional)",
    default=""
)
bpy.types.Scene.discord_mention_role = StringProperty(
    name="Mention Role ID",
    description="Discord Role ID to ping on completion/cancel (optional)",
    default=""
)
bpy.types.Scene.discord_thumbnail_url = StringProperty(
    name="Thumbnail URL",
    description="URL of an image to show as thumbnail in embeds (optional)",
    default=""
)
bpy.types.Scene.discord_notify_on_start = BoolProperty(
    name="Render Started",
    description="Send a notification when rendering begins",
    default=True
)
bpy.types.Scene.discord_notify_on_complete = BoolProperty(
    name="Render Complete",
    description="Send a notification when rendering finishes successfully",
    default=True
)
bpy.types.Scene.discord_notify_on_cancel = BoolProperty(
    name="Render Cancelled",
    description="Send a notification when rendering is cancelled",
    default=True
)

bpy.app.handlers.render_pre.append(render_pre_handler)
bpy.app.handlers.render_complete.append(render_complete_handler)
bpy.app.handlers.render_cancel.append(render_cancel_handler)

print("✅ Discord Render Notifier v2.0 registered.")
```

def unregister():
handlers = [
(bpy.app.handlers.render_pre,      render_pre_handler),
(bpy.app.handlers.render_complete,  render_complete_handler),
(bpy.app.handlers.render_cancel,    render_cancel_handler),
]
for handler_list, fn in handlers:
if fn in handler_list:
handler_list.remove(fn)

```
props = [
    "discord_webhook_url",
    "discord_mention_user",
    "discord_mention_role",
    "discord_thumbnail_url",
    "discord_notify_on_start",
    "discord_notify_on_complete",
    "discord_notify_on_cancel",
]
for prop in props:
    if hasattr(bpy.types.Scene, prop):
        delattr(bpy.types.Scene, prop)

for cls in reversed(classes):
    bpy.utils.unregister_class(cls)

print("✅ Discord Render Notifier unregistered.")
```

if **name** == “**main**”:
register()