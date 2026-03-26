#!/usr/bin/env python3
"""
download-training-pages.py
==========================
Downloads paired manuscript images + transcriptions from FromThePage
for use as training data in the self-taught paleography experiment.

Each download gives you two files:
  - An image of the manuscript page (JPG)
  - The human-made transcription of that page (TXT)

These pairs are what the learning agent studies to figure out
how to read early modern handwriting.

Usage:
    python3 download-training-pages.py --output ~/Desktop/blind-test-self-taught/training-materials

    # To list available pages for a manuscript before downloading:
    python3 download-training-pages.py --list 32026529

    # To download specific pages from specific manuscripts:
    python3 download-training-pages.py --output ./output --pages 32026529:5,10,15 54701:8,12

How it works:
    1. Fetches the IIIF manifest for each manuscript from FromThePage
    2. Finds the image URL and transcription URL for each page
    3. Downloads both and saves them as paired files

Note: Be patient — the script waits 2 seconds between downloads
to be respectful to the FromThePage server.
"""

import json
import os
import re
import sys
import time
import html as html_module
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


# ============================================================
# CONFIGURATION
# ============================================================

# Wait between downloads to be polite to the server
REQUEST_DELAY = 2

# Manuscripts to EXCLUDE (we already use these for testing/training)
EXCLUDE_WORK_IDS = {
    "32175110",  # Henslow MS688 — our test manuscript
    "55048",     # Sedley MS534 — already in training set
    "25002909",  # Brumwich MS160 — already in training set
    "32038497",  # Bulkeley MS169 — already in training set
    "32142178",  # Jane Jackson MS373 — water damage, excluded
}

# Pre-selected manuscripts for the experiment.
# These are all 100% transcribed, English-language recipe books
# from different collections and time periods.
#
# The "difficulty" rating is a rough guess based on the period,
# collection, and type of hand. We'll confirm once we see the images.
#
# Format: (work_id, short_name, full_title, difficulty_guess)

