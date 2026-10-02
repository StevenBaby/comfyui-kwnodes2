"""Custom HTTP routes for comfyui-kwnodes2 (Prompt File Picker only).

These back the directory autocomplete and the file-list refresh + editor
read/write. Routes are prefixed /kwnodes2/ so they don't collide with the
comfyui-kwnodes /kwnodes/ routes, letting both packs coexist.
"""

import os
from aiohttp import web
from server import PromptServer

from .prompt_file_picker import PromptFilePicker, _extract_fenced, _replace_fenced, _list_files_abs
from .pathutil import _abs, _is_within, ROOT


@PromptServer.instance.routes.get("/kwnodes2/getpath_image")
async def get_path_image(request):
    """Return one level of subdirectory names under a ROOT-relative path."""
    query = request.rel_url.query
    if "path" not in query:
        return web.Response(status=204)

    path = _abs(query["path"])
    if not os.path.isdir(path):
        return web.json_response([])

    items = []
    try:
        for item in os.scandir(path):
            try:
                if item.is_dir():
                    items.append(item.name + "/")
            except OSError:
                pass
    except OSError:
        return web.json_response([])
    items.sort()
    return web.json_response(items)


@PromptServer.instance.routes.get("/kwnodes2/list_prompt_files")
async def list_prompt_files(request):
    """Return the .md/.txt/.srt files in a ROOT-relative directory (sub=1 recursive)."""
    directory = request.query.get("directory", "")
    sub = request.query.get("sub", "1") in ("1", "true", "True")
    try:
        files = _list_files_abs(directory, sub)
        return web.json_response({"files": files})
    except OSError as e:
        return web.json_response({"files": [], "error": str(e)}, status=500)


@PromptServer.instance.routes.get("/kwnodes2/read_prompt_file")
async def read_prompt_file(request):
    """Return the content of a prompt file (mode-aware; .srt always raw)."""
    directory = _abs(request.query.get("directory", ""))
    file = request.query.get("file", "")
    mode = request.query.get("mode", "fenced")
    if not file:
        return web.json_response({"content": ""}, status=400)
    path = os.path.join(directory, file)
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return web.json_response({"content": "", "error": str(e)}, status=500)

    ext = os.path.splitext(file)[1].lower()
    if mode == "fenced" and ext != ".srt":
        text = _extract_fenced(text)
    return web.json_response({"content": text})


@PromptServer.instance.routes.post("/kwnodes2/save_prompt_file")
async def save_prompt_file(request):
    """Write the edited prompt text back to its file (mode-aware; .srt raw)."""
    post = await request.post()
    directory = _abs(post.get("directory", ""))
    file = post.get("file", "")
    content = post.get("content", "")
    mode = post.get("mode", "fenced")
    if not file:
        return web.json_response({"ok": False, "error": "no file"}, status=400)
    path = os.path.join(directory, file)
    try:
        ext = os.path.splitext(file)[1].lower()
        if mode == "fenced" and ext != ".srt":
            with open(path, "r", encoding="utf-8") as f:
                original = f.read()
            new_text = _replace_fenced(original, content)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_text)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        return web.json_response({"ok": True})
    except OSError as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


@PromptServer.instance.routes.post("/kwnodes2/new_prompt_file")
async def new_prompt_file(request):
    """Create a new, empty prompt file named prompt_<n>.md in the directory."""
    post = await request.post()
    directory = _abs(post.get("directory", ""))
    try:
        n = 1
        while True:
            name = "prompt_%d.md" % n
            path = os.path.join(directory, name)
            if not os.path.exists(path):
                break
            n += 1
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        return web.json_response({"ok": True, "file": name})
    except OSError as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)
