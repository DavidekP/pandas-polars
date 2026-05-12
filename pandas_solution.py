import pandas as pd
import numpy as np

CSV_PATH = "physics_solar_panel_lab_dataset.csv"

# -----------------------------
# Pomocné funkce
# -----------------------------
def to_numeric_series(s: pd.Series) -> pd.Series:
    """Převede text na čísla. Řeší desetinnou čárku a bordel v datech."""
    return pd.to_numeric(
        s.astype(str)
         .str.replace(",", ".", regex=False)
         .str.strip(),
        errors="coerce"
    )

def normalize_text(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
         .str.strip()
         .str.replace(r"\s+", " ", regex=True)
         .str.lower()
    )

def clip_invalid(df: pd.DataFrame) -> pd.DataFrame:
    """Základní fyzikální sanity checks (záporné/nesmyslné hodnoty)."""
    # úhel: obvykle 0–90 (pokud máte i záporné úhly kvůli orientaci, uprav)
    if "angle_deg" in df.columns:
        df.loc[(df["angle_deg"] < 0) | (df["angle_deg"] > 90), "angle_deg"] = np.nan

    # světlo lux: nemůže být záporné
    if "light_intensity_lux" in df.columns:
        df.loc[df["light_intensity_lux"] < 0, "light_intensity_lux"] = np.nan

    # napětí/proud: běžně nezáporné (pokud máte polaritu, tak to může být jinak)
    for col in ["voltage_v", "current_a", "power_w"]:
        if col in df.columns:
            df.loc[df[col] < 0, col] = np.nan

    return df

# -----------------------------
# 1) Načtení + první analýza
# -----------------------------
df_raw = pd.read_csv(CSV_PATH)
print("=== RAW HEAD ===")
print(df_raw.head())
print("\n=== RAW INFO ===")
print(df_raw.info())
print("\nRAW shape:", df_raw.shape)

# Doporučeno: sjednotit názvy sloupců (ať se s tím líp pracuje)
df = df_raw.copy()
df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
)

print("\n=== COLUMNS ===")
print(df.columns.tolist())

# -----------------------------
# 2) Čištění dat
# -----------------------------
# Pokud tvůj dataset používá jiné názvy, uprav jen mapování tady:
# (když už sloupce sedí, mapování nech prázdné)
rename_map = {
    # "timestamp": "timestamp",
    # "angle": "angle_deg",
    # "lux": "light_intensity_lux",
    # "voltage": "voltage_v",
    # "current": "current_a",
    # "power": "power_w",
    # "room": "room",
    # "weather": "weather",
    # "panel": "panel_id",
}
df = df.rename(columns=rename_map)

# Datové typy: timestamp
if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

# Datové typy: čísla
for col in ["voltage_v", "current_a", "power_w", "light_intensity_lux", "angle_deg", "temperature_c", "distance_cm"]:
    if col in df.columns:
        df[col] = to_numeric_series(df[col])

# Textové hodnoty: environment/room/weather
if "weather" in df.columns:
    w = normalize_text(df["weather"])
    # sjednocení častých překlepů
    w = w.replace({
        "suny": "sunny",
        "sun": "sunny",
        "sunny ": "sunny",
        "cloudy ": "cloudy",
        "clody": "cloudy",
        "over cast": "overcast",
    })
    df["weather"] = w

if "room" in df.columns:
    r = df["room"].astype(str).str.strip()
    # příklad sjednocení "Roof " -> "Roof"
    df["room"] = r

# Nesmyslné / záporné hodnoty
df = clip_invalid(df)

# Duplicity:
# ideálně dle timestamp + panel + úhel + prostředí; když ty sloupce nemáš, dej drop_duplicates() bez subset
subset = [c for c in ["timestamp", "panel_id", "angle_deg", "room", "weather"] if c in df.columns]
if subset:
    df = df.drop_duplicates(subset=subset, keep="first")
else:
    df = df.drop_duplicates(keep="first")

# Chybějící hodnoty:
# Jednoduchá strategie:
# - když chybí voltage/current/power -> ten řádek je často nepoužitelný pro výkon
# - u lux/angle lze někdy dopočítat/odhadnout, ale pro školní úkol stačí buď drop nebo imputace mediánem
critical = [c for c in ["voltage_v", "current_a"] if c in df.columns]
if critical:
    df = df.dropna(subset=critical)

# Ne-kritické: doplň mediánem (pokud existují)
for col in ["light_intensity_lux", "angle_deg", "temperature_c"]:
    if col in df.columns:
        df[col] = df[col].fillna(df[col].median())

print("\nCLEAN shape:", df.shape)
print("\nMissing values (top):")
print(df.isna().sum().sort_values(ascending=False).head(15))

# -----------------------------
# 3) Nové veličiny: power_calc + porovnání
# -----------------------------
if all(c in df.columns for c in ["voltage_v", "current_a"]):
    df["power_calc"] = df["voltage_v"] * df["current_a"]

