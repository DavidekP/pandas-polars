import polars as pl

def main():
    print("=== POLARS ŘEŠENÍ ===\n")
    
    # --- Úloha 1: Načtení dat ---
    # infer_schema_length=10000 zaručí, že polars správně odhadne typy i přes úvodní chyby
    df = pl.read_csv("physics_solar_panel_lab_dataset.csv", infer_schema_length=10000)
    print("Prvních 5 řádků:\n", df.head())
    print("\nSchéma datasetu:\n", df.schema)
    print(f"\nDataset má {df.height} řádků a {df.width} sloupců.\n")

    # --- Úloha 2: Čištění dat ---
    # Převod na čísla a datum pomocí strict=False (chyby se převedou na null)
    df = df.with_columns([
        pl.col('voltage_v').cast(pl.Float64, strict=False),
        pl.col('current_a').cast(pl.Float64, strict=False),
        pl.col('power_w').cast(pl.Float64, strict=False),
        pl.col('light_intensity_lux').cast(pl.Float64, strict=False),
        pl.col('angle_deg').cast(pl.Float64, strict=False),
        pl.col('timestamp').str.strptime(pl.Datetime, format="%Y-%m-%d %H:%M:%S", strict=False)
    ])

    # Filtrování logických nesmyslů
    df = df.filter(
        (pl.col('voltage_v') >= 0) & 
        (pl.col('current_a') >= 0) & 
        (pl.col('power_w') >= 0) & 
        (pl.col('light_intensity_lux') >= 0) &
        (pl.col('angle_deg') >= 0) & 
        (pl.col('angle_deg') <= 90)
    )

    # Odstranění null (NaN) hodnot a duplicit
    df = df.drop_nulls().unique()

    # Sjednocení textu
    df = df.with_columns([
        pl.col('weather').str.strip_chars().str.to_lowercase().str.replace('suny', 'sunny'),
        pl.col('room').str.strip_chars()
    ])
    
    print(f"Po vyčištění zbylo {df.height} řádků.\n")

    # --- Úloha 3: Vytvoření nových veličin ---
    df = df.with_columns(
        (pl.col('voltage_v') * pl.col('current_a')).alias('power_calc')
    )
    df = df.with_columns(
        (pl.col('power_w') - pl.col('power_calc')).abs().alias('power_diff')
    )
    print("Průměrný rozdíl výkonu (W):", df.select(pl.col('power_diff').mean()).item())

    # --- Úloha 4: Vliv úhlu ---
    angle_analysis = df.group_by('angle_deg').agg(pl.col('power_w').mean()).sort('power_w', descending=True)
    print("\nPrůměrný výkon podle úhlu:\n", angle_analysis)

    # --- Úloha 5: Vliv intenzity světla ---
    corr = df.select(pl.corr('light_intensity_lux', 'power_w')).item()
    print(f"\nKorelace mezi intenzitou a výkonem: {corr:.4f}")

    # --- Úloha 6: Porovnání prostředí ---
    env_analysis = df.group_by('weather').agg(pl.col('power_w').mean()).sort('power_w', descending=True)
    print("\nPrůměrný výkon podle počasí:\n", env_analysis)

    # --- Úloha 7: Nejlepší podmínky ---
    best_row = df.filter(pl.col('power_w') == pl.col('power_w').max())
    print("\nNejlepší podmínky měření:\n", best_row.select(['panel_id', 'room', 'weather', 'angle_deg', 'power_w']))

    # --- Úloha 8: Detekce anomálií ---
    q99 = df.select(pl.col('power_w').quantile(0.99)).item()
    anomalies = df.filter(pl.col('power_w') > q99)
    print(f"\nPočet měření s extrémním výkonem (> {q99:.2f} W): {anomalies.height}")

    # --- Úloha 9: Vlastní analýza (Efektivita panelů) ---
    panel_eff = df.group_by('panel_id').agg([
        pl.col('power_w').mean().alias('avg_power'),
        pl.col('power_w').max().alias('max_power')
    ]).sort('avg_power', descending=True)
    print("\nEfektivita panelů:\n", panel_eff)

if __name__ == "__main__":
    main()