SELECTED_MANUSCRIPTS = [
    # All manuscripts are from the early modern period (1500s-1690s),
    # 95%+ transcribed, and English-language recipe/medical books.
    #
    # Difficulty is a rough guess — we'll confirm from the images.

    # --- Likely easier (later 17th c., institutional collections) ---
    ("54701", "ayscough-ms1026",
     "Wellcome: Lady Ayscough (MS1026) [1692]", "easier"),
    ("25010759", "stjohn-ms4338",
     "Wellcome: Johanna Saint John (MS4338) [1680]", "easier"),

    # --- Likely moderate (mid-17th c., mixed hands) ---
    ("32086974", "rcp-ms504",
     "Royal College of Physicians: Medical receipts (MS504) [late 17th c.]", "moderate"),
    ("32028396", "rcp-ms502",
     "Royal College of Physicians: Medical receipts (MS502) [17th c.]", "moderate"),
    ("52011", "fanshawe-ms7113",
     "Wellcome: Lady Ann Fanshawe (MS7113) [1651-1680]", "moderate"),

    # --- Likely harder (earlier 17th c., multiple hands over time) ---
    ("25002908", "gibson-ms311",
     "Wellcome: John and Joan Gibson (MS311) [1632-1717]", "harder"),
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def fetch_url(url, description=""):
    """
    Downloads content from a URL and returns it as a string.
    Includes a polite delay and error handling.
    """
    if description:
        print(f"  Fetching {description}...")
    else:
        print(f"  Fetching {url[:80]}...")

    try:
        # Create a request with a user-agent header so the server
        # knows we're a research script, not a bot
        request = Request(url, headers={
            "User-Agent": "DaggerObelus-RecipeProject/1.0 (research; sarahcbonanno@gmail.com)"
        })
        with urlopen(request, timeout=30) as response:
            content = response.read().decode("utf-8", errors="replace")

        # Be polite — wait before the next request
        time.sleep(REQUEST_DELAY)
        return content

    except (URLError, HTTPError) as e:
        print(f"  ERROR downloading {url}: {e}")
        return None


def fetch_json(url, description=""):
    """Downloads a URL and parses the JSON response."""
    content = fetch_url(url, description)
    if content is None:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  ERROR parsing JSON: {e}")
        return None


def strip_html(text):
    """
    Removes HTML tags from text and decodes HTML entities.
    For example: "<p>Take &amp; boil</p>" becomes "Take & boil"
    """
    # Remove HTML tags
    text = re.sub(r'<br\s*/?>', '\n', text)  # Convert <br> to newlines
    text = re.sub(r'<p\s*/?>', '', text)      # Remove <p> tags
    text = re.sub(r'</p>', '\n', text)        # Convert </p> to newlines
    text = re.sub(r'<[^>]+>', '', text)        # Remove all remaining tags
    # Decode HTML entities like &amp; &lt; etc.
    text = html_module.unescape(text)
    # Clean up extra whitespace/newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def get_manifest(work_id):
    """
    Fetches the IIIF manifest for a manuscript.
    The manifest contains the list of all pages with their
    image URLs and links to transcription text.
    """
    url = f"https://fromthepage.com/iiif/{work_id}/manifest"
    return fetch_json(url, f"manifest for work {work_id}")


def list_pages(manifest):
    """
    Given a manifest, returns a list of pages with their info.
    Each page is a dict with: page_number, label, image_url,
    transcription_url, canvas_id
    """
    pages = []
    canvases = manifest.get("sequences", [{}])[0].get("canvases", [])

    for i, canvas in enumerate(canvases):
        page_info = {
            "page_number": i + 1,
            "label": canvas.get("label", f"Page {i+1}"),
            "canvas_id": canvas.get("@id", ""),
            "image_url": None,
            "transcription_url": None,
        }

        # Get image URL from the images array
        images = canvas.get("images", [])
        if images:
            resource = images[0].get("resource", {})
            page_info["image_url"] = resource.get("@id")

        # Get transcription URL from otherContent (annotation list)
        other_content = canvas.get("otherContent", [])
        for item in other_content:
            if "transcription" in item.get("@id", "").lower():
                page_info["transcription_url"] = item["@id"]
                break

        # Fallback: try seeAlso for HTML transcription
        if not page_info["transcription_url"]:
            see_also = canvas.get("seeAlso", [])
            for item in see_also:
                if "transcription" in item.get("@id", "").lower():
                    page_info["transcription_url"] = item["@id"]
                    break

        pages.append(page_info)

    return pages


def download_transcription(transcription_url):
    """
    Downloads the transcription text for a single page.
    FromThePage returns this as a IIIF annotation list (JSON).
    We extract the text content from it.
    """
    data = fetch_json(transcription_url, "transcription")
    if data is None:
        return None

    # The annotation list has a "resources" array.
    # Each resource has a "resource" with "chars" containing the text.
    resources = data.get("resources", [])
    text_parts = []
    for resource in resources:
        chars = resource.get("resource", {}).get("chars", "")
        if chars:
            text_parts.append(strip_html(chars))

    if not text_parts:
        # Maybe it's HTML format instead of annotation list
        # Try treating the whole response as text
        content = fetch_url(transcription_url, "transcription (HTML fallback)")
        if content:
            return strip_html(content)
        return None

    return "\n".join(text_parts)


def download_image(image_url, save_path):
    """
    Downloads a manuscript page image and saves it to disk.
    """
    print(f"  Downloading image...")
    try:
        request = Request(image_url, headers={
            "User-Agent": "DaggerObelus-RecipeProject/1.0 (research; sarahcbonanno@gmail.com)"
        })
        with urlopen(request, timeout=60) as response:
            image_data = response.read()

        with open(save_path, "wb") as f:
            f.write(image_data)

        # Show file size so you know it downloaded properly
        size_kb = len(image_data) / 1024
        print(f"  Saved image ({size_kb:.0f} KB): {save_path}")
        time.sleep(REQUEST_DELAY)
        return True

    except (URLError, HTTPError) as e:
        print(f"  ERROR downloading image: {e}")
        return False


def download_page(manuscript_name, page_info, output_dir):
    """
    Downloads both the image and transcription for one page
    and saves them as a paired set.
    """
    page_num = page_info["page_number"]
    label = page_info["label"]
    print(f"\n--- {manuscript_name} page {page_num} ({label}) ---")

    # Create filenames
    base_name = f"{manuscript_name}-page{page_num:03d}"
    image_path = os.path.join(output_dir, f"{base_name}.jpg")
    text_path = os.path.join(output_dir, f"{base_name}-transcription.txt")

    # Skip if already downloaded
    if os.path.exists(image_path) and os.path.exists(text_path):
        print(f"  Already downloaded, skipping.")
        return True

    # Download transcription first (smaller, faster — lets us check
    # if the page actually has transcription text before downloading
    # the larger image file)
    if page_info["transcription_url"]:
        transcription = download_transcription(page_info["transcription_url"])
    else:
        print(f"  No transcription URL found, skipping.")
        return False

    if not transcription or len(transcription.strip()) < 20:
        print(f"  Transcription is empty or too short, skipping.")
        return False

    # Save transcription
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(transcription)
    print(f"  Saved transcription ({len(transcription)} chars): {text_path}")

    # Download image
    if page_info["image_url"]:
        # Try to get a reasonable resolution — not the maximum
        # (which can be huge) but large enough to read the hand.
        # Replace /full/max/ with /full/1500,/ for ~1500px wide
        image_url = page_info["image_url"]
        image_url_sized = re.sub(
            r'/full/[^/]+/',
            '/full/1500,/',
            image_url
        )
        success = download_image(image_url_sized, image_path)
        if not success:
            # Fall back to original URL if resizing fails
            print("  Retrying with original image URL...")
            success = download_image(image_url, image_path)
        return success
    else:
        print(f"  No image URL found, skipping.")
        return False


# ============================================================
# MAIN SCRIPT
# ============================================================

def cmd_list(work_id):
    """List all available pages for a manuscript."""
    print(f"\nFetching manifest for work {work_id}...")
    manifest = get_manifest(work_id)
    if not manifest:
        print("Failed to fetch manifest.")
        return

    title = manifest.get("label", "Unknown")
    pages = list_pages(manifest)

    print(f"\n{title}")
    print(f"Total pages: {len(pages)}")
    print(f"\n{'Page':>6}  {'Label':<30}  {'Has Image':>10}  {'Has Text':>10}")
    print("-" * 70)
    for p in pages:
        has_img = "yes" if p["image_url"] else "no"
        has_txt = "yes" if p["transcription_url"] else "no"
        print(f"{p['page_number']:>6}  {p['label']:<30}  {has_img:>10}  {has_txt:>10}")


def cmd_download(output_dir, page_specs):
    """
    Download specific pages from specific manuscripts.

    page_specs is a list of strings like "32026529:5,10,15"
    meaning: from work 32026529, download pages 5, 10, and 15.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Find the short name for each work ID
    name_lookup = {ms[0]: ms[1] for ms in SELECTED_MANUSCRIPTS}

    total_downloaded = 0
    total_failed = 0

    for spec in page_specs:
        parts = spec.split(":")
        work_id = parts[0]

        # Get manuscript name
        ms_name = name_lookup.get(work_id, f"ms-{work_id}")

        # Fetch manifest
        print(f"\n{'='*60}")
        print(f"Manuscript: {ms_name} (work {work_id})")
        print(f"{'='*60}")
        manifest = get_manifest(work_id)
        if not manifest:
            print("Failed to fetch manifest, skipping.")
            total_failed += 1
            continue

        pages = list_pages(manifest)

        # Parse page numbers
        if len(parts) > 1:
            page_nums = [int(n) for n in parts[1].split(",")]
        else:
            # Default: download pages 10, 20, 30 (skip early pages
            # which are often title pages or blank)
            page_nums = [10, 20, 30]

        # Download each requested page
        for page_num in page_nums:
            if page_num < 1 or page_num > len(pages):
                print(f"\n  Page {page_num} does not exist (manuscript has {len(pages)} pages)")
                total_failed += 1
                continue

            page_info = pages[page_num - 1]
            success = download_page(ms_name, page_info, output_dir)
            if success:
                total_downloaded += 1
            else:
                total_failed += 1

    print(f"\n{'='*60}")
    print(f"Done! Downloaded {total_downloaded} pages, {total_failed} failed/skipped.")
    print(f"Files saved to: {output_dir}")


def cmd_auto(output_dir, count=10):
    """
    Automatically select and download a good mix of training pages.

    Picks pages from across the selected manuscripts, choosing
    pages from the middle of each manuscript (where recipe text
    is most likely — early pages are often title pages).
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"Auto-selecting ~{count} training pages from {len(SELECTED_MANUSCRIPTS)} manuscripts...")
    print(f"Output directory: {output_dir}")

    # Strategy: pick 1 page from each manuscript first (for variety),
    # then go back for seconds if we need more pages.
    # Choose pages from the middle third of each manuscript.

    total_downloaded = 0
    total_failed = 0
    round_num = 0

    while total_downloaded < count:
        round_num += 1
        for work_id, short_name, title, difficulty in SELECTED_MANUSCRIPTS:
            if total_downloaded >= count:
                break

            print(f"\n{'='*60}")
            print(f"Manuscript: {short_name} ({difficulty})")
            print(f"  {title}")
            print(f"{'='*60}")

            manifest = get_manifest(work_id)
            if not manifest:
                print("  Failed to fetch manifest, skipping.")
                total_failed += 1
                continue

            pages = list_pages(manifest)
            total_pages = len(pages)

            if total_pages < 5:
                print(f"  Only {total_pages} pages, skipping.")
                continue

            # Pick a page from the middle third, offset by round
            # Round 1: ~33% through, Round 2: ~50%, Round 3: ~66%
            target = int(total_pages * (0.25 + 0.15 * round_num))
            target = min(target, total_pages)
            target = max(target, 5)  # Don't pick very early pages

            page_info = pages[target - 1]

            # Check if already downloaded
            base_name = f"{short_name}-page{target:03d}"
            image_path = os.path.join(output_dir, f"{base_name}.jpg")
            if os.path.exists(image_path):
                print(f"  Page {target} already downloaded, trying next...")
                # Try the next page
                target = min(target + 5, total_pages)
                page_info = pages[target - 1]
                base_name = f"{short_name}-page{target:03d}"
                image_path = os.path.join(output_dir, f"{base_name}.jpg")
                if os.path.exists(image_path):
                    continue

            success = download_page(short_name, page_info, output_dir)
            if success:
                total_downloaded += 1
            else:
                total_failed += 1

    print(f"\n{'='*60}")
    print(f"Done! Downloaded {total_downloaded} pages, {total_failed} failed/skipped.")
    print(f"Files saved to: {output_dir}")


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

