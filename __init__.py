# __init__.py
print("✅ kmlbdh Video Combine: Module loaded!")

# Import all node classes
from .kmlbdh_video_combine import NODE_CLASS_MAPPINGS as vc_mappings, NODE_DISPLAY_NAME_MAPPINGS as vc_display
from .kmlbdh_ram_cleaner import NODE_CLASS_MAPPINGS as rc_mappings, NODE_DISPLAY_NAME_MAPPINGS as rc_display

# Combine all mappings
NODE_CLASS_MAPPINGS = {}
NODE_CLASS_MAPPINGS.update(vc_mappings)
NODE_CLASS_MAPPINGS.update(rc_mappings)

NODE_DISPLAY_NAME_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS.update(vc_display)
NODE_DISPLAY_NAME_MAPPINGS.update(rc_display)

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']