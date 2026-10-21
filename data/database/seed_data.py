import duckdb
import pandas as pd
import numpy as np
from pathlib import Path

DB_PATH = Path(__file__).parent / "enterprise_analytics.duckdb"

def seed_database():
    """Seeds an enterprise decision analytics database using DuckDB."""
    con = duckdb.connect(str(DB_PATH))
    
    # 1. Quarterly Regional Sales & Revenue Performance
    con.execute("DROP TABLE IF EXISTS quarterly_sales;")
    con.execute("""
    CREATE TABLE quarterly_sales (
        quarter VARCHAR,
        year INTEGER,
        region VARCHAR,
        product_line VARCHAR,
        revenue_millions DOUBLE,
        target_millions DOUBLE,
        marketing_spend_millions DOUBLE,
        sales_reps_count INTEGER,
        customer_retention_rate DOUBLE
    );
    """)
    
    # Realistic enterprise data across 2024-2025 quarters
    sales_data = [
        # Q1 2024
        ("Q1", 2024, "North America", "Oncology", 28.5, 27.0, 4.2, 45, 0.94),
        ("Q1", 2024, "North America", "Immunology", 19.2, 20.0, 3.1, 32, 0.91),
        ("Q1", 2024, "Europe", "Oncology", 14.8, 15.0, 2.8, 28, 0.89),
        ("Q1", 2024, "Europe", "Immunology", 12.1, 12.0, 2.2, 22, 0.88),
        ("Q1", 2024, "APAC", "Oncology", 9.4, 9.0, 1.8, 18, 0.92),
        ("Q1", 2024, "APAC", "Immunology", 8.1, 8.0, 1.4, 15, 0.90),
        
        # Q2 2024
        ("Q2", 2024, "North America", "Oncology", 31.0, 29.5, 4.5, 46, 0.95),
        ("Q2", 2024, "North America", "Immunology", 20.8, 21.0, 3.3, 33, 0.92),
        ("Q2", 2024, "Europe", "Oncology", 15.2, 15.5, 2.9, 29, 0.89),
        ("Q2", 2024, "Europe", "Immunology", 12.5, 12.5, 2.3, 23, 0.87),
        ("Q2", 2024, "APAC", "Oncology", 10.1, 9.8, 2.0, 19, 0.93),
        ("Q2", 2024, "APAC", "Immunology", 8.7, 8.5, 1.5, 16, 0.91),

        # Q3 2024 (Crucial Quarter: Notice the European drop!)
        ("Q3", 2024, "North America", "Oncology", 33.2, 31.0, 4.8, 48, 0.95),
        ("Q3", 2024, "North America", "Immunology", 22.0, 22.5, 3.5, 34, 0.90),
        ("Q3", 2024, "Europe", "Oncology", 11.8, 16.0, 2.5, 27, 0.78), # Drop from 15.2 -> 11.8 (-22.4%)
        ("Q3", 2024, "Europe", "Immunology", 9.6, 13.0, 2.0, 21, 0.76),  # Drop from 12.5 -> 9.6 (-23.2%)
        ("Q3", 2024, "APAC", "Oncology", 11.2, 10.5, 2.2, 20, 0.94),
        ("Q3", 2024, "APAC", "Immunology", 9.3, 9.0, 1.6, 17, 0.92),

        # Q4 2024
        ("Q4", 2024, "North America", "Oncology", 35.8, 33.0, 5.2, 50, 0.96),
        ("Q4", 2024, "North America", "Immunology", 23.5, 23.0, 3.7, 35, 0.91),
        ("Q4", 2024, "Europe", "Oncology", 13.1, 16.5, 2.9, 28, 0.82),
        ("Q4", 2024, "Europe", "Immunology", 10.8, 13.5, 2.4, 23, 0.81),
        ("Q4", 2024, "APAC", "Oncology", 12.5, 11.5, 2.5, 22, 0.95),
        ("Q4", 2024, "APAC", "Immunology", 10.2, 9.8, 1.8, 18, 0.93)
    ]
    
    con.executemany("""
    INSERT INTO quarterly_sales VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, sales_data)
    
    # 2. Competitor Pricing & Market Share Table
    con.execute("DROP TABLE IF EXISTS market_share_benchmarks;")
    con.execute("""
    CREATE TABLE market_share_benchmarks (
        year INTEGER,
        quarter VARCHAR,
        region VARCHAR,
        company VARCHAR,
        market_share_percent DOUBLE,
        avg_treatment_price_usd DOUBLE
    );
    """)
    
    benchmark_data = [
        (2024, "Q2", "Europe", "Our Company", 34.5, 4800.0),
        (2024, "Q2", "Europe", "BioPharma Corp (Competitor A)", 28.2, 5100.0),
        (2024, "Q2", "Europe", "Vanguard Therapeutics (Competitor B)", 21.0, 4950.0),
        
        (2024, "Q3", "Europe", "Our Company", 26.8, 4800.0), # Dropped share by 7.7%
        (2024, "Q3", "Europe", "BioPharma Corp (Competitor A)", 37.4, 4100.0), # Slashed price by 20%, captured share
        (2024, "Q3", "Europe", "Vanguard Therapeutics (Competitor B)", 20.8, 4900.0),
    ]
    con.executemany("INSERT INTO market_share_benchmarks VALUES (?, ?, ?, ?, ?, ?);", benchmark_data)

    con.close()
    print(f"Database successfully created and seeded at: {DB_PATH}")

if __name__ == "__main__":
    seed_database()
