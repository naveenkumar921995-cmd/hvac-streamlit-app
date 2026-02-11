from database import get_connection
import pandas as pd
from datetime import datetime

def check_amc_alerts():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM assets", conn)
    conn.close()

    today = datetime.today()

    alerts = []

    for _, row in df.iterrows():
        if row["amc_end"]:
            amc_date = datetime.strptime(row["amc_end"], "%Y-%m-%d")
            if (amc_date - today).days < 30:
                alerts.append(f"AMC Expiring Soon: {row['asset_name']}")

    return alerts
