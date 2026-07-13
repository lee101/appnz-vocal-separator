"""Cog adapter for Demucs music source separation."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path as LocalPath

from cog import BaseRunner, Input, Path


STEM_MODES = ("two", "four")
FORMATS = ("mp3", "wav")
MODELS = ("htdemucs", "htdemucs_ft", "mdx_extra")


def demucs_args(audio: str, output: str, stems: str, audio_format: str, model: str) -> list[str]:
    if stems not in STEM_MODES:
        raise ValueError("stems must be two or four")
    if audio_format not in FORMATS:
        raise ValueError("format must be mp3 or wav")
    if model not in MODELS:
        raise ValueError(f"unsupported model: {model}")
    args = [
        sys.executable,
        "-m",
        "demucs.separate",
        "--device",
        "cuda",
        "--jobs",
        "1",
        "--name",
        model,
        "--out",
        output,
        "--filename",
        "{stem}.{ext}",
    ]
    if stems == "two":
        args.extend(["--two-stems", "vocals"])
    if audio_format == "mp3":
        args.extend(["--mp3", "--mp3-bitrate", "320"])
    args.append(audio)
    return args


class Runner(BaseRunner):
    def setup(self) -> None:
        import torch

        self._device = "cuda" if torch.cuda.is_available() else "cpu"

    def run(
        self,
        audio: Path = Input(description="Song as WAV, MP3, FLAC, or OGG"),
        stems: str = Input(description="Stem set", default="two", choices=["two", "four"]),
        format: str = Input(description="Output audio format", default="mp3", choices=["mp3", "wav"]),
        model: str = Input(description="Demucs model", default="htdemucs", choices=["htdemucs", "htdemucs_ft", "mdx_extra"]),
    ) -> Path:
        work = LocalPath(tempfile.mkdtemp(prefix="appnz-demucs-"))
        args = demucs_args(str(audio), str(work), stems, format, model)
        args[args.index("cuda")] = self._device
        try:
            subprocess.run(args, check=True, timeout=45 * 60)
            files = sorted(work.rglob(f"*.{format}"))
            if not files:
                raise RuntimeError("Demucs completed without producing stems")
            archive_base = f"/tmp/{LocalPath(str(audio)).stem}-{stems}-stems"
            archive = shutil.make_archive(archive_base, "zip", root_dir=work)
            return Path(archive)
        finally:
            shutil.rmtree(work, ignore_errors=True)
