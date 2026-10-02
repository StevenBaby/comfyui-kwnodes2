"""Prompt File Picker — scan a directory for .md/.txt/.srt prompt files and
output the selected file's text as a STRING.

This is the kwnodes2 port of the comfyui-kwnodes PromptFilePicker, rewritten on
the typed `comfy_api.latest.io` schema API so the STRING output carries a real
type that automation (e.g. ComfyUI-AutoFlow) can connect on.

Directory field: ROOT-relative with VHS-style autocomplete (confined to the
project root). `sub` toggle lists files in subdirectories. The file list
refreshes on change; an inline editor lets you view/edit and save back.
"""

import os
import re

from comfy_api.latest import io

from .pathutil import ROOT, _abs, _is_within, PROMPT_EXTENSIONS

NO_FILES = "(no prompt files)"

# .srt has no ``` fences and its numbered lines must NOT be stripped as
# comments, so it is always read raw regardless of the mode toggle.
RAW_EXTENSIONS = (".srt",)


def _list_files_abs(directory, sub=True):
    """Return .md/.txt/.srt files under `directory` (ROOT-relative), newest first.
    With `sub`, walk subdirectories and prefix names with the subpath."""
    directory = _abs(directory)

    if not sub:
        try:
            entries = [
                e
                for e in os.listdir(directory)
                if e.lower().endswith(PROMPT_EXTENSIONS)
                and os.path.isfile(os.path.join(directory, e))
            ]
        except OSError:
            return [NO_FILES]
        return _sort_by_mtime(directory, entries)

    found = []  # (relpath, abspath)
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        for f in files:
            if not f.lower().endswith(PROMPT_EXTENSIONS):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, directory)
            found.append((rel, full))
    if not found:
        return [NO_FILES]
    found.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
    return [rel for rel, _ in found]


def _sort_by_mtime(directory, entries):
    entries = list(entries)
    entries.sort(
        key=lambda e: os.path.getmtime(os.path.join(directory, e)),
        reverse=True,
    )
    return entries if entries else [NO_FILES]


def _extract_fenced(text):
    """Return the content of all ``` fenced blocks, joined by newlines."""
    blocks = re.findall(r"```[^\n]*\n(.*?)```", text, flags=re.DOTALL)
    if not blocks:
        return text
    return "\n".join(b.strip("\n") for b in blocks)


def _replace_fenced(text, new_content):
    """Replace the content of ``` fenced blocks in `text` with `new_content`,
    preserving everything outside the fences. If there is exactly one block,
    swap its body; with multiple blocks, split new_content across them. If
    there are no fences at all, wrap new_content in a fresh ``` block."""
    blocks = re.findall(r"```[^\n]*\n(.*?)```", text, flags=re.DOTALL)
    if not blocks:
        return "```\n" + new_content.strip("\n") + "\n```\n"
    if len(blocks) == 1:
        return re.sub(
            r"```[^\n]*\n(.*?)```",
            "```\n" + new_content.strip("\n") + "\n```",
            text,
            count=1,
            flags=re.DOTALL,
        )
    # Multiple blocks: replace them sequentially with split content.
    parts = new_content.split("\n\n")

    def repl(m):
        nonlocal parts
        return "```\n" + (parts.pop(0) if parts else "") + "\n```"

    return re.sub(
        r"```[^\n]*\n(.*?)```", repl, text, count=len(blocks), flags=re.DOTALL
    )


class PromptFilePicker(io.ComfyNode):
    """Pick a prompt file (.md/.txt/.srt) and output its text as a STRING."""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="PromptFilePicker",
            display_name="Prompt File Picker",
            category="kwnodes",
            description=(
                "Pick a prompt directory (ROOT-relative, inline autocomplete) "
                "and a .md/.txt/.srt file inside it; output the file's text as "
                "a STRING. mode 'raw' = the whole file; mode 'fenced' = only "
                "the ``` fenced prompt body (.srt is always read raw). With "
                "'sub' on (default), files in subdirectories are listed too, "
                "named relative to the directory. Newest files first."
            ),
            inputs=[
                io.String.Input(
                    "directory",
                    default="prompts",
                    socketless=True,
                    tooltip="Directory to scan, relative to the ComfyUI root. VHS-style autocomplete.",
                ),
                io.Boolean.Input(
                    "sub",
                    default=True,
                    tooltip="ON: also list files in subdirectories, named relative to the directory.",
                ),
                io.Combo.Input(
                    "file",
                    options=_list_files_abs("prompts", True),
                    tooltip="The prompt file to read. Newest first. Press ↻ Refresh after adding a file.",
                ),
                io.Combo.Input(
                    "mode",
                    options=["raw", "fenced"],
                    default="fenced",
                    tooltip="'fenced' = only the ``` fenced body; 'raw' = the whole file. .srt is always raw.",
                ),
                io.String.Input(
                    "editor",
                    default="",
                    multiline=True,
                    socketless=True,
                    tooltip="Inline editor showing the file content. Save writes back to the file.",
                ),
            ],
            outputs=[
                io.String.Output(display_name="text"),
            ],
        )

    @classmethod
    def validate_inputs(cls, directory=None, sub=None, file=None, mode=None, editor=None, **kwargs):
        # LINKED inputs resolve to None at validation time; only check real values.
        if directory is None or file is None:
            return True
        files = _list_files_abs(directory, True if sub is None else sub)
        if file not in files and file != NO_FILES:
            return "Prompt File Picker: file '%s' not found in %s" % (file, directory)
        return True

    @classmethod
    def fingerprint_inputs(cls, directory="prompts", sub=True, file=NO_FILES, mode="fenced", editor=None, **kwargs):
        # Cache on mtime so edits (via Save / external editor) re-read the file.
        path = os.path.join(_abs(directory), str(file or ""))
        try:
            return os.path.getmtime(path)
        except OSError:
            return float("NaN")

    @classmethod
    def execute(cls, directory, sub, file, mode="fenced", editor=None) -> io.NodeOutput:
        if file == NO_FILES or not file:
            raise ValueError("Prompt File Picker: no file selected")

        directory = _abs(directory)
        path = os.path.join(directory, str(file))
        if not _is_within(path, ROOT):
            raise ValueError(
                "Prompt File Picker: path %s is outside the project root %s"
                % (path, ROOT)
            )

        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            raise ValueError("Prompt File Picker: cannot read %s: %s" % (path, e))

        # .srt is always read raw (no fences, and numbered lines aren't comments).
        ext = os.path.splitext(str(file))[1].lower()
        if mode == "fenced" and ext not in RAW_EXTENSIONS:
            text = _extract_fenced(text)
            # Strip comment lines (those starting with '#', ignoring leading space).
            lines = [ln for ln in text.split("\n") if not ln.lstrip().startswith("#")]
            text = "\n".join(lines)

        return io.NodeOutput(text)


NODE_CLASS_MAPPINGS = {
    "PromptFilePicker": PromptFilePicker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptFilePicker": "Prompt File Picker",
}
