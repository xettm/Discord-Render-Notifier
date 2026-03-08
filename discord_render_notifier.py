bl_info = {
“name”: “Discord Render Notifier”,
“blender”: (3, 0, 0),
“location”: “Properties > Render Tab”,
“category”: “Render”,
“author”: “Dodo”,
“version”: (3, 0),
“description”: “Sends rich Discord notifications for render events with presets, progress, and embed customization”,
}

import bpy
from bpy.props import (
StringProperty, BoolProperty, IntProperty,
EnumProperty, CollectionProperty
)
from bpy.types import PropertyGroup
from bpy.app.handlers import persistent
import time
import threading
import os

# —————————————————————––

# Optional requests import

# —————————————————————––

try:
import requests
REQUESTS_AVAILABLE = True
except ImportError:
REQUESTS_AVAILABLE = False

# —————————————————————––

# Global State

# —————————————————————––

render_start_time = None
frame_times = []
last_frame_start = None
last_notification_time = 0.0

# —————————————————————––

# Embed Color Presets

# —————————————————————––

EMBED_COLOR_PRESETS = {
“DEFAULT”: {“start”: 3447003,  “complete”: 3066993,  “cancel”: 15158332},
“NEON”:    {“start”: 16711935, “complete”: 65535,    “cancel”: 16711680},
“PASTEL”:  {“start”: 11393254, “complete”: 9498256,  “cancel”: 16754788},
“MONO”:    {“start”: 8421504,  “complete”: 16777215, “cancel”: 4210752},
“CUSTOM”:  None,
}

