import duckdb
import pandas as pd
import re
from typing import Dict, Any, Tuple
from src.config import DB_PATH, GEMINI_API_KEY, OPENAI_API_KEY

class DatabaseAnalyticsEngine:
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        con = duckdb.connect(self.db_path)
        tables = con.execute("SHOW TABLES;").fetchall()
        con.close()
        if not tables:
            from data.database.seed_data import seed_database
            seed_database()

    def get_schema_summary(self) -> str:
        """Returns detailed database schema representation for LLM context."""
        con = duckdb.connect(self.db_path)
        tables = [t[0] for t in con.execute("SHOW TABLES;").fetchall()]
        schema_text = []
        for table in tables:
            cols = con.execute(f"DESCRIBE {table};").fetchall()
            col_desc = ", ".join([f"{col[0]} ({col[1]})" for col in cols])
            schema_text.append(f"Table: {table}\nColumns: {col_desc}")
            # Add sample rows
            sample = con.execute(f"SELECT * FROM {table} LIMIT 2;").fetchdf()
            schema_text.append(f"Sample data:\n{sample.to_string(index=False)}\n")
        con.close()
        return "\n".join(schema_text)

    def execute_query(self, sql: str) -> Tuple[pd.DataFrame, str]:
        """Executes a safe read-only SQL query and returns results as DataFrame."""
        clean_sql = sql.strip().strip("```sql").strip("```").strip()
        # Security Guardrail: Read-only operations only
        disallowed = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE"]
        for keyword in disallowed:
            if re.search(rf"\b{keyword}\b", clean_sql, re.IGNORECASE):
                raise ValueError(f"Security Alert: Disallowed mutating operation '{keyword}' detected.")

        con = duckdb.connect(self.db_path, read_only=True)
        try:
            df = con.execute(clean_sql).fetchdf()
            return df, clean_sql
        except Exception as e:
            raise RuntimeError(f"SQL Execution Error: {str(e)}\nQuery attempted:\n{clean_sql}")
        finally:
            con.close()

    def text_to_sql(self, user_question: str) -> str:
        """Translates user natural language into optimized SQL."""
        # Check if an API key is available for LLM SQL Generation
        if GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=GEMINI_API_KEY)
                prompt = f"""You are a senior decision analytics SQL expert for DuckDB.
Given the following database schema:
{self.get_schema_summary()}

Translate the user's question into a clean, single SQL query:
User Question: "{user_question}"

Return ONLY the raw SQL code without any markdown tags or conversational text.
"""
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                return response.text.strip().strip("```sql").strip("```").strip()
            except Exception as e:
                print(f"[Warning] LLM SQL generation failed: {e}. Falling back to internal engine.")

        # Robust deterministic fallback engine for common decision queries
        q = user_question.lower()
        if "europe" in q and ("drop" in q or "q3" in q or "variance" in q or "revenue" in q or "sales" in q):
            return """
            SELECT quarter, year, region, product_line, 
                   revenue_millions, target_millions, 
                   (revenue_millions - target_millions) as variance_millions,
                   customer_retention_rate
            FROM quarterly_sales 
            WHERE region = 'Europe' 
            ORDER BY year, quarter, product_line;
            """.strip()

        elif "competitor" in q or "market share" in q or "price" in q:
            return """
            SELECT year, quarter, region, company, 
                   market_share_percent, avg_treatment_price_usd 
            FROM market_share_benchmarks 
            WHERE region = 'Europe' 
            ORDER BY quarter DESC, market_share_percent DESC;
            """.strip()

        elif "north america" in q:
            return """
            SELECT quarter, year, region, product_line, revenue_millions, target_millions
            FROM quarterly_sales 
            WHERE region = 'North America'
            ORDER BY year, quarter;
            """.strip()

        else:
            return """
            SELECT region, quarter, SUM(revenue_millions) as total_revenue, 
                   SUM(target_millions) as total_target,
                   AVG(customer_retention_rate) as avg_retention
            FROM quarterly_sales 
            GROUP BY region, quarter 
            ORDER BY region, quarter;
            """.strip()

    def run_analytics_pipeline(self, user_question: str) -> Dict[str, Any]:
        """End-to-end pipeline: NL -> SQL -> Execution -> Metrics."""
        sql = self.text_to_sql(user_question)
        df, executed_sql = self.execute_query(sql)
        
        # Calculate summary metrics if revenue columns exist
        summary = {}
        if "revenue_millions" in df.columns:
            summary["total_revenue"] = round(df["revenue_millions"].sum(), 2)
            summary["record_count"] = len(df)
            if "target_millions" in df.columns:
                summary["total_target"] = round(df["target_millions"].sum(), 2)
                summary["variance"] = round(summary["total_revenue"] - summary["total_target"], 2)

        return {
            "sql": executed_sql,
            "data": df,
            "metrics": summary,
            "markdown_table": df.to_markdown(index=False)
        }
