"""Pad Audio — prepend/append silence to an AUDIO in seconds (float).

A small, reusable audio utility on the typed comfy_api.latest.io API. Give it
an AUDIO and how many seconds of silence to add at the start and/or end; it
returns the same audio with the silence inserted. Both pads are independent and
default to 0 (no change).
"""

import torch

from comfy_api.latest import io


class PadAudio(io.ComfyNode):
    """Add silence to the start and/or end of an AUDIO (in seconds)."""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="PadAudio",
            display_name="Pad Audio",
            category="kwnodes/audio",
            description=(
                "Add silence to the start and/or end of an audio track, in "
                "seconds (float). pad_start prepends silence, pad_end appends "
                "it; both default to 0 (no change). The waveform is padded "
                "with zeros at the audio's own sample rate."
            ),
            inputs=[
                io.Audio.Input(
                    "audio",
                    tooltip="The audio to pad.",
                ),
                io.Float.Input(
                    "pad_start",
                    default=0.0,
                    min=0.0,
                    max=3600.0,
                    step=0.01,
                    tooltip="Seconds of silence to prepend at the start.",
                ),
                io.Float.Input(
                    "pad_end",
                    default=0.0,
                    min=0.0,
                    max=3600.0,
                    step=0.01,
                    tooltip="Seconds of silence to append at the end.",
                ),
            ],
            outputs=[
                io.Audio.Output(display_name="audio"),
            ],
        )

    @classmethod
    def execute(cls, audio, pad_start=0.0, pad_end=0.0) -> io.NodeOutput:
        if audio is None:
            raise ValueError("Pad Audio: input audio is None.")

        waveform = audio.get("waveform")
        sample_rate = audio.get("sample_rate")
        if waveform is None or sample_rate is None:
            raise ValueError("Pad Audio: audio missing waveform/sample_rate.")
        if not isinstance(waveform, torch.Tensor):
            raise ValueError("Pad Audio: waveform must be a torch.Tensor.")

        sample_rate = int(sample_rate)
        pad_start = float(pad_start or 0.0)
        pad_end = float(pad_end or 0.0)

        start_samples = int(round(pad_start * sample_rate))
        end_samples = int(round(pad_end * sample_rate))

        # Short-circuit when there is nothing to add.
        if start_samples <= 0 and end_samples <= 0:
            return io.NodeOutput(audio)

        parts = [waveform]
        if start_samples > 0:
            silence_start = waveform.new_zeros(
                (*waveform.shape[:-1], start_samples)
            )
            parts.insert(0, silence_start)
        if end_samples > 0:
            silence_end = waveform.new_zeros((*waveform.shape[:-1], end_samples))
            parts.append(silence_end)

        out_waveform = torch.cat(parts, dim=-1)
        return io.NodeOutput(
            {"waveform": out_waveform, "sample_rate": sample_rate}
        )


NODE_CLASS_MAPPINGS = {
    "PadAudio": PadAudio,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PadAudio": "Pad Audio",
}
