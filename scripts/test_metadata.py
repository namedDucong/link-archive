import json
import sys

from crawler.metadata import fetch_page_metadata_as_dict


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/test_metadata.py <URL>")
        sys.exit(1)

    url = sys.argv[1]

    try:
        metadata = fetch_page_metadata_as_dict(url)
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()