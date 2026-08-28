import pandas as pd


def clean_sales_data(df):
    # Start with a copy so we don't change the original data
    clean_df = df.copy()

    # This will store records that we reject
    quarantine = []

    # Remove completely empty rows
    clean_df = clean_df.dropna(how="all")

    # Find duplicate orders
    duplicates = clean_df[
        clean_df["order_id"].duplicated(keep="first")
    ].copy()

    # Record why duplicate records were rejected
    for _, row in duplicates.iterrows():
        quarantine.append({
            "order_id": row["order_id"],
            "reason": "Duplicate order ID"
        })

    # Keep only the first occurrence of each order
    clean_df = clean_df.drop_duplicates(
        subset=["order_id"],
        keep="first"
    )

    # Make sure quantity and price are numbers
    clean_df["quantity"] = pd.to_numeric(
        clean_df["quantity"],
        errors="coerce"
    )

    clean_df["unit_price"] = pd.to_numeric(
        clean_df["unit_price"],
        errors="coerce"
    )

    # Find records with invalid quantities
    invalid_quantity = clean_df[
        clean_df["quantity"].isna() |
        (clean_df["quantity"] <= 0)
    ].copy()

    # Record the rejected orders
    for _, row in invalid_quantity.iterrows():
        quarantine.append({
            "order_id": row["order_id"],
            "reason": "Invalid quantity"
        })

    # Keep only valid quantities
    clean_df = clean_df[
        clean_df["quantity"].notna() &
        (clean_df["quantity"] > 0)
    ]

    # Find records with invalid prices
    invalid_price = clean_df[
        clean_df["unit_price"].isna() |
        (clean_df["unit_price"] <= 0)
    ].copy()

    # Record the rejected orders
    for _, row in invalid_price.iterrows():
        quarantine.append({
            "order_id": row["order_id"],
            "reason": "Invalid unit price"
        })

    # Keep only valid prices
    clean_df = clean_df[
        clean_df["unit_price"].notna() &
        (clean_df["unit_price"] > 0)
    ]

    # Turn our quarantine list into a DataFrame
    quarantine_df = pd.DataFrame(
        quarantine,
        columns=["order_id", "reason"]
    )

    print(f"Clean records: {len(clean_df)}")
    print(f"Quarantined records: {len(quarantine_df)}")

    # Return both the good data and rejected data
    return clean_df, quarantine_df