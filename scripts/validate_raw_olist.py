from pathlib import Path


EXPECTED_OLIST_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
    "product_category_name_translation.csv",
    "olist_customers_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_geolocation_dataset.csv",
]


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    raw_olist_dir = project_root / "raw" / "olist"

    print("Raw Olist data validation")
    print(f"Expected folder: {raw_olist_dir.relative_to(project_root)}")

    if not raw_olist_dir.exists():
        print("\nFAIL: raw/olist folder was not found.")
        print("\nMissing files:")
        for filename in EXPECTED_OLIST_FILES:
            print(f"- {filename}")
        return 1

    if not raw_olist_dir.is_dir():
        print("\nFAIL: raw/olist exists but is not a folder.")
        return 1

    missing_files = [
        filename
        for filename in EXPECTED_OLIST_FILES
        if not (raw_olist_dir / filename).is_file()
    ]

    if missing_files:
        print("\nFAIL: Missing expected Olist CSV files.")
        print("\nMissing files:")
        for filename in missing_files:
            print(f"- {filename}")
        return 1

    print("\nPASS: All expected Olist CSV files are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
