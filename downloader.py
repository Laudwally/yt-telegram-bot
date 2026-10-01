"""YouTube download logic, kept separate from the Telegram bot handlers so it
can be tested and reused without touching the Telegram API."""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yt_dlp

# The standard Telegram Bot API caps files sent by bots at 50 MB (a local Bot
# API server can raise this to 2 GB, but that's a separate, heavier setup —
# see README). Leave some headroom below the hard limit.
MAX_FILESIZE_BYTES = 49 * 1024 * 1024

YOUTUBE_URL_RE = re.compile(
    r"^https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[\w-]+"
)


class DownloadError(Exception):
    """Raised when a video can't be fetched or doesn't fit Telegram's size limit."""


@dataclass
class VideoInfo:
    title: str
    duration_seconds: int
    uploader: str
    webpage_url: str


def is_youtube_url(text: str) -> bool:
    return bool(YOUTUBE_URL_RE.match(text.strip()))


def get_video_info(url: str) -> VideoInfo:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return VideoInfo(
        title=info.get("title", "Unknown title"),
        duration_seconds=int(info.get("duration") or 0),
        uploader=info.get("uploader", "Unknown"),
        webpage_url=info.get("webpage_url", url),
    )


def download_video(url: str, out_dir: Path, max_filesize_bytes: int = MAX_FILESIZE_BYTES) -> Path:
    """Downloads video capped at 480p (merging separate video/audio DASH
    streams via ffmpeg, which modern YouTube serves almost exclusively — a
    single combined "best" format rarely exists anymore). The `filesize`
    field yt-dlp reports is frequently missing for these streams, so rather
    than filter on it upfront, this downloads at a resolution cap intended to
    stay under the limit and verifies the actual file size afterward,
    deleting and raising DownloadError if it still doesn't fit.

    Requires ffmpeg on PATH to merge the separate streams.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(out_dir / "%(id)s.%(ext)s")

    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "outtmpl": out_template,
        "format": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise DownloadError("yt-dlp returned no video information.")
            filename = Path(ydl.prepare_filename(info))
    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(str(e)) from e

    # merge_output_format can change the actual extension from what
    # prepare_filename predicted before the merge happened.
    if not filename.exists():
        candidate = filename.with_suffix(".mp4")
        if candidate.exists():
            filename = candidate

    if not filename.exists():
        raise DownloadError("Download finished but the output file is missing — this is unexpected.")

    if filename.stat().st_size > max_filesize_bytes:
        filename.unlink(missing_ok=True)
        raise DownloadError(
            "This video is too large to send even at 480p (Telegram bots cap files at 50 MB). "
            "Try 'Audio only' instead."
        )

    return filename


def download_audio(url: str, out_dir: Path) -> Path:
    """Extracts audio as MP3. Requires ffmpeg to be installed and on PATH."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(out_dir / "%(id)s.%(ext)s")

    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "outtmpl": out_template,
        "format": "bestaudio/best",
        "noplaylist": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}
        ],
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(str(e)) from e

    mp3_path = out_dir / f"{info['id']}.mp3"
    if not mp3_path.exists():
        raise DownloadError("Audio extraction failed — is ffmpeg installed and on PATH?")
    return mp3_path


def make_temp_download_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="ytbot_"))
