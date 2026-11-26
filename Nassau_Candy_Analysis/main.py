
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# 1. PROJECT SETUP
# ==========================================

print("=" * 55)
print("NASSAU CANDY SHIPPING ROUTE ANALYSIS")
print("=" * 55)

# Create output folder
output_folder = Path("outputs")
output_folder.mkdir(exist_ok=True)

# ==========================================
# 2. LOAD DATASET
# ==========================================

file_path = "Nassau Candy Distributor.csv"

try:
    df = pd.read_csv(file_path)
    print("\nDataset loaded successfully!")
    print("Total records:", len(df))
    print("Total columns:", len(df.columns))

except FileNotFoundError:
    print("ERROR: CSV file not found.")
    print("Place the CSV file in the same folder as main.py.")
    raise SystemExit

# ==========================================
# 3. DATASET OVERVIEW
# ==========================================

print("\nDATASET SHAPE")
print(df.shape)

print("\nCOLUMN NAMES")
print(df.columns.tolist())

print("\nMISSING VALUES")
print(df.isnull().sum())

# ==========================================
# 4. CONVERT DATE COLUMNS
# ==========================================

df["Order Date"] = pd.to_datetime(
    df["Order Date"],
    dayfirst=True,
    errors="coerce"
)

df["Ship Date"] = pd.to_datetime(
    df["Ship Date"],
    dayfirst=True,
    errors="coerce"
)

# Calculate lead time for investigation.
# The dates have an unresolved inconsistency,
# so these values are NOT treated as valid
# shipping-performance measurements yet.

df["Lead Time"] = (
    df["Ship Date"] - df["Order Date"]
).dt.days

print("\nDATE QUALITY CHECK")
print("Order date range:",
      df["Order Date"].min(), "to",
      df["Order Date"].max())

print("Ship date range:",
      df["Ship Date"].min(), "to",
      df["Ship Date"].max())

print("\nLead time summary (provisional)")
print(df["Lead Time"].describe())

# ==========================================
# 5. MAP PRODUCTS TO FACTORIES
# ==========================================

factory_mapping = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory"
}

df["Factory"] = df["Product Name"].map(factory_mapping)

unmapped = df[df["Factory"].isna()]["Product Name"].unique()

print("\nFACTORY MAPPING CHECK")
print("Mapped records:", df["Factory"].notna().sum())
print("Unmapped records:", df["Factory"].isna().sum())

if len(unmapped) > 0:
    print("Products requiring mapping:")
    print(unmapped)

# ==========================================
# 6. FACTORY SUMMARY
# ==========================================

factory_summary = (
    df.groupby("Factory", dropna=False)
    .agg(
        Product_Records=("Row ID", "count"),
        Unique_Orders=("Order ID", "nunique"),
        Unique_Products=("Product Name", "nunique")
    )
    .reset_index()
    .sort_values("Product_Records", ascending=False)
)

print("\nRECORDS BY FACTORY")
print(factory_summary.to_string(index=False))

factory_summary.to_csv(
    output_folder / "factory_summary.csv",
    index=False
)

# ==========================================
# 7. FACTORY-TO-STATE ROUTE ANALYSIS
# ==========================================

routes = (
    df.groupby(["Factory", "State/Province"], dropna=False)
    .agg(
        Product_Records=("Row ID", "count"),
        Unique_Orders=("Order ID", "nunique")
    )
    .reset_index()
    .sort_values("Unique_Orders", ascending=False)
)

print("\nTOP 10 FACTORY-TO-STATE ROUTES")
print(routes.head(10).to_string(index=False))

routes.to_csv(
    output_folder / "factory_state_routes.csv",
    index=False
)

# ==========================================
# 8. SHIPPING MODE ANALYSIS
# ==========================================

ship_mode_summary = (
    df.groupby("Ship Mode")
    .agg(
        Product_Records=("Row ID", "count"),
        Unique_Orders=("Order ID", "nunique")
    )
    .reset_index()
    .sort_values("Product_Records", ascending=False)
)

print("\nSHIPPING METHOD DISTRIBUTION")
print(ship_mode_summary.to_string(index=False))

ship_mode_summary.to_csv(
    output_folder / "shipping_mode_summary.csv",
    index=False
)

# ==========================================
# 9. CHART 1: TOP 10 ROUTES
# ==========================================

top_routes = routes.dropna(
    subset=["Factory", "State/Province"]
).head(10).copy()

top_routes["Route"] = (
    top_routes["Factory"] + " -> " +
    top_routes["State/Province"].astype(str)
)

plt.figure(figsize=(12, 7))

plt.barh(
    top_routes["Route"].iloc[::-1],
    top_routes["Unique_Orders"].iloc[::-1]
)

plt.xlabel("Unique Order IDs")
plt.ylabel("Factory -> Customer State")
plt.title("Top 10 Factory-to-State Routes by Order Count")
plt.tight_layout()

plt.savefig(
    output_folder / "top_10_routes.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 10. CHART 2: SHIPPING MODE DISTRIBUTION
# ==========================================

ship_counts = df["Ship Mode"].value_counts()

plt.figure(figsize=(9, 5))

plt.bar(
    ship_counts.index,
    ship_counts.values
)

plt.xlabel("Shipping Mode")
plt.ylabel("Number of Product Records")
plt.title("Shipping Mode Distribution")
plt.xticks(rotation=15)
plt.tight_layout()

plt.savefig(
    output_folder / "shipping_mode_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 11. SAVE ANALYSIS DATA
# ==========================================

df.to_csv(
    output_folder / "dataset_with_factory.csv",
    index=False
)

print("\n" + "=" * 55)
print("ANALYSIS COMPLETED SUCCESSFULLY!")
print("=" * 55)

print("\nFiles saved in the outputs folder:")
for file in sorted(output_folder.iterdir()):
    print("-", file.name)

print("\nNote:")
print(
    "Shipping lead times remain provisional because "
    "the source dates need validation."
)
