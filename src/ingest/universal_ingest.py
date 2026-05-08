import os
import argparse
import shutil
import logging
from pathlib import Path
from datetime import datetime

import fitz  # pymupdf
import trafilatura
from docx import Document

from . import yt_fetcher

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Configurable vault path, defaulting to ./data/obsidian
DEFAULT_VAULT_PATH = Path("data/obsidian").resolve()
VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH))

def ingest(source: str, tags: list[str] = None) -> Path:
    """
    Detects type of source (URL or file), extracts text, and writes to vault as .md
    """
    tags = tags or []
    source = source.strip()
    date = datetime.now().strftime("%Y-%m-%d")

    if source.startswith("http://") or source.startswith("https://"):
        if "youtube.com" in source or "youtu.be" in source:
            return _ingest_youtube(source, date, tags)
        return _ingest_url(source, date, tags)

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")

    ext = path.suffix.lower()

    if ext == ".pdf":
        return _ingest_pdf(path, date, tags)
    elif ext == ".docx":
        return _ingest_docx(path, date, tags)
    elif ext in [".md", ".txt"]:
        return _ingest_text(path, date, tags)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _write_vault(folder: str, title: str, text: str,
                  date: str, tags: list, meta: dict = None) -> Path:
    meta = meta or {}
    out_dir = VAULT / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    
    safe = title[:50].replace("/", "-").replace("\\", "-").replace(" ", "-").lower()
    # Remove any other problematic characters
    safe = "".join(c for c in safe if c.isalnum() or c == "-")
    if not safe:
        safe = "untitled"

    filepath = out_dir / f"{date}-{safe}.md"

    frontmatter_lines = [f"{k}: {v}" for k, v in meta.items()]
    frontmatter = "\n".join(frontmatter_lines) + ("\n" if frontmatter_lines else "")
    
    tags_str = ", ".join(tags)
    content = f"""---
source_type: {folder}
title: "{title}"
date: {date}
tags: [{tags_str}]
ingested: false
{frontmatter}---

# {title}

{text}
"""
    filepath.write_text(content, encoding="utf-8")
    logger.info(f"Saved → {filepath.name} to {out_dir}")
    return filepath


def _ingest_url(url: str, date: str, tags: list) -> Path:
    logger.info(f"Fetching URL: {url}")
    html = trafilatura.fetch_url(url)
    if not html:
        raise ValueError(f"Failed to fetch or received empty response from {url}")
        
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    if not text:
        raise ValueError(f"Could not extract article content from {url}")
        
    # Use first line as title, fallback to URL
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    title = lines[0][:80] if lines else url
    return _write_vault("articles", title, text, date,
                         ["article"] + tags, {"url": url})


def _ingest_pdf(path: Path, date: str, tags: list) -> Path:
    logger.info(f"Extracting PDF: {path}")
    doc = fitz.open(path)
    text = "\n".join(page.get_text() for page in doc)
    return _write_vault("pdfs", path.stem, text, date, ["pdf"] + tags)


def _ingest_docx(path: Path, date: str, tags: list) -> Path:
    logger.info(f"Extracting DOCX: {path}")
    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return _write_vault("docs", path.stem, text, date, ["doc"] + tags)


def _ingest_text(path: Path, date: str, tags: list) -> Path:
    logger.info(f"Copying Text/MD: {path}")
    text = path.read_text(encoding="utf-8")
    return _write_vault("journal", path.stem, text, date, ["journal"] + tags)

def _ingest_youtube(url: str, date: str, tags: list) -> Path:
    logger.info(f"Fetching YouTube transcript: {url}")
    transcript_obj = yt_fetcher.fetch_transcript(url)
    
    meta = {
        "video_id": transcript_obj.video_id,
        "url": transcript_obj.url,
        "channel": f'"{transcript_obj.channel or "Unknown"}"',
        "duration_seconds": transcript_obj.duration_seconds or 'null',
        "method": transcript_obj.method_used,
        "fetched_at": transcript_obj.fetched_at,
    }
    
    text = f"**Source:** [YouTube]({transcript_obj.url})  \n**Channel:** {transcript_obj.channel or 'Unknown'}\n\n## Transcript\n\n{transcript_obj.transcript}"
    
    return _write_vault("youtube", transcript_obj.title, text, date, ["youtube"] + tags, meta)

def main():
    parser = argparse.ArgumentParser(description="Universal Data Ingestion to Obsidian Vault")
    parser.add_argument("source", help="File path or URL to ingest")
    parser.add_argument("--tags", "-t", nargs="+", default=[], help="Optional tags to append (e.g. --tags AI ml)")
    
    args = parser.parse_args()
    
    try:
        result_path = ingest(args.source, tags=args.tags)
        logger.info(f"Successfully ingested! Path: {result_path}")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
