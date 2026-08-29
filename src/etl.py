import os
import logging

import mysql.connector
import pandas as pd
from dotenv import load_dotenv

from data_cleaning import clean_sales_data
from data_quality import validate_sales_data


# Load database settings from .env
load_dotenv()


# Location of our CSV file
DATA_FILE = "data/sales.csv"


# Create the logs folder before creating the log file
os.makedirs("logs", exist_ok=True)


# Save every pipeline run in logs/etl.log
# New runs are added to the existing file
logging.basicConfig(
    filename="logs/etl.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def get_connection():
    # Connect to our MySQL database
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def main():

    # =========================================================
    # 1. START PIPELINE
    # =========================================================

    print("Starting sales ETL pipeline...")
    logger.info("ETL pipeline started")


    # =========================================================
    # 2. EXTRACT
    # =========================================================

    # Read the CSV file
    df = pd.read_csv(DATA_FILE)

    print(f"Raw records loaded: {len(df)}")
    logger.info(f"Raw records loaded: {len(df)}")


    # =========================================================
    # 3. CLEAN THE DATA
    # =========================================================

    # Separate good records from bad records
    clean_df, quarantine_df = clean_sales_data(df)

    logger.info(
        f"Clean records: {len(clean_df)}"
    )

    logger.info(
        f"Quarantined records: {len(quarantine_df)}"
    )


    # Save bad records if we find any
    if not quarantine_df.empty:

        quarantine_df.to_csv(
            "data/quarantine.csv",
            index=False
        )

        print("Bad records saved to logs/quarantine.csv")

        logger.warning(
            f"{len(quarantine_df)} records were quarantined"
        )

    else:

        print("No records were quarantined.")
        logger.info("No records were quarantined")


    # =========================================================
    # 4. CHECK DATA QUALITY
    # =========================================================

    # Make sure the cleaned data passes our rules
    validate_sales_data(clean_df)

    logger.info("Data-quality checks passed")


    # Only continue with validated data
    df = clean_df


    # =========================================================
    # 5. PREPARE CUSTOMER DATA
    # =========================================================

    # Get one unique record for each customer
    customers = df[
        [
            "customer_id",
            "customer_name",
            "customer_city",
        ]
    ].drop_duplicates()


    # =========================================================
    # 6. PREPARE PRODUCT DATA
    # =========================================================

    # Get one unique record for each product
    products = df[
        [
            "product_id",
            "product_name",
            "category",
            "unit_price",
        ]
    ].drop_duplicates()


    # =========================================================
    # 7. PREPARE DATE DATA
    # =========================================================

    # Convert order dates into actual dates
    dates = pd.to_datetime(
        df["order_date"]
    ).dt.date

    # Keep each date only once
    dates = pd.Series(
        dates
    ).drop_duplicates()


    # =========================================================
    # 8. CONNECT TO MYSQL
    # =========================================================

    connection = get_connection()
    cursor = connection.cursor()

    print("MySQL connection successful.")
    logger.info("MySQL connection successful")


    # =========================================================
    # 9. LOAD CUSTOMERS
    # =========================================================

    customer_sql = """
        INSERT INTO dim_customer (
            customer_id,
            customer_name,
            customer_city
        )
        VALUES (%s, %s, %s)

        ON DUPLICATE KEY UPDATE
            customer_name = VALUES(customer_name),
            customer_city = VALUES(customer_city)
    """

    for row in customers.itertuples(index=False):

        cursor.execute(
            customer_sql,
            (
                row.customer_id,
                row.customer_name,
                row.customer_city,
            )
        )

    print(f"Customers loaded: {len(customers)}")
    logger.info(f"Customers loaded: {len(customers)}")


    # =========================================================
    # 10. LOAD PRODUCTS
    # =========================================================

    product_sql = """
        INSERT INTO dim_product (
            product_id,
            product_name,
            category,
            unit_price
        )
        VALUES (%s, %s, %s, %s)

        ON DUPLICATE KEY UPDATE
            product_name = VALUES(product_name),
            category = VALUES(category),
            unit_price = VALUES(unit_price)
    """

    for row in products.itertuples(index=False):

        cursor.execute(
            product_sql,
            (
                row.product_id,
                row.product_name,
                row.category,
                row.unit_price,
            )
        )

    print(f"Products loaded: {len(products)}")
    logger.info(f"Products loaded: {len(products)}")


    # =========================================================
    # 11. LOAD DATES
    # =========================================================

    date_sql = """
        INSERT INTO dim_date (
            date_key,
            full_date,
            year,
            month,
            day
        )
        VALUES (%s, %s, %s, %s, %s)

        ON DUPLICATE KEY UPDATE
            full_date = VALUES(full_date),
            year = VALUES(year),
            month = VALUES(month),
            day = VALUES(day)
    """

    for current_date in dates:

        # Example:
        # 2026-01-07 becomes 20260107
        date_key = int(
            current_date.strftime("%Y%m%d")
        )

        cursor.execute(
            date_sql,
            (
                date_key,
                current_date,
                current_date.year,
                current_date.month,
                current_date.day,
            )
        )

    print(f"Dates loaded: {len(dates)}")
    logger.info(f"Dates loaded: {len(dates)}")


    # Save dimension changes
    connection.commit()


    # =========================================================
    # 12. GET DATABASE KEYS
    # =========================================================

    # The CSV uses customer_id.
    # MySQL uses customer_key.
    # This lookup connects the two.
    cursor.execute("""
        SELECT customer_id, customer_key
        FROM dim_customer
    """)

    customer_lookup = dict(
        cursor.fetchall()
    )


    # Do the same for products
    cursor.execute("""
        SELECT product_id, product_key
        FROM dim_product
    """)

    product_lookup = dict(
        cursor.fetchall()
    )


    # And dates
    cursor.execute("""
        SELECT full_date, date_key
        FROM dim_date
    """)

    date_lookup = dict(
        cursor.fetchall()
    )


    # =========================================================
    # 13. LOAD SALES INTO FACT TABLE
    # =========================================================

    fact_sql = """
        INSERT INTO fact_sales (
            order_id,
            date_key,
            customer_key,
            product_key,
            quantity,
            unit_price,
            sales_amount
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)

        ON DUPLICATE KEY UPDATE
            date_key = VALUES(date_key),
            customer_key = VALUES(customer_key),
            product_key = VALUES(product_key),
            quantity = VALUES(quantity),
            unit_price = VALUES(unit_price),
            sales_amount = VALUES(sales_amount)
    """


    # Process each sale
    for row in df.itertuples(index=False):

        # Convert the date into the same format
        # used by our date dimension
        order_date = pd.to_datetime(
            row.order_date
        ).date()


        # Find the MySQL keys
        customer_key = customer_lookup[
            row.customer_id
        ]

        product_key = product_lookup[
            row.product_id
        ]

        date_key = date_lookup[
            order_date
        ]


        # Calculate the total value of the sale
        sales_amount = (
            row.quantity * row.unit_price
        )


        # Insert the sale
        cursor.execute(
            fact_sql,
            (
                row.order_id,
                date_key,
                customer_key,
                product_key,
                row.quantity,
                row.unit_price,
                sales_amount,
            )
        )


    # Save the sales
    connection.commit()

    print(f"Sales loaded: {len(df)}")
    logger.info(f"Sales loaded: {len(df)}")


    # =========================================================
    # 14. CLOSE MYSQL
    # =========================================================

    cursor.close()
    connection.close()

    logger.info(
        "ETL pipeline completed successfully"
    )

    print(
        "Sales ETL pipeline completed successfully."
    )


# =============================================================
# 15. RUN THE PIPELINE AND RECORD FAILURES
# =============================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as e:

        # logger.exception() records the error message
        # AND the traceback showing where it happened
        logger.exception(
            "ETL pipeline failed"
        )

        # Show the error in the terminal too
        print(
            f"ETL pipeline failed: {e}"
        )

        # Keep the program marked as failed
        raise