def print_usage():
    """Print help text explaining how to use the script."""
    print("""
download-training-pages.py — Download paired manuscript images + transcriptions

COMMANDS:

  --auto [--output DIR] [--count N]
      Automatically select and download N training pages (default: 10)
      from a pre-selected mix of manuscripts.

      Example:
        python3 download-training-pages.py --auto --output ~/Desktop/training --count 10

  --list WORK_ID
      List all available pages for a manuscript (useful for picking
      specific pages to download).

      Example:
        python3 download-training-pages.py --list 32026529

  --pages SPEC [SPEC ...] --output DIR
      Download specific pages from specific manuscripts.
      Each SPEC is: WORK_ID:PAGE1,PAGE2,PAGE3

      Example:
        python3 download-training-pages.py --pages 32026529:5,10 54701:8 --output ./output

AVAILABLE MANUSCRIPTS (pre-selected, 100% transcribed):
""")
    for work_id, short_name, title, difficulty in SELECTED_MANUSCRIPTS:
        print(f"  {work_id:>10}  [{difficulty:<8}]  {title}")
    print()


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print_usage()
        sys.exit(0)

    # Parse arguments
    output_dir = None
    count = 10

    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output_dir = os.path.expanduser(args[idx + 1])

    if "--count" in args:
        idx = args.index("--count")
        if idx + 1 < len(args):
            count = int(args[idx + 1])

    if "--list" in args:
        idx = args.index("--list")
        if idx + 1 < len(args):
            cmd_list(args[idx + 1])
        else:
            print("Error: --list requires a work ID")
        sys.exit(0)

    if "--pages" in args:
        if not output_dir:
            print("Error: --pages requires --output DIR")
            sys.exit(1)
        idx = args.index("--pages")
        # Collect all specs until the next flag
        specs = []
        for a in args[idx + 1:]:
            if a.startswith("--"):
                break
            specs.append(a)
        cmd_download(output_dir, specs)
        sys.exit(0)

    if "--auto" in args:
        if not output_dir:
            output_dir = os.path.expanduser(
                "~/Desktop/blind-test-self-taught/training-materials"
            )
        cmd_auto(output_dir, count)
        sys.exit(0)

    print("Unknown command. Use --help for usage.")
    sys.exit(1)
