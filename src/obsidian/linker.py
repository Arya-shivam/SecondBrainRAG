"""
obsidian/linker.py — Automatic Wikilink Engine for Obsidian Vault

Algorithm: Multi-pass Title Scanning with Word-Boundary Regex
─────────────────────────────────────────────────────────────
1. BUILD INDEX: Walk vault, collect every .md file's title (from frontmatter
   or filename stem). Build a sorted list, longest titles first to prevent
   partial matches (e.g., "RAG" shouldn't match inside "prodRAG").

2. LINKIFY: For each title in the index, run a word-boundary case-insensitive
   regex search against the content. If found and NOT already linked (i.e., not
   already wrapped in [[...]]), replace the FIRST occurrence with [[Title]].
   Subsequent occurrences are left as plain text (Obsidian convention).

3. RELATED NOTES: After linkification, collect all titles that were linked and
   append a "## Related Notes" section with [[link]] bullets at the bottom.

Key design choices:
- Titles sorted by length (descending) → longer phrases matched before sub-phrases.
- Skips linking a note to itself.
- Skips code blocks and frontmatter sections to avoid corrupting them.
- Idempotent: running linkify twice doesn't double-link anything.
"""

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Regex to detect if a phrase is already a wikilink  [[anything]]
_ALREADY_LINKED = re.compile(r"\[\[([^\]]+)\]\]")

# Regex to strip frontmatter block (--- ... ---) and code fences
_FRONTMATTER = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)


def build_link_index(vault_path: Path) -> dict[str, str]:
    """
    Scan the vault and return a mapping of {display_title: note_stem}.

    Title is extracted from YAML frontmatter `title:` field if present,
    otherwise falls back to the file stem (filename without .md).

    Returns dict sorted longest-first so multi-word phrases are matched
    before their constituent words.
    """
    index: dict[str, str] = {}
    for md_file in vault_path.rglob("*.md"):
        # Skip Obsidian config folder
        if ".obsidian" in md_file.parts:
            continue

        stem = md_file.stem
        title = stem  # fallback

        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("title:"):
                    extracted = line.removeprefix("title:").strip().strip('"').strip("'")
                    if extracted:
                        title = extracted
                    break
        except Exception:
            pass  # use stem as fallback

        index[title] = stem

    # Sort by title length descending (longest match first)
    return dict(sorted(index.items(), key=lambda x: len(x[0]), reverse=True))


def linkify(content: str, note_title: str, link_index: dict[str, str]) -> str:
    """
    Insert [[wikilinks]] into `content` for every vault note title found.

    Args:
        content:    Raw markdown content to process.
        note_title: Title of the note being written (to avoid self-linking).
        link_index: Output of build_link_index().

    Returns:
        Modified content with wikilinks injected and a Related Notes section.
    """
    if not link_index:
        return content

    # Separate frontmatter from body so we don't corrupt YAML
    fm_match = _FRONTMATTER.match(content)
    frontmatter = fm_match.group(0) if fm_match else ""
    body = content[len(frontmatter):]

    # Collect all phrases already linked so we don't double-link
    existing_links = set(_ALREADY_LINKED.findall(body))

    # Mask code blocks so we don't linkify inside them
    code_blocks: list[str] = []
    def _mask_code(m: re.Match) -> str:
        code_blocks.append(m.group(0))
        return f"__CODE_BLOCK_{len(code_blocks) - 1}__"
    masked_body = _CODE_FENCE.sub(_mask_code, body)

    linked_titles: list[str] = []

    for title, stem in link_index.items():
        # Don't link a note to itself
        if title.lower() == note_title.lower() or stem.lower() == note_title.lower():
            continue
        # Skip if already explicitly linked
        if title in existing_links or stem in existing_links:
            existing_links.add(title)
            linked_titles.append(title)
            continue

        # Word-boundary match, case-insensitive, not inside existing [[...]]
        pattern = re.compile(
            r"(?<!\[\[)"          # not preceded by [[
            r"\b" + re.escape(title) + r"\b"
            r"(?!\]\])",          # not followed by ]]
            re.IGNORECASE,
        )

        # Use a fresh sentinel list per title to avoid mutable-default-arg bug
        _replaced: list[bool] = []
        _current_title = title  # capture in closure

        def replace_first(m: re.Match, _sentinel: list = _replaced, _t: str = _current_title) -> str:
            if not _sentinel:
                _sentinel.append(True)
                linked_titles.append(_t)
                return f"[[{_t}]]"
            return m.group(0)

        new_body = pattern.sub(replace_first, masked_body, count=1)
        if new_body != masked_body:
            masked_body = new_body

    # Restore code blocks
    for i, block in enumerate(code_blocks):
        masked_body = masked_body.replace(f"__CODE_BLOCK_{i}__", block)

    body = masked_body

    # Append Related Notes section if we linked anything new
    unique_linked = list(dict.fromkeys(linked_titles))  # deduplicate, preserve order
    if unique_linked:
        related_section = "\n\n---\n\n## Related Notes\n\n"
        related_section += "\n".join(f"- [[{t}]]" for t in unique_linked)
        # Only add if section doesn't already exist
        if "## Related Notes" not in body:
            body += related_section

    return frontmatter + body


def retrolink_file(filepath: Path, vault_path: Path, link_index: dict[str, str]) -> bool:
    """
    Retroactively add wikilinks to an existing vault note in-place.

    Returns True if the file was modified, False if nothing changed.
    """
    try:
        original = filepath.read_text(encoding="utf-8", errors="ignore")
        # Extract title for self-link exclusion
        note_title = filepath.stem
        for line in original.splitlines():
            line = line.strip()
            if line.startswith("title:"):
                extracted = line.removeprefix("title:").strip().strip('"').strip("'")
                if extracted:
                    note_title = extracted
                break

        updated = linkify(original, note_title, link_index)
        if updated != original:
            filepath.write_text(updated, encoding="utf-8")
            logger.info(f"  Retrolinked: {filepath.name}")
            return True
        return False
    except Exception as e:
        logger.error(f"  Failed to retrolink {filepath.name}: {e}")
        return False