if "power_w" in df.columns and "power_calc" in df.columns:
    df["power_diff"] = df["power_w"] - df["power_calc"]
    df["power_diff_abs"] = df["power_diff"].abs()

    print("\n=== POWER CHECK ===")
    print("Mean abs diff:", df["power_diff_abs"].mean())
    print("Median abs diff:", df["power_diff_abs"].median())
    # řádky s největším rozdílem
    print("\nTop 10 mismatches:")
    print(df.sort_values("power_diff_abs", ascending=False).head(10)[
        [c for c in ["timestamp","voltage_v","current_a","power_w","power_calc","power_diff"] if c in df.columns]
    ])

# Pokud power_w nemáš, použij power_calc jako power
if "power_w" not in df.columns and "power_calc" in df.columns:
    df["power_w"] = df["power_calc"]

# -----------------------------
# 4) Vliv úhlu
# -----------------------------
if "angle_deg" in df.columns and "power_w" in df.columns:
    angle_summary = (
        df.groupby("angle_deg", as_index=False)["power_w"]
          .mean()
          .rename(columns={"power_w": "power_mean_w"})
          .sort_values("angle_deg")
    )
    print("\n=== POWER vs ANGLE (mean) ===")
    print(angle_summary.head(20))
    best_angle_row = angle_summary.sort_values("power_mean_w", ascending=False).head(1)
    print("\nBest angle (by mean):")
    print(best_angle_row)

# -----------------------------
# 5) Vliv intenzity světla (lux)
# -----------------------------
if "light_intensity_lux" in df.columns and "power_w" in df.columns:
    corr = df["light_intensity_lux"].corr(df["power_w"])
    print("\n=== CORRELATION (lux vs power) ===")
    print("corr:", corr)

# -----------------------------
# 6) Porovnání prostředí (indoor vs outdoor apod.)
# -----------------------------
# Může být "room" (Lab/Roof), "environment", apod. – použij co máš.
env_col = None
for candidate in ["room", "environment", "location"]:
    if candidate in df.columns:
        env_col = candidate
        break

if env_col and "power_w" in df.columns:
    env_summary = df.groupby(env_col, as_index=False)["power_w"].agg(["mean", "median", "count"]).reset_index()
    print(f"\n=== POWER by {env_col} ===")
    print(env_summary.sort_values("mean", ascending=False))

# -----------------------------
# 7) Nejlepší podmínky (kombinace)
# -----------------------------
group_cols = [c for c in ["panel_id", "angle_deg", env_col, "weather"] if c and c in df.columns]
if group_cols and "power_w" in df.columns:
    best_combo = (
        df.groupby(group_cols, as_index=False)["power_w"].mean()
          .sort_values("power_w", ascending=False)
          .head(10)
    )
    print("\n=== TOP 10 combos (mean power) ===")
    print(best_combo)

# -----------------------------
# 8) Anomálie (extrémy)
# -----------------------------
if "power_w" in df.columns:
    q1, q3 = df["power_w"].quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    anomalies_power = df[(df["power_w"] < lo) | (df["power_w"] > hi)]
    print("\n=== ANOMALIES: POWER (IQR) ===")
    print("count:", len(anomalies_power))
    print(anomalies_power.head(10)[[c for c in ["timestamp","power_w","angle_deg","light_intensity_lux", env_col] if c in anomalies_power.columns]])

if "light_intensity_lux" in df.columns:
    q1, q3 = df["light_intensity_lux"].quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    anomalies_lux = df[(df["light_intensity_lux"] < lo) | (df["light_intensity_lux"] > hi)]
    print("\n=== ANOMALIES: LUX (IQR) ===")
    print("count:", len(anomalies_lux))
    print(anomalies_lux.head(10)[[c for c in ["timestamp","light_intensity_lux","power_w","angle_deg", env_col] if c in anomalies_lux.columns]])

# -----------------------------
# 9) Vlastní analýza (příklad): vliv teploty na výkon
# (splňuje 2+ pandas operace: filter + groupby/agg)
# -----------------------------
if "temperature_c" in df.columns and "power_w" in df.columns:
    df_temp = df.dropna(subset=["temperature_c", "power_w"]).copy()
    # binning teploty
    df_temp["temp_bin"] = pd.cut(df_temp["temperature_c"], bins=5)
    temp_summary = df_temp.groupby("temp_bin", as_index=False)["power_w"].mean()
    print("\n=== CUSTOM: POWER by temperature bins ===")
    print(temp_summary)

# Ulož si vyčištěná data (hodí se do odevzdání)
df.to_csv("physics_solar_panel_lab_dataset_clean.csv", index=False)
print("\nSaved: physics_solar_panel_lab_dataset_clean.csv")
