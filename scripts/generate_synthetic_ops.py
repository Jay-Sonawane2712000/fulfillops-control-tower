import csv
import random
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


RANDOM_SEED = 2712000

FAST_CATEGORY_KEYWORDS = (
    "beleza",
    "fashion",
    "eletron",
    "informatica",
    "telefonia",
    "relogios",
    "perfumaria",
    "papelaria",
)
BULKY_CATEGORY_KEYWORDS = (
    "moveis",
    "cama_mesa_banho",
    "construcao",
    "ferramentas",
    "eletrodomesticos",
    "climatizacao",
)

ISSUE_TYPES = ("missing", "damaged", "wrong", "failed", "refund")
NORTHEAST_STATES = {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"}


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def last_six_complete_month_window(purchase_dates: list[date]) -> tuple[date, date]:
    max_date = max(purchase_dates)
    latest_month_start = date(max_date.year, max_date.month, 1)
    latest_complete_month_start = (
        latest_month_start if max_date.day >= 28 else add_months(latest_month_start, -1)
    )
    start_date = add_months(latest_complete_month_start, -5)
    end_date = add_months(latest_complete_month_start, 1) - timedelta(days=1)
    return start_date, end_date


def build_warehouse_lookup(warehouses: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    lookup = {}
    for warehouse in warehouses:
        for state in warehouse["assigned_states"].split(";"):
            lookup[state] = warehouse

    southeast = next(row for row in warehouses if row["warehouse_id"] == "WH_SOUTHEAST")
    central_west = next(row for row in warehouses if row["warehouse_id"] == "WH_CENTRAL_WEST")
    for state in NORTHEAST_STATES:
        lookup[state] = southeast
    lookup.setdefault("", central_west)
    return lookup


def choose_order_category(
    order_id: str,
    items_by_order: dict[str, list[str]],
    product_categories: dict[str, str],
) -> str:
    categories = [
        product_categories.get(product_id, "")
        for product_id in items_by_order.get(order_id, [])
    ]
    categories = [category for category in categories if category]
    if not categories:
        return "unknown"
    return Counter(categories).most_common(1)[0][0]


def map_sla_tier(category_name: str) -> str:
    category = category_name.lower()
    if any(keyword in category for keyword in BULKY_CATEGORY_KEYWORDS):
        return "bulky"
    if any(keyword in category for keyword in FAST_CATEGORY_KEYWORDS):
        return "fast"
    return "standard"


def choose_carrier(
    rng: random.Random,
    warehouse_id: str,
    carriers: list[dict[str, str]],
) -> dict[str, str]:
    weights = []
    for carrier in carriers:
        carrier_id = carrier["carrier_id"]
        if carrier_id in {"CAR_A", "CAR_B"}:
            weight = 0.33
        elif carrier_id == "CAR_C":
            weight = 0.22
        else:
            weight = 0.12

        if carrier["warehouse_exception"] == warehouse_id:
            weight += 0.23
        weights.append(weight)

    return rng.choices(carriers, weights=weights, k=1)[0]


def find_anomaly(
    order_date: date,
    carrier_id: str,
    warehouse_id: str,
    anomalies: list[dict[str, str]],
) -> dict[str, str] | None:
    for anomaly in anomalies:
        start_date = date.fromisoformat(anomaly["start_date"])
        end_date = date.fromisoformat(anomaly["end_date"])
        carrier_match = (
            not anomaly["affected_carrier_id"]
            or anomaly["affected_carrier_id"] == carrier_id
        )
        warehouse_match = anomaly["affected_warehouse_id"] == warehouse_id
        if start_date <= order_date <= end_date and carrier_match and warehouse_match:
            return anomaly
    return None


def issue_probability(
    order: dict[str, str],
    review_score: int | None,
    carrier: dict[str, str],
    warehouse_id: str,
    anomaly: dict[str, str] | None,
) -> tuple[float, list[str]]:
    probability = 0.03
    signals = []

    delivered = parse_datetime(order["order_delivered_customer_date"])
    estimated = parse_datetime(order["order_estimated_delivery_date"])
    if delivered and estimated and delivered.date() > estimated.date():
        probability += 0.12
        signals.append("late_delivery")

    if review_score is not None and review_score <= 2:
        probability += 0.15
        signals.append("low_review")

    if carrier["carrier_id"] == "CAR_C":
        probability += 0.05
        signals.append("carrier_reliability")

    if carrier["warehouse_exception"] == warehouse_id:
        probability += 0.12
        signals.append("warehouse_carrier_weakness")

    if anomaly:
        if anomaly["anomaly_type"] == "sharp_spike":
            probability += 0.35
        elif anomaly["anomaly_type"] == "gradual_drift":
            start_date = date.fromisoformat(anomaly["start_date"])
            end_date = date.fromisoformat(anomaly["end_date"])
            order_date = parse_datetime(order["order_purchase_timestamp"]).date()
            span_days = max((end_date - start_date).days, 1)
            drift_factor = (order_date - start_date).days / span_days
            probability += 0.05 + (0.18 * drift_factor)
        signals.append("injected_anomaly")

    if order["order_status"] == "canceled":
        probability = max(probability, 0.95)
        signals.append("order_canceled")

    return min(probability, 0.95), signals


def choose_issue_type(
    rng: random.Random,
    order: dict[str, str],
    probability: float,
    anomaly: dict[str, str] | None,
) -> str:
    if order["order_status"] == "canceled":
        return "cancelled"

    if rng.random() >= probability:
        return "none"

    if anomaly and anomaly["anomaly_type"] == "sharp_spike":
        return rng.choices(["damaged", "missing", "wrong"], weights=[0.7, 0.2, 0.1], k=1)[0]

    if anomaly and anomaly["anomaly_type"] == "gradual_drift":
        return rng.choices(["failed", "refund", "missing"], weights=[0.6, 0.25, 0.15], k=1)[0]

    return rng.choice(ISSUE_TYPES)


def main() -> int:
    rng = random.Random(RANDOM_SEED)
    project_root = Path(__file__).resolve().parents[1]
    raw_olist_dir = project_root / "raw" / "olist"
    synthetic_dir = project_root / "raw" / "synthetic"
    generated_dir = synthetic_dir / "generated"

    orders = read_rows(raw_olist_dir / "olist_orders_dataset.csv")
    customers = read_rows(raw_olist_dir / "olist_customers_dataset.csv")
    items = read_rows(raw_olist_dir / "olist_order_items_dataset.csv")
    products = read_rows(raw_olist_dir / "olist_products_dataset.csv")
    reviews = read_rows(raw_olist_dir / "olist_order_reviews_dataset.csv")

    warehouses = read_rows(synthetic_dir / "warehouses.csv")
    carriers = read_rows(synthetic_dir / "carriers.csv")
    sla_targets = read_rows(synthetic_dir / "sla_targets.csv")
    anomalies = read_rows(synthetic_dir / "anomaly_windows.csv")

    purchase_dates = [
        parse_datetime(order["order_purchase_timestamp"]).date()
        for order in orders
        if order["order_purchase_timestamp"]
    ]
    start_date, end_date = last_six_complete_month_window(purchase_dates)
    filtered_orders = [
        order
        for order in orders
        if start_date
        <= parse_datetime(order["order_purchase_timestamp"]).date()
        <= end_date
    ]

    customer_states = {
        customer["customer_id"]: customer["customer_state"]
        for customer in customers
    }
    warehouse_lookup = build_warehouse_lookup(warehouses)
    sla_days = {row["sla_tier"]: row["target_days"] for row in sla_targets}
    product_categories = {
        product["product_id"]: product["product_category_name"]
        for product in products
    }
    review_scores = {}
    for review in reviews:
        order_id = review["order_id"]
        score = int(review["review_score"])
        review_scores[order_id] = min(score, review_scores.get(order_id, score))

    items_by_order = defaultdict(list)
    for item in items:
        items_by_order[item["order_id"]].append(item["product_id"])

    warehouse_rows = []
    carrier_rows = []
    sla_rows = []
    issue_rows = []

    for order in filtered_orders:
        order_id = order["order_id"]
        order_date = parse_datetime(order["order_purchase_timestamp"]).date()
        customer_state = customer_states.get(order["customer_id"], "")
        warehouse = warehouse_lookup.get(customer_state, warehouse_lookup[""])
        carrier = choose_carrier(rng, warehouse["warehouse_id"], carriers)
        category_name = choose_order_category(order_id, items_by_order, product_categories)
        sla_tier = map_sla_tier(category_name)
        anomaly = find_anomaly(
            order_date,
            carrier["carrier_id"],
            warehouse["warehouse_id"],
            anomalies,
        )

        probability, signals = issue_probability(
            order,
            review_scores.get(order_id),
            carrier,
            warehouse["warehouse_id"],
            anomaly,
        )
        issue_type = choose_issue_type(rng, order, probability, anomaly)
        issue_source = "none" if issue_type == "none" else signals[-1] if signals else "synthetic_baseline"

        warehouse_rows.append(
            {
                "order_id": order_id,
                "warehouse_id": warehouse["warehouse_id"],
                "warehouse_name": warehouse["warehouse_name"],
                "customer_state": customer_state,
            }
        )
        carrier_rows.append(
            {
                "order_id": order_id,
                "carrier_id": carrier["carrier_id"],
                "carrier_name": carrier["carrier_name"],
            }
        )
        sla_rows.append(
            {
                "order_id": order_id,
                "category_name": category_name,
                "sla_tier": sla_tier,
                "sla_target_days": sla_days[sla_tier],
            }
        )
        issue_rows.append(
            {
                "order_id": order_id,
                "issue_type": issue_type,
                "issue_source": issue_source,
                "synthetic_issue_probability": f"{probability:.4f}",
                "anomaly_flag": anomaly["anomaly_id"] if anomaly else "none",
            }
        )

    write_rows(
        generated_dir / "warehouse_assignments.csv",
        ["order_id", "warehouse_id", "warehouse_name", "customer_state"],
        warehouse_rows,
    )
    write_rows(
        generated_dir / "carrier_assignments.csv",
        ["order_id", "carrier_id", "carrier_name"],
        carrier_rows,
    )
    write_rows(
        generated_dir / "issue_flags.csv",
        [
            "order_id",
            "issue_type",
            "issue_source",
            "synthetic_issue_probability",
            "anomaly_flag",
        ],
        issue_rows,
    )
    write_rows(
        generated_dir / "order_sla_targets.csv",
        ["order_id", "category_name", "sla_tier", "sla_target_days"],
        sla_rows,
    )

    print("Synthetic operations generation")
    print(f"Filtered order window: {start_date} to {end_date}")
    print(f"Filtered orders: {len(filtered_orders)}")
    print(f"Output folder: {generated_dir.relative_to(project_root)}")
    print("\nGenerated files:")
    print(f"- warehouse_assignments.csv: {len(warehouse_rows)} rows")
    print(f"- carrier_assignments.csv: {len(carrier_rows)} rows")
    print(f"- issue_flags.csv: {len(issue_rows)} rows")
    print(f"- order_sla_targets.csv: {len(sla_rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
