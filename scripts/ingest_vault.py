"""
scripts/ingest_vault.py — Bulk Vault Ingestion Script

Sweeps TWO locations and indexes every .md file into OpenSearch:
  1. C:\\Second Brain  — the real Obsidian vault
  2. prodRAG/data/obsidian — previously ingested files (articles, youtube, etc.)
     → These are also COPIED into the real vault under the correct folders.

Usage:
    uv run python scripts/ingest_vault.py
    uv run python scripts/ingest_vault.py --dry-run     # show what would be indexed
    uv run python scripts/ingest_vault.py --retrolink   # also add wikilinks to existing notes
"""

import sys
import argparse
import logging
from pathlib import Path

# Make src importable when running as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest.universal_ingest import (
    VAULT,
    FOLDER_ARTICLES,
    FOLDER_YOUTUBE,
    index_markdown_file,
)
from src.obsidian.linker import build_link_index, retrolink_file

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# prodRAG legacy data folder
DATA_OBSIDIAN = Path(__file__).parent.parent / "data" / "obsidian"

# Map legacy folder names → real Obsidian vault folders
LEGACY_FOLDER_MAP = {
    "articles": FOLDER_ARTICLES,
    "youtube": FOLDER_YOUTUBE,
    "pdfs": "2-Source Materials/Books",
    "docs": "2-Source Materials",
    "journal": "1-Rough Notes",
    "notes": "6- Zettelkasten ( Main notes )",
}

# Folders/dirs to skip inside the vault
SKIP_DIRS = {".obsidian", ".git", ".trash", "logseq"}


def collect_vault_files(vault_path: Path) -> list[Path]:
    """Return all .md files in the vault, skipping system folders."""
    files = []
    for md_file in vault_path.rglob("*.md"):
        # Skip any path containing a system dir
        if any(part in SKIP_DIRS for part in md_file.parts):
            continue
        files.append(md_file)
    return files


def migrate_legacy_files(dry_run: bool) -> list[Path]:
    """
    Copy files from prodRAG/data/obsidian into C:\\Second Brain under correct folders.
    Returns list of destination paths.
    """
    if not DATA_OBSIDIAN.exists():
        logger.info("No legacy data/obsidian folder found, skipping migration.")
        return []

    migrated = []
    for legacy_folder, vault_folder in LEGACY_FOLDER_MAP.items():
        src_dir = DATA_OBSIDIAN / legacy_folder
        if not src_dir.exists():
            continue

        dest_dir = VAULT / vault_folder
        for src_file in src_dir.glob("*.md"):
            dest_file = dest_dir / src_file.name
            if dest_file.exists():
                logger.info(f"  [skip] Already in vault: {src_file.name}")
                migrated.append(dest_file)
                continue

            if dry_run:
                logger.info(f"  [dry-run] Would copy: {src_file.name} → {vault_folder}/")
            else:
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file.write_bytes(src_file.read_bytes())
                logger.info(f"  Copied: {src_file.name} → {vault_folder}/")
            migrated.append(dest_file)

    return migrated


def ingest_files(files: list[Path], dry_run: bool) -> tuple[int, int]:
    """Index a list of .md files into OpenSearch. Returns (ok_count, fail_count)."""
    ok = fail = 0
    for filepath in files:
        if dry_run:
            logger.info(f"  [dry-run] Would index: {filepath.relative_to(filepath.anchor)}")
            ok += 1
            continue
        try:
            index_markdown_file(filepath)
            ok += 1
        except Exception as e:
            logger.error(f"  Failed to index {filepath.name}: {e}")
            fail += 1
    return ok, fail


def retrolink_vault(vault_path: Path, dry_run: bool) -> tuple[int, int]:
    """Add [[wikilinks]] to all existing vault notes. Returns (modified, unchanged)."""
    logger.info("\n🔗 Building link index for retroactive wikilink injection...")
    link_index = build_link_index(vault_path)
    logger.info(f"   Found {len(link_index)} notes in vault.")

    modified = unchanged = 0
    for md_file in collect_vault_files(vault_path):
        if dry_run:
            logger.info(f"  [dry-run] Would retrolink: {md_file.name}")
            unchanged += 1
            continue
        changed = retrolink_file(md_file, vault_path, link_index)
        if changed:
            modified += 1
        else:
            unchanged += 1

    return modified, unchanged


def main():
    parser = argparse.ArgumentParser(
        description="Bulk ingest Obsidian vault + prodRAG legacy files into OpenSearch."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes.",
    )
    parser.add_argument(
        "--retrolink",
        action="store_true",
        help="Also retroactively add [[wikilinks]] to all existing vault notes.",
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Skip OpenSearch indexing (useful when OpenSearch is not running).",
    )
    args = parser.parse_args()

    logger.info(f"{'[DRY RUN] ' if args.dry_run else ''}🧠 Second Brain Vault Ingestion")
    logger.info(f"   Vault:  {VAULT}")
    logger.info(f"   Legacy: {DATA_OBSIDIAN}\n")

    # ── Step 1: Migrate legacy prodRAG/data/obsidian files ──────────────────
    logger.info("📦 Step 1: Migrating prodRAG/data/obsidian → real vault...")
    migrated = migrate_legacy_files(dry_run=args.dry_run)
    logger.info(f"   {len(migrated)} files processed.\n")

    # ── Step 2: Collect all vault .md files ─────────────────────────────────
    logger.info("📂 Step 2: Scanning vault for .md files...")
    vault_files = collect_vault_files(VAULT)
    logger.info(f"   Found {len(vault_files)} .md files in vault.\n")

    # ── Step 3: Index into OpenSearch ────────────────────────────────────────
    if args.skip_index:
        logger.info("⏭️  Step 3: Skipping OpenSearch indexing (--skip-index).\n")
        ok, fail = len(vault_files), 0
    else:
        logger.info("🔍 Step 3: Indexing files into OpenSearch...")
        ok, fail = ingest_files(vault_files, dry_run=args.dry_run)
        logger.info(f"   ✅ Indexed: {ok}  |  ❌ Failed: {fail}\n")

    # ── Step 4 (optional): Retroactive wikilink injection ────────────────────
    if args.retrolink:
        logger.info("🔗 Step 4: Retroactively adding [[wikilinks]] to existing notes...")
        modified, unchanged = retrolink_vault(VAULT, dry_run=args.dry_run)
        logger.info(f"   Modified: {modified}  |  Unchanged: {unchanged}\n")
    else:
        logger.info("ℹ️  Step 4: Skipping retrolink (run with --retrolink to enable).\n")

    # ── Summary ──────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("✅ Done!")
    logger.info(f"   Vault notes found:     {len(vault_files)}")
    logger.info(f"   Legacy files migrated: {len(migrated)}")
    if not args.skip_index:
        logger.info(f"   Indexed into OpenSearch: {ok}")
        logger.info(f"   Failed:                  {fail}")
    if args.retrolink:
        logger.info(f"   Notes retrolinked:       {modified}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
