import pandas as pd


def clean_sales_data(df):

    # Make a copy so the original data is not changed
    df = df.copy()

    # Store records that fail our cleaning rules
    bad_records = pd.DataFrame()


    # ---------------------------------------------------------
    # 1. Treat empty strings as missing values
    # ---------------------------------------------------------

    required_columns = [
        "order_id",
        "order_date",
        "customer_id",
        "customer_name",
        "product_id",
        "product_name",
    ]

    # Convert empty spaces such as "" into missing values
    df[required_columns] = df[required_columns].replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )

    missing_data = df[required_columns].isna().any(axis=1)

    bad_records = pd.concat(
        [bad_records, df[missing_data]]
    )

    df = df[~missing_data]


    # ---------------------------------------------------------
    # 2. Check that order dates are valid
    # ---------------------------------------------------------

    df["order_date"] = pd.to_datetime(
        df["order_date"],
        errors="coerce"
    )

    invalid_dates = df["order_date"].isna()

    bad_records = pd.concat(
        [bad_records, df[invalid_dates]]
    )

    df = df[~invalid_dates]


    # ---------------------------------------------------------
    # 3. Check quantity
    # ---------------------------------------------------------

    invalid_quantity = df["quantity"] <= 0

    bad_records = pd.concat(
        [bad_records, df[invalid_quantity]]
    )

    df = df[~invalid_quantity]


    # ---------------------------------------------------------
    # 4. Check unit price
    # ---------------------------------------------------------

    invalid_price = df["unit_price"] <= 0

    bad_records = pd.concat(
        [bad_records, df[invalid_price]]
    )

    df = df[~invalid_price]


    # ---------------------------------------------------------
    # 5. Check duplicate orders
    # ---------------------------------------------------------

    duplicate_orders = df["order_id"].duplicated(
        keep="first"
    )

    bad_records = pd.concat(
        [bad_records, df[duplicate_orders]]
    )

    df = df[~duplicate_orders]


    # ---------------------------------------------------------
    # 6. Remove duplicate records from quarantine
    # ---------------------------------------------------------

    bad_records = bad_records.drop_duplicates(
        subset=["order_id"]
    )


    # Return good data and bad data separately
    return df, bad_records