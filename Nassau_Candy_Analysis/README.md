# Nassau Candy Distributor – Shipping Route Efficiency Analysis

## Project files
- `main.py`: runs the data analysis.
- `app.py`: optional Streamlit dashboard.
- `Nassau Candy Distributor.csv`: input dataset.
- `outputs/`: generated CSV summaries and charts.

## Requirements
Python 3.10 or later is recommended. Install libraries with:

```bash
pip install -r requirements.txt
```

## Run the analysis
Place the CSV file in the project folder (or update the input path in `main.py`), open a terminal in the project folder, and run:

```bash
python main.py
```

## Run the dashboard
If `app.py` is configured to read the same input/output paths, run:

```bash
python -m streamlit run app.py
```

## Expected outputs
Check the `outputs` folder for:
- `dataset_with_factory.csv`
- `factory_state_routes.csv`
- `factory_summary.csv`
- `shipping_mode_summary.csv`
- `shipping_mode_distribution.png`
- `top_10_routes.png`

## Important data-quality note
The analysis reported Order Date values from 2024–2025 and Ship Date values from 2026–2030. Verify these source dates before interpreting calculated lead times as actual delivery performance.
