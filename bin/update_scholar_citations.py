#!/usr/bin/env python

import os
import sys
import tempfile
import yaml
from datetime import datetime


def load_scholar_user_id() -> str:
    """Load the Google Scholar user ID from the configuration file."""
    config_file = "_data/socials.yml"
    if not os.path.exists(config_file):
        print(
            f"Configuration file {config_file} not found. Please ensure the file exists and contains your Google Scholar user ID."
        )
        sys.exit(1)
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
        scholar_user_id = config.get("scholar_userid")
        if not scholar_user_id:
            print(
                "No 'scholar_userid' found in the configuration file. Please add 'scholar_userid' to _data/socials.yml."
            )
            sys.exit(1)
        return scholar_user_id
    except yaml.YAMLError as e:
        print(
            f"Error parsing YAML file {config_file}: {e}. Please check the file for correct YAML syntax."
        )
        sys.exit(1)


SCHOLAR_USER_ID: str = load_scholar_user_id()
OUTPUT_FILE: str = "_data/citations.yml"


def get_scholar_citations() -> None:
    """Fetch and update Google Scholar citation data."""
    print(f"Fetching citations for Google Scholar ID: {SCHOLAR_USER_ID}")
    from scholarly import scholarly

    existing_data = None
    today = datetime.now().strftime("%Y-%m-%d")

    # Load the previous successful snapshot; every invocation fetches again.
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r") as f:
                existing_data = yaml.safe_load(f)
            if (
                existing_data
                and "metadata" in existing_data
                and "last_updated" in existing_data["metadata"]
            ):
                print(f"Last updated on: {existing_data['metadata']['last_updated']}")
        except Exception as e:
            print(
                f"Warning: Could not read existing citation data from {OUTPUT_FILE}: {e}. The file may be missing or corrupted."
            )

    citation_data = {
        "metadata": {"last_updated": today, "scholar_userid": SCHOLAR_USER_ID},
        "papers": {},
    }

    scholarly.set_timeout(15)
    scholarly.set_retries(3)
    try:
        author = scholarly.search_author_id(SCHOLAR_USER_ID)
        author_data = scholarly.fill(author)
    except Exception as e:
        print(
            f"Error fetching author data from Google Scholar for user ID '{SCHOLAR_USER_ID}': {e}. Please check your internet connection and Scholar user ID."
        )
        sys.exit(1)

    if not author_data:
        print(
            f"Could not fetch author data for user ID '{SCHOLAR_USER_ID}'. Please verify the Scholar user ID and try again."
        )
        sys.exit(1)

    if author_data.get("scholar_id") != SCHOLAR_USER_ID:
        raise ValueError("Fetched author ID does not match the configured profile.")

    if "publications" not in author_data:
        print(f"No publications found in author data for user ID '{SCHOLAR_USER_ID}'.")
        sys.exit(1)

    for pub in author_data["publications"]:
        try:
            pub_id = pub.get("author_pub_id") or pub.get("pub_id")
            if not pub_id:
                raise ValueError("Publication has no ID; refusing a partial update.")

            if not pub_id.startswith(SCHOLAR_USER_ID + ":"):
                raise ValueError("Publication ID does not belong to configured profile.")

            title = pub.get("bib", {}).get("title", "Unknown Title")
            year = pub.get("bib", {}).get("pub_year", "Unknown Year")
            citations = pub.get("num_citations", 0)

            print(f"Found: {title} ({year}) - Citations: {citations}")

            citation_data["papers"][pub_id] = {
                "title": title,
                "year": year,
                "citations": citations,
            }
        except Exception as e:
            raise ValueError(
                f"Error processing publication '{pub.get('bib', {}).get('title', 'Unknown')}': {e}. Update aborted."
            ) from e

    # Compare new data with existing data
    if existing_data == citation_data:
        print("No changes in citation data. Skipping file update.")
        return

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=os.path.dirname(OUTPUT_FILE), delete=False
        ) as f:
            temporary_file = f.name
            yaml.safe_dump(citation_data, f, width=1000, sort_keys=True)
        os.replace(temporary_file, OUTPUT_FILE)
        print(f"Citation data saved to {OUTPUT_FILE}")
    except Exception as e:
        if "temporary_file" in locals() and os.path.exists(temporary_file):
            os.unlink(temporary_file)
        print(
            f"Error writing citation data to {OUTPUT_FILE}: {e}. Please check file permissions and disk space."
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        get_scholar_citations()
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
