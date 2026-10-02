# comfyui-kwnodes2

Custom nodes for ComfyUI, built on the typed `comfy_api.latest.io` schema API.

## Nodes

### Prompt File Picker

Scan a directory for `.md` / `.txt` / `.srt` prompt files and output the
selected file's text as a `STRING`.

- **Directory** field: ROOT-relative with VHS-style path autocomplete (confined
  to the ComfyUI project root).
- **sub** toggle: list files in subdirectories too, named relative to the
  directory.
- **mode**: `fenced` (extract the ``` fenced body, strip `#` comment lines) or
  `raw` (whole file).
- **.srt files are always read raw** — no fences, and the numbered lines are not
  stripped as comments.
- **Editor**: an inline multiline editor shows the file content; ↻ Refresh
  re-scans, 💾 Save writes back, ➕ New creates `prompt_<n>.md`.

The STRING output carries a real type, so automation (e.g. ComfyUI-AutoFlow)
can connect it by type.

## Relationship to comfyui-kwnodes

This is the successor to `comfyui-kwnodes`. The old `PromptFilePicker` lives on
as `PromptFilePickerLegacy` in that pack (marked `DEPRECATED`) so existing
workflows keep loading; migrate to this pack's `PromptFilePicker` for `.srt`
support and the typed API.