def hex_to_int(hex_str):
try:
return int(hex_str.strip().lstrip(”#”), 16)
except ValueError:
return 3447003

def get_embed_colors(scene):
preset = scene.discord_color_preset
if preset == “CUSTOM”:
return {
“start”:    hex_to_int(scene.discord_custom_color_start),
“complete”: hex_to_int(scene.discord_custom_color_complete),
“cancel”:   hex_to_int(scene.discord_custom_color_cancel),
}
return EMBED_COLOR_PRESETS.get(preset, EMBED_COLOR_PRESETS[“DEFAULT”])

# —————————————————————––

# Webhook Preset Collection Item

# —————————————————————––

class DiscordWebhookPreset(PropertyGroup):
name: StringProperty(name=“Preset Name”, default=“My Server”)
url:  StringProperty(name=“Webhook URL”,  default=””)

# —————————————————————––

# Async Discord Sender

# —————————————————————––

def _send_in_thread(webhook, payload):
try:
response = requests.post(webhook, json=payload, timeout=10)
response.raise_for_status()
print(“✅ Discord notification sent.”)
except requests.exceptions.Timeout:
print(“❌ Discord timed out.”)
except requests.exceptions.ConnectionError:
print(“❌ Could not connect to Discord.”)
except Exception as e:
print(f”❌ Discord send failed: {e}”)

def send_discord_message(content=None, embed=None, ping=True, force=False):
global last_notification_time

```
if not REQUESTS_AVAILABLE:
    print("⚠️ 'requests' module not installed.")
    return

scene = bpy.context.scene
presets = scene.discord_webhook_presets
idx = scene.discord_active_preset_index

if not presets or idx >= len(presets):
    print("⚠️ No webhook preset selected.")
    return

webhook = presets[idx].url.strip()
if not webhook:
    print("⚠️ Active preset has no URL.")
    return

if not (webhook.startswith("https://discord.com/api/webhooks/") or
        webhook.startswith("https://discordapp.com/api/webhooks/")):
    print("⚠️ Webhook URL looks invalid.")
    return

# Cooldown check (completion & cancel always bypass)
if not force:
    cooldown = scene.discord_cooldown_seconds
    now = time.time()
    if cooldown > 0 and (now - last_notification_time) < cooldown:
        remaining = cooldown - (now - last_notification_time)
        print(f"⏳ Cooldown active — {remaining:.1f}s left. Skipped.")
        return
    last_notification_time = now

mentions = ""
if ping:
    if scene.discord_mention_user.strip():
        mentions += f"<@{scene.discord_mention_user.strip()}> "
    if scene.discord_mention_role.strip():
        mentions += f"<@&{scene.discord_mention_role.strip()}> "

payload = {"content": mentions.strip()}

if embed:
    if scene.discord_thumbnail_url.strip():
        embed["thumbnail"] = {"url": scene.discord_thumbnail_url.strip()}

    footer_text = scene.discord_custom_footer.strip() or f"Blender {bpy.app.version_string} • Discord Render Notifier v3.0"
    embed["footer"] = {"text": footer_text}

    note = scene.discord_render_note.strip()
    if note:
        embed.setdefault("fields", [])
        embed["fields"].append({"name": "📝 Note", "value": note, "inline": False})

    payload["embeds"] = [embed]

if content:
    payload["content"] = (mentions + content).strip()

t = threading.Thread(target=_send_in_thread, args=(webhook, payload), daemon=True)
t.start()
```

# —————————————————————––

# Operators

# —————————————————————––

class DISCORD_OT_test_webhook(bpy.types.Operator):
bl_idname = “discord.test_webhook”
bl_label = “Test Webhook”
bl_description = “Send a test embed to verify the active webhook”

```
def execute(self, context):
    if not REQUESTS_AVAILABLE:
        self.report({'ERROR'}, "'requests' not installed.")
        return {'CANCELLED'}
    embed = {
        "title": "🔧 Webhook Test",
        "description": "Discord Render Notifier v3.0 is connected!",
        "color": 7506394,
        "fields": [
            {"name": "Blender", "value": bpy.app.version_string,         "inline": True},
            {"name": "Scene",   "value": context.scene.name,             "inline": True},
            {"name": "Theme",   "value": context.scene.discord_color_preset, "inline": True},
        ],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    send_discord_message(embed=embed, ping=False, force=True)
    self.report({'INFO'}, "Test message sent!")
    return {'FINISHED'}
```

class DISCORD_OT_add_preset(bpy.types.Operator):
bl_idname = “discord.add_preset”
bl_label = “Add Preset”

```
def execute(self, context):
    scene = context.scene
    p = scene.discord_webhook_presets.add()
    p.name = f"Preset {len(scene.discord_webhook_presets)}"
    scene.discord_active_preset_index = len(scene.discord_webhook_presets) - 1
    return {'FINISHED'}
```

class DISCORD_OT_remove_preset(bpy.types.Operator):
bl_idname = “discord.remove_preset”
bl_label = “Remove Preset”

```
def execute(self, context):
    scene = context.scene
    idx = scene.discord_active_preset_index
    if scene.discord_webhook_presets and 0 <= idx < len(scene.discord_webhook_presets):
        scene.discord_webhook_presets.remove(idx)
        scene.discord_active_preset_index = max(0, idx - 1)
    return {'FINISHED'}
```

class DISCORD_OT_clear_webhook(bpy.types.Operator):
bl_idname = “discord.clear_webhook”
bl_label = “Clear URL”

```
def execute(self, context):
    scene = context.scene
    idx = scene.discord_active_preset_index
    if scene.discord_webhook_presets and 0 <= idx < len(scene.discord_webhook_presets):
        scene.discord_webhook_presets[idx].url = ""
    return {'FINISHED'}
```

# —————————————————————––

# Preset UIList

# —————————————————————––

class DISCORD_UL_presets(bpy.types.UIList):
def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
row = layout.row(align=True)
row.prop(item, “name”, text=””, emboss=False, icon=‘LINKED’)
hint = (item.url[:32] + “…”) if len(item.url) > 32 else item.url
row.label(text=hint if hint else “No URL set”)

# —————————————————————––

# Panels

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
    self.layout.label(text="", icon='COMMUNITY')

def draw(self, context):
    layout = self.layout
    if not REQUESTS_AVAILABLE:
        box = layout.box()
        box.alert = True
        box.label(text="⚠ 'requests' not installed!", icon='ERROR')
        box.label(text="Run: pip install requests")
```

class RENDER_PT_discord_presets(bpy.types.Panel):
bl_label = “Webhook Presets”
bl_idname = “RENDER_PT_discord_presets”
bl_space_type = “PROPERTIES”
bl_region_type = “WINDOW”
bl_context = “render”
bl_parent_id = “RENDER_PT_discord_notify”

```
def draw(self, context):
    layout = self.layout
    scene = context.scene

    row = layout.row()
    row.template_list(
        "DISCORD_UL_presets", "",
        scene, "discord_webhook_presets",
        scene, "discord_active_preset_index",
        rows=3
    )
    col = row.column(align=True)
    col.operator("discord.add_preset",    text="", icon='ADD')
    col.operator("discord.remove_preset", text="", icon='REMOVE')

    presets = scene.discord_webhook_presets
    idx = scene.discord_active_preset_index
    if presets and 0 <= idx < len(presets):
        box = layout.box()
        active = presets[idx]
        box.prop(active, "name", text="Name")
        row = box.row(align=True)
        row.prop(active, "url", text="URL")
        row.operator("discord.clear_webhook", text="", icon='X')

    row = layout.row()
    row.scale_y = 1.2
    row.operator("discord.test_webhook", icon='CHECKMARK')
```

class RENDER_PT_discord_mentions(bpy.types.Panel):
bl_label = “Mentions & Identity”
bl_idname = “RENDER_PT_discord_mentions”
bl_space_type = “PROPERTIES”
bl_region_type = “WINDOW”
bl_context = “render”
bl_parent_id = “RENDER_PT_discord_notify”
bl_options = {‘DEFAULT_CLOSED’}

```
def draw(self, context):
    layout = self.layout
    scene = context.scene
    col = layout.column(align=True)
    col.prop(scene, "discord_mention_user",  icon='PERSON')
    col.prop(scene, "discord_mention_role",  icon='GROUP')
    layout.prop(scene, "discord_thumbnail_url", icon='IMAGE_DATA')
    layout.prop(scene, "discord_render_note",   icon='TEXT')
```

class RENDER_PT_discord_notifications(bpy.types.Panel):
bl_label = “Notifications”
bl_idname = “RENDER_PT_discord_notifications”
bl_space_type = “PROPERTIES”
bl_region_type = “WINDOW”
bl_context = “render”
bl_parent_id = “RENDER_PT_discord_notify”

```
def draw(self, context):
    layout = self.layout
    scene = context.scene

    box = layout.box()
    box.label(text="Send notification on...", icon='PREFERENCES')
    col = box.column(align=True)
    col.prop(scene, "discord_notify_on_start",    icon='PLAY')
    col.prop(scene, "discord_notify_on_complete",  icon='CHECKMARK')
    col.prop(scene, "discord_notify_on_cancel",    icon='CANCEL')

    layout.separator()

    box = layout.box()
    box.label(text="Frame Progress", icon='RENDER_ANIMATION')
    box.prop(scene, "discord_progress_enabled")
    if scene.discord_progress_enabled:
        box.prop(scene, "discord_progress_interval")

    layout.separator()

    box = layout.box()
    box.label(text="Cooldown", icon='TIME')
    box.prop(scene, "discord_cooldown_seconds")
    if scene.discord_cooldown_seconds > 0:
        box.label(text="Completion & cancel always bypass cooldown.", icon='INFO')
```

class RENDER_PT_discord_embed(bpy.types.Panel):
bl_label = “Embed Customization”
bl_idname = “RENDER_PT_discord_embed”
bl_space_type = “PROPERTIES”
bl_region_type = “WINDOW”
bl_context = “render”
bl_parent_id = “RENDER_PT_discord_notify”
bl_options = {‘DEFAULT_CLOSED’}

```
def draw(self, context):
    layout = self.layout
    scene = context.scene

    layout.prop(scene, "discord_color_preset", text="Color Theme")

    if scene.discord_color_preset == "CUSTOM":
        box = layout.box()
        box.label(text="Hex Colors (no #):", icon='COLOR')
        col = box.column(align=True)
        col.prop(scene, "discord_custom_color_start",    text="Start")
        col.prop(scene, "discord_custom_color_complete", text="Complete")
        col.prop(scene, "discord_custom_color_cancel",   text="Cancel")

    layout.separator()
    layout.prop(scene, "discord_custom_footer", icon='FONT_DATA')

    layout.separator()
    box = layout.box()
    box.label(text="Render Info Preview", icon='RENDER_STILL')
    col = box.column(align=True)
    col.label(text=f"Engine: {scene.render.engine}")
    res_x = int(scene.render.resolution_x * scene.render.resolution_percentage / 100)
    res_y = int(scene.render.resolution_y * scene.render.resolution_percentage / 100)
    col.label(text=f"Resolution: {res_x} × {res_y}  ({scene.render.resolution_percentage}%)")
    col.label(text=f"Frames: {scene.frame_start}–{scene.frame_end}  ({scene.frame_end - scene.frame_start + 1} total)")
```

# —————————————————————––

# Render Handlers

# —————————————————————––

@persistent
def render_pre_handler(scene):
global render_start_time, frame_times, last_frame_start
render_start_time = time.time()
frame_times = []
last_frame_start = time.time()

```
if not scene.discord_notify_on_start:
    return

total = scene.frame_end - scene.frame_start + 1
res_x = int(scene.render.resolution_x * scene.render.resolution_percentage / 100)
res_y = int(scene.render.resolution_y * scene.render.resolution_percentage / 100)
colors = get_embed_colors(scene)

embed = {
    "title": "🟡 Render Started",
    "color": colors["start"],
    "fields": [
        {"name": "📁 Scene",      "value": scene.name,                                             "inline": True},
        {"name": "🎬 Engine",     "value": scene.render.engine,                                    "inline": True},
        {"name": "🖼 Resolution", "value": f"{res_x} × {res_y}",                                  "inline": True},
        {"name": "🎞 Frames",     "value": f"{scene.frame_start}–{scene.frame_end} ({total} total)", "inline": True},
        {"name": "📂 Output",     "value": f"`{scene.render.filepath or 'Not set'}`",              "inline": False},
    ],
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}
send_discord_message(embed=embed, ping=False)
```

@persistent
def render_post_handler(scene):
global frame_times, last_frame_start

```
now = time.time()
if last_frame_start:
    frame_times.append(now - last_frame_start)
last_frame_start = now

if not scene.discord_progress_enabled:
    return

interval = scene.discord_progress_interval
start    = scene.frame_start
end      = scene.frame_end
total    = end - start + 1
done     = scene.frame_current - start + 1

if done % interval != 0 or done >= total:
    return

percent    = (done / total) * 100
bar_filled = int(percent / 10)
bar        = "█" * bar_filled + "░" * (10 - bar_filled)

recent     = frame_times[-interval:] if len(frame_times) >= interval else frame_times
avg_frame  = sum(recent) / max(len(recent), 1)
eta_str    = _format_duration(avg_frame * (total - done))
elapsed    = _format_duration(time.time() - render_start_time) if render_start_time else "?"

colors = get_embed_colors(scene)
embed = {
    "title": "⏳ Render Progress",
    "description": f"`{bar}` {percent:.1f}%",
    "color": colors["start"],
    "fields": [
        {"name": "🎞 Frame",      "value": f"{done} / {total}", "inline": True},
        {"name": "⏱ Elapsed",    "value": elapsed,             "inline": True},
        {"name": "🏁 ETA",       "value": eta_str,             "inline": True},
        {"name": "⚡ Avg/Frame", "value": f"{avg_frame:.1f}s", "inline": True},
    ],
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}
send_discord_message(embed=embed, ping=False)
```

@persistent
def render_complete_handler(scene):
global render_start_time, frame_times

```
elapsed_str = "Unknown"
if render_start_time:
    elapsed_str = _format_duration(time.time() - render_start_time)
    render_start_time = None

if not scene.discord_notify_on_complete:
    return

total     = scene.frame_end - scene.frame_start + 1
file_size = _get_file_size(scene.render.frame_path(frame=scene.frame_current))
avg_frame = (sum(frame_times) / len(frame_times)) if frame_times else None
colors    = get_embed_colors(scene)

fields = [
    {"name": "📁 Scene",        "value": scene.name,   "inline": True},
    {"name": "⏱ Render Time",  "value": elapsed_str,  "inline": True},
    {"name": "🎞 Total Frames", "value": str(total),   "inline": True},
    {"name": "📂 Output",       "value": f"`{scene.render.filepath or 'Not set'}`", "inline": False},
]
if avg_frame:
    fields.append({"name": "⚡ Avg/Frame", "value": f"{avg_frame:.1f}s", "inline": True})
if file_size:
    fields.append({"name": "💾 File Size", "value": file_size, "inline": True})

embed = {
    "title": "✅ Render Complete!",
    "description": "Your render finished successfully.",
    "color": colors["complete"],
    "fields": fields,
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}
send_discord_message(embed=embed, ping=True, force=True)
frame_times = []
```

@persistent
def render_cancel_handler(scene):
global render_start_time, frame_times

```
elapsed_str = "Unknown"
if render_start_time:
    elapsed_str = _format_duration(time.time() - render_start_time)
    render_start_time = None

if not scene.discord_notify_on_cancel:
    return

done   = scene.frame_current - scene.frame_start
total  = scene.frame_end - scene.frame_start + 1
colors = get_embed_colors(scene)

embed = {
    "title": "🚫 Render Cancelled",
    "description": "The render was stopped before completing.",
    "color": colors["cancel"],
    "fields": [
        {"name": "📁 Scene",      "value": scene.name,               "inline": True},
        {"name": "⏱ Time Spent", "value": elapsed_str,              "inline": True},
        {"name": "🎞 Progress",   "value": f"{done} / {total} frames", "inline": True},
    ],
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}
send_discord_message(embed=embed, ping=True, force=True)
frame_times = []
```

# —————————————————————––

# Helpers

# —————————————————————––

def _format_duration(seconds):
seconds = int(seconds)
h = seconds // 3600
m = (seconds % 3600) // 60
s = seconds % 60
if h > 0:   return f”{h}h {m}m {s}s”
elif m > 0: return f”{m}m {s}s”
return f”{s}s”

def _get_file_size(filepath):
try:
if filepath and os.path.isfile(filepath):
size = os.path.getsize(filepath)
if size >= 1_048_576: return f”{size / 1_048_576:.1f} MB”
elif size >= 1024:    return f”{size / 1024:.1f} KB”
return f”{size} B”
except Exception:
pass
return None

# —————————————————————––

# Register / Unregister

# —————————————————————––

classes = (
DiscordWebhookPreset,
DISCORD_UL_presets,
DISCORD_OT_test_webhook,
DISCORD_OT_add_preset,
DISCORD_OT_remove_preset,
DISCORD_OT_clear_webhook,
RENDER_PT_discord_notify,
RENDER_PT_discord_presets,
RENDER_PT_discord_mentions,
RENDER_PT_discord_notifications,
RENDER_PT_discord_embed,
)

def register():
for cls in classes:
bpy.utils.register_class(cls)

```
S = bpy.types.Scene
S.discord_webhook_presets     = CollectionProperty(type=DiscordWebhookPreset)
S.discord_active_preset_index = IntProperty(default=0)
S.discord_mention_user        = StringProperty(name="Mention User ID",  default="")
S.discord_mention_role        = StringProperty(name="Mention Role ID",  default="")
S.discord_thumbnail_url       = StringProperty(name="Thumbnail URL",    default="")
S.discord_render_note         = StringProperty(name="Render Note",      default="", description="Appended to all embeds for this render")
S.discord_notify_on_start     = BoolProperty(name="Render Started",     default=True)
S.discord_notify_on_complete  = BoolProperty(name="Render Complete",    default=True)
S.discord_notify_on_cancel    = BoolProperty(name="Render Cancelled",   default=True)
S.discord_progress_enabled    = BoolProperty(name="Frame Progress Updates", default=False)
S.discord_progress_interval   = IntProperty(name="Every N Frames", default=10, min=1, max=500)
S.discord_cooldown_seconds    = IntProperty(name="Cooldown (seconds)",  default=0, min=0, max=3600,
                                            description="Min seconds between notifications. 0 = off.")
S.discord_color_preset        = EnumProperty(name="Color Theme", default="DEFAULT", items=[
    ("DEFAULT", "Default", "Blue / Green / Red"),
    ("NEON",    "Neon",    "Magenta / Cyan / Red"),
    ("PASTEL",  "Pastel",  "Soft tones"),
    ("MONO",    "Mono",    "Greyscale"),
    ("CUSTOM",  "Custom",  "Your own hex colors"),
])
S.discord_custom_color_start    = StringProperty(name="Start Color",    default="3498DB", maxlen=6)
S.discord_custom_color_complete = StringProperty(name="Complete Color", default="2ECC71", maxlen=6)
S.discord_custom_color_cancel   = StringProperty(name="Cancel Color",   default="E74C3C", maxlen=6)
S.discord_custom_footer         = StringProperty(name="Custom Footer",  default="",
                                                 description="Leave blank for the default footer")

bpy.app.handlers.render_pre.append(render_pre_handler)
bpy.app.handlers.render_post.append(render_post_handler)
bpy.app.handlers.render_complete.append(render_complete_handler)
bpy.app.handlers.render_cancel.append(render_cancel_handler)

print("✅ Discord Render Notifier v3.0 registered.")
```

def unregister():
for lst, fn in [
(bpy.app.handlers.render_pre,      render_pre_handler),
(bpy.app.handlers.render_post,     render_post_handler),
(bpy.app.handlers.render_complete,  render_complete_handler),
(bpy.app.handlers.render_cancel,    render_cancel_handler),
]:
if fn in lst:
lst.remove(fn)

```
for prop in [
    "discord_webhook_presets", "discord_active_preset_index",
    "discord_mention_user", "discord_mention_role",
    "discord_thumbnail_url", "discord_render_note",
    "discord_notify_on_start", "discord_notify_on_complete", "discord_notify_on_cancel",
    "discord_progress_enabled", "discord_progress_interval",
    "discord_cooldown_seconds",
    "discord_color_preset",
    "discord_custom_color_start", "discord_custom_color_complete", "discord_custom_color_cancel",
    "discord_custom_footer",
]:
    if hasattr(bpy.types.Scene, prop):
        delattr(bpy.types.Scene, prop)

for cls in reversed(classes):
    bpy.utils.unregister_class(cls)

print("✅ Discord Render Notifier v3.0 unregistered.")
```

if **name** == “**main**”:
register()