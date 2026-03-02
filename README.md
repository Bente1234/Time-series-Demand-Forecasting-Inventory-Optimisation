# Time-series-Demand-Forecasting-Inventory-Optimisation (StreamLit)
Time-series demand forecasting with exponential smoothing and inventory policy simulation under lead-time and promotion scenarios.

Interactive prototype for **time-series demand forecasting** and **inventory control** using order history data. The app supports category/product selection, Holt-style exponential smoothing forecasts, promotion uplift scenarios, and a simple reorder-policy simulation (EOQ/ROP + lead time + safety stock). This was built as a prototype for small E-commerce retailers. 

## Quant / Technical Summary

### Forecasting
- Aggregates order quantities to weekly demand.
- Fits **Exponential Smoothing (Holt trend)** to historical weekly demand.
- Produces a baseline forecast for a configurable horizon.

### Scenario Modelling (Promotions)
- Applies an uplift factor during a user-defined promotion window:
  - uplift = elasticity × discount
- Produces a “forecast with action” scenario.

### Inventory Control & Simulation
- Computes classic control quantities:
  - **EOQ** (economic order quantity)
  - **ROP** (reorder point)
  - **Safety stock** (weeks of coverage)
- Simulates inventory over time with:
  - lead-time deliveries (pipeline inventory)
  - reorder trigger when on-hand ≤ ROP
- Outputs KPIs such as number of orders and average inventory level.

## Repository Contents
- `src/app.py` — Streamlit application
- `data/EE_Orders_Demo.csv` — demo order dataset (replaceable with your own)

## How to run

1) Install dependencies:
```bash
pip install -r requirements.txt
streamlit run src/app.py
