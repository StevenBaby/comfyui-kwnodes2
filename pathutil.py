"""Path helpers shared by kwnodes2 nodes.

Only the bits the Prompt File Picker needs: the ROOT ceiling and `_abs` /
`_is_within` path confinement. The full Load Image / Load Audio nodes live in
comfyui-kwnodes and are not (yet) part of kwnodes2.
"""

import os

# Directory ceiling: ComfyUI's working directory. The directory picker is
# confined to this subtree (no escaping upward via "..").
ROOT = os.path.realpath(os.getcwd())

# File extensions the prompt picker accepts.
PROMPT_EXTENSIONS = (".md", ".txt", ".srt")


def _is_within(path, root):
    """True if `path` is `root` or inside it (both realpath'd, no `..` escape)."""
    p = os.path.realpath(path)
    r = os.path.realpath(root)
    return p == r or p.startswith(r + os.sep)


def _abs(directory):
    """Resolve a directory (relative to ROOT) to an absolute path, confined to
    ROOT. A leading '/' input is treated as relative anyway (stripped), so the
    field always shows a ROOT-relative path like 'prompts' or 'prompts/sub'.
    """
    directory = os.path.expanduser(directory or "").strip()
    # Treat the value as ROOT-relative; drop any leading separators so a pasted
    # absolute path still lands inside ROOT rather than escaping it.
    directory = directory.lstrip("/")
    path = os.path.realpath(os.path.join(ROOT, directory))
    if not _is_within(path, ROOT):
        return ROOT
    return path
