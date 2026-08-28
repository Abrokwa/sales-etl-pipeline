# Sales ETL Pipeline



## Summary
A sales ETL pipeline that reads raw sales data from a CSV file, cleans and validates the data, identifies invalid records, transforms the data into a simple star schema, and loads it into a MySQL data warehouse.
The warehouse contains customer, product, date, and sales fact tables, allowing SQL queries for business analysis.

## Pipeline
CSV → Python → Cleaning → Data Quality Checks → MySQL Star Schema → SQL Analysis

