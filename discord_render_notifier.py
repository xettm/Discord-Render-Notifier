bl_info = {
    "name": "Discord Render Notifier",
    "blender": (3, 0, 0),
    "location": "Properties > Render Tab",
    "category": "Render",
    "author": "Dodo",
    "version": (1, 5),
    "description": "Sends a Discord notification when a render is finished or cancelled",
}

import bpy
from bpy.props import StringProperty, BoolProperty
import time
import requests

# -------------------------------------------------------------------
# Panel in Render Properties
# -------------------------------------------------------------------
class RENDER_PT_discord_notify(bpy.types.Panel):
    bl_label = "Discord Render Notifier"
    bl_idname = "RENDER_PT_discord_notify"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Webhook Settings")
        layout.prop(scene, "discord_webhook_url")
        layout.prop(scene, "discord_mention_user")
        layout.prop(scene, "discord_mention_role")
        layout.prop(scene, "discord_notify_on_start")  # <-- Add toggle

# -------------------------------------------------------------------
# Global variable to track render start time
# -------------------------------------------------------------------
render_start_time = None

# -------------------------------------------------------------------
# Send Discord message
# -------------------------------------------------------------------
def send_discord_message(content=None, embed=None, ping=True):
    """
    Sends a message to the specified Discord webhook.

    Parameters:
        content (str, optional): The message content to send.
        embed (dict, optional): An embed object to include in the message.
        ping (bool, optional): Whether to include user/role mentions in the message.

    Behavior:
        - Uses the Discord webhook URL from the current Blender scene.
        - Optionally mentions a user or role if their IDs are set in the scene properties.
        - Prints a warning if the webhook URL is not set.
        - Prints a success or error message after attempting to send.
    """
    scene = bpy.context.scene
    webhook = scene.discord_webhook_url.strip()
    if not webhook:
        print("⚠️ Discord webhook URL not set!")
        return

    mentions = ""
    if ping:
        if scene.discord_mention_user.strip():
            mentions += f"<@{scene.discord_mention_user.strip()}> "
        if scene.discord_mention_role.strip():
            mentions += f"<@&{scene.discord_mention_role.strip()}> "

    payload = {}
    if content:
        payload["content"] = mentions + content
    else:
        payload["content"] = mentions

    if embed:
        payload["embeds"] = [embed]

    try:
        response = requests.post(webhook, json=payload)
        response.raise_for_status()
        print("✅ Discord notification sent")
    except Exception as e:
        print(f"❌ Failed to send Discord message: {e}")

# -------------------------------------------------------------------
# Render handlers
# -------------------------------------------------------------------
def render_pre_handler(scene):
    global render_start_time
    elapsed_str = "Unknown"
    if render_start_time:
        elapsed = time.time() - render_start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
    render_start_time = time.time()

    if not scene.discord_notify_on_start:
        return  # Don't send message if toggle is off

    embed = {
        "title": "🟡 Render Started",
        "color": 3447003,  # Blue
        "fields": [
            {"name": "Scene", "value": scene.name, "inline": True},
            {"name": "Output", "value": f"`{scene.render.filepath}`", "inline": False},
                        {"name": "Render Time", "value": elapsed_str, "inline": True},

            {"name": "Current Frame", "value": str(scene.frame_current), "inline": True},
            {"name": "Total Frames", "value": str(scene.frame_end - scene.frame_start + 1), "inline": True}
        ],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    # ping=False disables mentions
    send_discord_message(embed=embed, ping=False)

def render_complete_handler(scene):
    global render_start_time
    elapsed_str = "Unknown"
    if render_start_time:
        elapsed = time.time() - render_start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        render_start_time = None  # Reset after use

    current_frame = scene.frame_current
    total_frames = scene.frame_end - scene.frame_start + 1

    embed = {
        "title": "🎉 Render Finished!",
        "color": 3066993,  # Green
        "fields": [
            {"name": "Scene", "value": scene.name, "inline": True},
            {"name": "Output", "value": f"`{scene.render.filepath}`", "inline": False},
            {"name": "Total Frames", "value": str(total_frames), "inline": True},
            {"name": "Render Time", "value": elapsed_str, "inline": True}
        ],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    send_discord_message(embed=embed, ping=True)

def render_cancel_handler(scene):
    embed = {
        "title": "❌ Render Cancelled",
        "color": 15158332,  # Red
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    send_discord_message(embed=embed, ping=True)

# -------------------------------------------------------------------
# Register / Unregister
# -------------------------------------------------------------------
classes = (RENDER_PT_discord_notify,)

def register():
    # Register panel
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register Scene properties
    bpy.types.Scene.discord_webhook_url = StringProperty(
        name="Discord Webhook URL",
        description="Paste your Discord webhook URL here",
        default=""
    )
    bpy.types.Scene.discord_mention_user = StringProperty(
        name="Mention User ID",
        description="Discord User ID to ping (optional)",
        default=""
    )
    bpy.types.Scene.discord_mention_role = StringProperty(
        name="Mention Role ID",
        description="Discord Role ID to ping (optional)",
        default=""
    )
    bpy.types.Scene.discord_notify_on_start = BoolProperty(
        name="Send Start Render Message",
        description="Send a Discord message when rendering starts",
        default=True
    )

    # Add render handlers
    bpy.app.handlers.render_pre.append(render_pre_handler)
    bpy.app.handlers.render_complete.append(render_complete_handler)
    bpy.app.handlers.render_cancel.append(render_cancel_handler)

def unregister():
    # Remove render handlers
    if render_pre_handler in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.remove(render_pre_handler)
    if render_complete_handler in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(render_complete_handler)
    if render_cancel_handler in bpy.app.handlers.render_cancel:
        bpy.app.handlers.render_cancel.remove(render_cancel_handler)

    # Remove Scene properties
    del bpy.types.Scene.discord_webhook_url
    del bpy.types.Scene.discord_mention_user
    del bpy.types.Scene.discord_mention_role
    del bpy.types.Scene.discord_notify_on_start

    # Unregister panel
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
