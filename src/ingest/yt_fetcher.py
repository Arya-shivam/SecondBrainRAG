"""
YouTube Transcript Fetcher
--------------------------
Method 1: youtube-transcript-api  (fast, transcripts only)
Method 2: yt-dlp                  (fallback, more reliable)

Usage:
    python yt_fetcher.py <youtube_url>
    python yt_fetcher.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
"""

import sys
import re
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Transcript:
    video_id: str
    title: str
    url: str
    transcript: str
    method_used: str
    fetched_at: str
    duration_seconds: int | None = None
    channel: str | None = None


def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


# ─── Method 1: youtube-transcript-api ────────────────────────────────────────

def fetch_via_transcript_api(video_id: str) -> str | None:
    """
    Fast and simple. Works for most videos.
    Gets auto-generated captions too, not just manual ones.
    v1.2.4+: API is now instance-based, not class methods.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        )

        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)

            # Prefer manual English → auto English → any available
            try:
                transcript = transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
                except NoTranscriptFound:
                    # Take whatever is available, translate if needed
                    transcript = next(iter(transcript_list))
                    if transcript.language_code not in ["en", "en-US", "en-GB"]:
                        transcript = transcript.translate("en")

            fetched = transcript.fetch()
            full_text = " ".join(chunk.text for chunk in fetched)

            # Clean up common auto-caption artifacts
            full_text = re.sub(r"\[.*?\]", "", full_text)   # remove [Music], [Applause]
            full_text = re.sub(r"\s+", " ", full_text).strip()

            return full_text

        except (TranscriptsDisabled, NoTranscriptFound):
            print(f"  [transcript-api] No transcript available for {video_id}")
            return None
        except VideoUnavailable:
            print(f"  [transcript-api] Video unavailable: {video_id}")
            return None

    except Exception as e:
        print(f"  [transcript-api] Failed: {e}")
        return None


# ─── Method 2: yt-dlp ────────────────────────────────────────────────────────

def fetch_via_ytdlp(video_id: str) -> tuple[str | None, dict]:
    """
    More reliable fallback. Also fetches video metadata.
    Returns (transcript_text, metadata_dict)
    """
    import tempfile
    import os
    import glob

    url = f"https://www.youtube.com/watch?v={video_id}"
    metadata = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: get metadata (title, channel, duration)
        try:
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--dump-json",
                    "--no-download",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                info = json.loads(result.stdout)
                metadata = {
                    "title": info.get("title", "Unknown"),
                    "channel": info.get("uploader", info.get("channel", "Unknown")),
                    "duration": info.get("duration"),
                    "upload_date": info.get("upload_date"),
                    "description": (info.get("description") or "")[:500],
                }
        except Exception as e:
            print(f"  [yt-dlp] Metadata fetch failed: {e}")

        # Step 2: download subtitles
        try:
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--write-auto-sub",      # auto-generated captions
                    "--write-sub",           # manual captions (if available)
                    "--sub-lang", "en",
                    "--sub-format", "vtt",
                    "--skip-download",       # don't download the video
                    "--output", f"{tmpdir}/%(id)s",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Find the downloaded .vtt file
            vtt_files = glob.glob(f"{tmpdir}/*.vtt")
            if not vtt_files:
                print("  [yt-dlp] No subtitle file downloaded")
                return None, metadata

            transcript_text = parse_vtt(vtt_files[0])
            return transcript_text, metadata

        except subprocess.TimeoutExpired:
            print("  [yt-dlp] Timed out")
            return None, metadata
        except Exception as e:
            print(f"  [yt-dlp] Failed: {e}")
            return None, metadata


def parse_vtt(vtt_path: str) -> str:
    """Parse a .vtt subtitle file into clean plain text."""
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    text_lines = []
    seen = set()

    for line in lines:
        line = line.strip()
        # Skip VTT header, timestamps, cue settings, empty lines
        if (
            not line
            or line.startswith("WEBVTT")
            or line.startswith("NOTE")
            or "-->" in line
            or re.match(r"^\d+$", line)                    # cue numbers
            or re.match(r"^[\d:.,\s]+-->", line)           # timestamps
        ):
            continue

        # Remove inline tags like <00:00:01.000>, <c>, </c>
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\[.*?\]", "", line)   # [Music], [Applause]
        line = line.strip()

        if line and line not in seen:
            seen.add(line)
            text_lines.append(line)

    full_text = " ".join(text_lines)
    full_text = re.sub(r"\s+", " ", full_text).strip()
    return full_text


# ─── Main fetcher with fallback logic ─────────────────────────────────────────

def fetch_transcript(url: str) -> Transcript:
    """
    Tries youtube-transcript-api first (fast).
    Falls back to yt-dlp if that fails (slower but more reliable).
    """
    video_id = extract_video_id(url)
    print(f"\nFetching transcript for video: {video_id}")

    # --- Try Method 1 first ---
    print("  Trying youtube-transcript-api...")
    transcript_text = fetch_via_transcript_api(video_id)

    if transcript_text:
        print(f"  [OK] Got transcript via youtube-transcript-api ({len(transcript_text)} chars)")
        return Transcript(
            video_id=video_id,
            title=f"Video {video_id}",   # transcript-api doesn't give title
            url=url,
            transcript=transcript_text,
            method_used="youtube-transcript-api",
            fetched_at=datetime.now().isoformat(),
        )

    # --- Fallback to yt-dlp ---
    print("  Falling back to yt-dlp...")
    transcript_text, metadata = fetch_via_ytdlp(video_id)

    if transcript_text:
        print(f"  [OK] Got transcript via yt-dlp ({len(transcript_text)} chars)")
        return Transcript(
            video_id=video_id,
            title=metadata.get("title", f"Video {video_id}"),
            url=url,
            transcript=transcript_text,
            method_used="yt-dlp",
            fetched_at=datetime.now().isoformat(),
            duration_seconds=metadata.get("duration"),
            channel=metadata.get("channel"),
        )

    raise RuntimeError(
        f"Both methods failed for video {video_id}. "
        "Video may have no captions, be private, or be age-restricted."
    )


def to_obsidian_markdown(t: Transcript) -> str:
    """Convert transcript to Obsidian vault markdown with frontmatter."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r"[^\w\s-]", "", t.title).strip().replace(" ", "-").lower()

    return f"""---
source_type: youtube
video_id: {t.video_id}
url: {t.url}
title: "{t.title}"
channel: "{t.channel or 'Unknown'}"
date: {date_str}
duration_seconds: {t.duration_seconds or 'null'}
method: {t.method_used}
fetched_at: {t.fetched_at}
tags: [youtube]
ingested: false
---

# {t.title}

**Source:** [YouTube]({t.url})  
**Channel:** {t.channel or 'Unknown'}

## Transcript

{t.transcript}
"""


# ─── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python yt_fetcher.py <youtube_url>")
        print("Example: python yt_fetcher.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)

    url = sys.argv[1]

    try:
        transcript = fetch_transcript(url)

        print(f"\n{'-'*50}")
        print(f"Title:    {transcript.title}")
        print(f"Channel:  {transcript.channel}")
        print(f"Method:   {transcript.method_used}")
        print(f"Length:   {len(transcript.transcript)} chars")
        print(f"Preview:  {transcript.transcript[:200]}...")
        print(f"{'-'*50}\n")

        # Save as obsidian markdown
        md = to_obsidian_markdown(transcript)
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-{transcript.video_id}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Saved to: {filename}")

    except Exception as e:
        print(f"\n[Error] {e}")
        sys.exit(1)
