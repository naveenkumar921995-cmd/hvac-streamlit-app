from database import get_connection
import pandas as pd

def calculate_kpi():
    conn = get_connection()

    assets = pd.read_sql("SELECT * FROM assets", conn)
    energy = pd.read_sql("SELECT * FROM energy", conn)

    conn.close()

    total_assets = len(assets)
    avg_health = assets["health"].mean() if total_assets > 0 else 0
    total_energy = energy["kwh"].sum() if len(energy) > 0 else 0

    score = (avg_health * 0.6) + (100 - total_energy * 0.01)

    return {
        "Total Assets": total_assets,
        "Average Health": round(avg_health, 2),
        "Total Energy": round(total_energy, 2),
        "KPI Score": round(score, 2)
    }
