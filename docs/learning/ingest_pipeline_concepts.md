# Ingestion Pipeline Concepts: Capturing Knowledge

This document explains the concepts and mechanics behind the "Ingestion Layer" of your Second Brain. The goal of this pipeline is to provide zero-friction capture of information (articles, videos, PDFs) from the web directly into your local storage.

## 1. Zero-Friction Capture Tools

### The Chrome Extension
The browser extension serves as your primary bridge between the web and your Second Brain.
*   **`manifest.json`**: The configuration file for the extension. We specified permissions for `activeTab` (to read the current webpage URL), `scripting` (to interact with the page), and `notifications` (for observability). Crucially, we added host permissions for `http://127.0.0.1:8000/*` to allow the extension to bypass browser security and communicate with your local backend.
*   **`background.js`**: A Service Worker that runs in the background of Chrome. When you trigger the extension (via the context menu "Send to Dhi"), it captures the URL and sends an HTTP POST request to your FastAPI backend. 
*   **UI Observability**: To make the ingestion process "frictionless" but not "invisible", we utilized `chrome.notifications.create`. This gives you immediate, native desktop popups telling you if the capture was "Sending...", "Success", or "Failed", allowing you to confidently close the tab without checking your backend logs.

## 2. API Exposure (`src/routers/ingest.py`)
This file defines the `/api/ingest` endpoint. It acts as the gatekeeper, receiving URLs from the Chrome Extension (and eventually the Telegram bot), running them through a background task, and returning a fast HTTP 200 response. By running the actual extraction in a background task, the user interface (the browser) isn't forced to wait for long PDF downloads or YouTube processing.

## 3. The Ingestion Engine

### Universal Ingestion (`src/ingest/universal_ingest.py`)
This is the master router for content processing. It inspects the URL and dynamically routes it to the correct parser:
1.  **YouTube Router**: If the URL contains "youtube.com" or "youtu.be", it hands off execution to `yt_fetcher.py`.
2.  **PDF Parser (`pymupdf`)**: If the URL ends in `.pdf`, it downloads the binary file and extracts the text page-by-page.
3.  **Web Article Scraper (`trafilatura`)**: For standard web pages, it uses Trafilatura. This library is designed to strip away ads, navigation bars, and footers, extracting only the main body text of an article.

### YouTube Extractor (`src/ingest/yt_fetcher.py`)
Videos require completely different processing logic than text:
*   **`yt-dlp`**: An industry-standard library we use purely to extract rich metadata: the exact video title, channel name, and upload date.
*   **`youtube-transcript-api`**: Extracts the actual spoken words (captions) natively from YouTube's API without downloading the heavy video or audio files.

## 4. The Obsidian Data Contract
The final step of the ingestion script is saving the parsed content. Instead of throwing it directly into the database, we save it as a physical `.md` file in `/app/data/obsidian/`.

**Why save physical files?**
This ensures your data is future-proof and accessible outside the RAG system. If the database crashes, you still own your raw notes in an open format.

**YAML Frontmatter**
Every generated file includes a header like this:
```yaml
---
title: "Understanding the Second Brain"
source: "youtube"
author: "Tiago Forte"
date: "2026-05-08"
ingested: false
---
```
This is the **Data Contract** with Phase 3 (Airflow). Airflow will periodically scan the `data/obsidian/` folder, find any files where `ingested: false`, chunk the text, compute embeddings, push them to OpenSearch, and then update the file to `ingested: true`. This decoupled architecture makes the system incredibly resilient.
