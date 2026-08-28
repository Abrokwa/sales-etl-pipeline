# Columns that must exist in our sales data
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "customer_id",
    "customer_name",
    "customer_city",
    "product_id",
    "product_name",
    "category",
    "quantity",
    "unit_price",
]


def validate_sales_data(df):
    # Tell us that validation has started
    print("Running data-quality checks...")

    # The dataset should not be empty
    if df.empty:
        raise ValueError("Sales file is empty.")

    # Check that all required columns exist
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    # Make sure order IDs are unique
    duplicate_orders = df["order_id"].duplicated().sum()

    if duplicate_orders > 0:
        raise ValueError(
            f"Duplicate order IDs found: {duplicate_orders}"
        )

    # Check for missing values
    null_count = (
        df[REQUIRED_COLUMNS]
        .isnull()
        .sum()
        .sum()
    )

    if null_count > 0:
        raise ValueError(
            f"Null values found: {null_count}"
        )

    # Quantity must be greater than zero
    if (df["quantity"] <= 0).any():
        raise ValueError("Invalid quantity found.")

    # Price must be greater than zero
    if (df["unit_price"] <= 0).any():
        raise ValueError("Invalid unit price found.")

    # If we reach here, everything passed
    print("Data-quality checks passed.")