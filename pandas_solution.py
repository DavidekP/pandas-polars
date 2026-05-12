import pandas as pd
import numpy as np

def main():
    print("=== PANDAS ŘEŠENÍ ===\n")
    
    # --- Úloha 1: Načtení dat ---
    df = pd.read_csv("physics_solar_panel_lab_dataset.csv")
    print("Prvních 5 řádků:\n", df.head())
    print("\nInformace o datasetu:")
    df.info()
    print(f"\nDataset má {df.shape[0]} řádků a {df.shape[1]} sloupců.\n")

    # --- Úloha 2: Čištění dat ---
    # Převod na číselné typy (chybné hodnoty se změní na NaN)
    num_cols = ['voltage_v', 'current_a', 'power_w', 'angle_deg', 'light_intensity_lux']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Odstranění nesmyslných hodnot (záporné hodnoty, úhel mimo 0-90)
    df = df[
        (df['voltage_v'] >= 0) & 
        (df['current_a'] >= 0) & 
        (df['power_w'] >= 0) & 
        (df['light_intensity_lux'] >= 0) &
        (df['angle_deg'] >= 0) & 
        (df['angle_deg'] <= 90)
    ]

    # Odstranění chybějících hodnot a duplicit
    df = df.dropna().drop_duplicates()

    # Sjednocení textových hodnot
    df['weather'] = df['weather'].str.strip().str.lower().str.replace('suny', 'sunny')
    df['room'] = df['room'].str.strip()
    print(f"Po vyčištění zbylo {df.shape[0]} řádků.\n")

    # --- Úloha 3: Vytvoření nových veličin ---
    df['power_calc'] = df['voltage_v'] * df['current_a']
    df['power_diff'] = abs(df['power_w'] - df['power_calc'])
    print("Průměrný rozdíl mezi power_w a power_calc (W):", df['power_diff'].mean())

    # --- Úloha 4: Vliv úhlu ---
    angle_analysis = df.groupby('angle_deg')['power_w'].mean().reset_index()
    print("\nPrůměrný výkon podle úhlu:\n", angle_analysis.sort_values(by='power_w', ascending=False))

    # --- Úloha 5: Vliv intenzity světla ---
    corr = df['light_intensity_lux'].corr(df['power_w'])
    print(f"\nKorelace mezi intenzitou a výkonem: {corr:.4f}")

    # --- Úloha 6: Porovnání prostředí ---
    env_analysis = df.groupby('weather')['power_w'].mean().reset_index()
    print("\nPrůměrný výkon podle počasí/prostředí:\n", env_analysis)

    # --- Úloha 7: Nejlepší podmínky ---
    best_idx = df['power_w'].idxmax()
    best_conditions = df.loc[best_idx, ['panel_id', 'room', 'weather', 'angle_deg', 'power_w']]
    print("\nNejlepší podmínky měření:\n", best_conditions)

    # --- Úloha 8: Detekce anomálií ---
    q99 = df['power_w'].quantile(0.99)
    anomalies = df[df['power_w'] > q99]
    print(f"\nPočet měření s extrémním výkonem (> {q99:.2f} W): {len(anomalies)}")

    # --- Úloha 9: Vlastní analýza (Efektivita panelů) ---
    panel_eff = df.groupby('panel_id').agg(
        avg_power=('power_w', 'mean'),
        max_power=('power_w', 'max')
    ).sort_values('avg_power', ascending=False)
    print("\nEfektivita panelů:\n", panel_eff)

if __name__ == "__main__":
    main()
