"""comfyui-kwnodes2

Custom nodes for ComfyUI, built on the typed comfy_api.latest.io schema API.

Currently provides:
- "Prompt File Picker" (prompt_file_picker.py) — scan a directory for
  .md/.txt/.srt prompt files and output the selected file's text as a STRING.
  The directory field has VHS-style path autocomplete; the file list refreshes
  on change. An inline editor views/edits/saves back to disk.
- "Pad Audio" (pad_audio.py) — add silence to the start and/or end of an
  AUDIO, in seconds (float).
"""

import importlib

from .prompt_file_picker import NODE_CLASS_MAPPINGS as _PICKER_NODES
from .prompt_file_picker import NODE_DISPLAY_NAME_MAPPINGS as _PICKER_NAMES
from .pad_audio import NODE_CLASS_MAPPINGS as _PAD_NODES
from .pad_audio import NODE_DISPLAY_NAME_MAPPINGS as _PAD_NAMES

WEB_DIRECTORY = "./web"

NODE_CLASS_MAPPINGS = {**_PICKER_NODES, **_PAD_NODES}

NODE_DISPLAY_NAME_MAPPINGS = {**_PICKER_NAMES, **_PAD_NAMES}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

# Register the custom HTTP routes (directory autocomplete + file list refresh).
importlib.import_module(".routes", __name__)
