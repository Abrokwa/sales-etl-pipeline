# Sales ETL Pipeline



## Summary



A sales ETL pipeline using Python, Pandas, and MySQL.



The pipeline reads raw sales data from a CSV file, cleans and validates the data, identifies invalid records, transforms the data into a simple star schema, and loads it into a MySQL data warehouse.



The warehouse contains customer, product, date, and sales fact tables, allowing SQL queries for business analysis such as monthly sales by customer.



The project also includes pipeline logging to record successful and failed executions.



## Pipeline



CSV → Python → Cleaning → Data Quality Checks → MySQL Star Schema → SQL Analysis

