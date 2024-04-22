from __future__ import annotations

from schorle.rendering_context import RENDERING_CONTEXT


def text(value: str):
    if not RENDERING_CONTEXT.get():
        raise RuntimeError("Text must be created inside a rendering context")
    else:
        rc = RENDERING_CONTEXT.get()
        rc.set_text(value)
