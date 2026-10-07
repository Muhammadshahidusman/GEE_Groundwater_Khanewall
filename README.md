# Groundwater Potential Zone Mapping: Khanewal, Punjab (AHP)

Delineating **Groundwater Potential Zones (GWPZ)** for Khanewal District, Punjab, Pakistan, by combining seven thematic layers with the **Analytic Hierarchy Process (AHP)**, a multi-criteria decision-making method (Saaty, 1980).

## Thematic factors and AHP weights

| Rank | Factor | Weight |
|---|---|---|
| 1 | Geology (lithology) | 40.55 % |
| 2 | Rainfall (mm/year) | 21.47 % |
| 3 | Soil type (texture / permeability) | 14.92 % |
| 4 | Lineament density (km/km²) | 10.34 % |
| 5 | Land use / land cover | 7.28 % |
| 6 | Drainage density (km/km²) | 2.72 % |
| 7 | Slope (degrees) | 2.72 % |

**Consistency check:** λmax = 7.457, CI = 0.076, RI = 1.32, **CR = 0.058**. A CR below 0.10 means the pairwise judgements are consistent.

Each factor is split into five sub-classes rated 1 (very poor) to 5 (very good) for groundwater potential. The final map is the weighted overlay:

```
GWPZ = Σ (weight_i × rating_i)
```

## Workflow

1. Prepare the thematic layers (slope and drainage from a DEM, rainfall, geology, soil, lineaments, LULC)
2. Build the 7 × 7 pairwise comparison matrix on Saaty's 1–9 scale
3. Normalise the matrix, then derive the weights and check consistency (CR)
4. Reclassify each layer into sub-class ratings
5. Run a weighted overlay to get the GWPZ index, then classify it into zones

## Repository structure

| File | Purpose |
|---|---|
| `AHP1.py` | Python AHP engine: pairwise matrix, weights, λmax, CI and CR |
| `AHP.py` | Interactive React (JSX) explainer of the AHP method and weights |
| `pyproject.toml`, `uv.lock` | Environment (managed with `uv`) |

> Note: `AHP.py` is a React component despite its `.py` extension. Rename it to `AHP_dashboard.jsx` for clarity.

## Run it yourself

```bash
uv sync
uv run python AHP1.py
```

## Tools

Python · NumPy · Google Earth Engine · React · AHP / MCDM

## Author

**Muhammad Shahid Usman**, Geospatial Data Analyst & Spatial Data Scientist
[Portfolio](https://muhammadshahidusman.github.io/) · [GitHub](https://github.com/Muhammadshahidusman)
