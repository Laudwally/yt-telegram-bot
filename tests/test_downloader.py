import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from downloader import MAX_FILESIZE_BYTES, is_youtube_url  # noqa: E402


def test_accepts_standard_watch_url():
    assert is_youtube_url("https://www.youtube.com/watch?v=jNQXAC9IVRw") is True


def test_accepts_short_youtu_be_url():
    assert is_youtube_url("https://youtu.be/jNQXAC9IVRw") is True


def test_accepts_shorts_url():
    assert is_youtube_url("https://www.youtube.com/shorts/jNQXAC9IVRw") is True


def test_accepts_url_without_www():
    assert is_youtube_url("https://youtube.com/watch?v=jNQXAC9IVRw") is True


def test_rejects_non_youtube_url():
    assert is_youtube_url("https://example.com/watch?v=123") is False


def test_rejects_plain_text():
    assert is_youtube_url("not a url at all") is False


def test_rejects_other_video_sites():
    assert is_youtube_url("https://vimeo.com/123456") is False


def test_strips_surrounding_whitespace():
    assert is_youtube_url("  https://youtu.be/jNQXAC9IVRw  ") is True


def test_max_filesize_is_under_telegrams_hard_limit():
    # Telegram's bot API hard cap is 50 MB; we should stay comfortably under it.
    assert MAX_FILESIZE_BYTES < 50 * 1024 * 1024
