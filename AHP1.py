"""
=============================================================================
  GROUNDWATER POTENTIAL ZONE MAPPING
  Analytic Hierarchy Process (AHP) - 7 Thematic Factor Analysis
  Multi-Criteria Decision Making (MCDM)
  Reference: Saaty, T.L. (1980)
=============================================================================
"""

import numpy as np

# ─── FACTORS ──────────────────────────────────────────────────────────────────
FACTOR_IDS   = ["SLP",  "DD",   "LD",   "LULC", "RAIN", "GEO",  "SOIL"]
FACTOR_NAMES = [
    "Slope (degrees)",
    "Drainage Density (km/km2)",
    "Lineament Density (km/km2)",
    "LULC (Land Use/Cover)",
    "Rainfall (mm/year)",
    "Geology (Lithology)",
    "Soil Type (Texture/Permeability)",
]

# ─── PAIRWISE COMPARISON MATRIX ───────────────────────────────────────────────
# Order: SLP, DD, LD, LULC, RAIN, GEO, SOIL
RAW_MATRIX = np.array([
    [1,    1,    1/5,  1/4,  1/7,  1/9,  1/6],  # SLP
    [1,    1,    1/5,  1/4,  1/7,  1/9,  1/6],  # DD
    [5,    5,    1,    2,    1/3,  1/5,  1/2],  # LD
    [4,    4,    1/2,  1,    1/4,  1/6,  1/3],  # LULC
    [7,    7,    3,    4,    1,    1/3,  2  ],  # RAIN
    [9,    9,    5,    6,    3,    1,    4  ],  # GEO
    [6,    6,    2,    3,    1/2,  1/4,  1  ],  # SOIL
])

# ─── SUB-CRITERIA RATINGS ─────────────────────────────────────────────────────
SUB_CRITERIA = {
    "SLP": [
        ("> 30 deg",   "Very Steep", 1, "Very Poor",  "High runoff, minimal infiltration"),
        ("20-30 deg",  "Steep",      2, "Poor",       "Significant runoff, low recharge"),
        ("10-20 deg",  "Moderate",   3, "Moderate",   "Balanced runoff/infiltration"),
        ("5-10 deg",   "Gentle",     4, "Good",       "Favours infiltration over runoff"),
        ("< 5 deg",    "Flat",       5, "Very Good",  "Maximum infiltration & recharge"),
    ],
    "DD": [
        ("> 4.0",    "Very High", 1, "Very Poor",  "High surface drainage, less groundwater"),
        ("3.0-4.0",  "High",      2, "Poor",       "Increased runoff, less percolation"),
        ("2.0-3.0",  "Moderate",  3, "Moderate",   "Intermediate recharge"),
        ("1.0-2.0",  "Low",       4, "Good",       "More percolation, less runoff"),
        ("< 1.0",    "Very Low",  5, "Very Good",  "Excellent groundwater recharge zone"),
    ],
    "LD": [
        ("< 0.5",    "Very Low",  1, "Very Poor",  "Minimal fractures, poor conductivity"),
        ("0.5-1.0",  "Low",       2, "Poor",       "Limited structural conduits"),
        ("1.0-2.0",  "Moderate",  3, "Moderate",   "Some fracture-controlled flow"),
        ("2.0-3.0",  "High",      4, "Good",       "Good fracture network, high recharge"),
        ("> 3.0",    "Very High", 5, "Very Good",  "Dense fractures, excellent conduit"),
    ],
    "LULC": [
        ("Urban/Built-up",       "Impervious", 1, "Very Poor",  "Impervious surfaces block recharge"),
        ("Barren/Rocky",         "Barren",     2, "Poor",       "Low vegetation, high runoff"),
        ("Scrubland",            "Scrubland",  3, "Moderate",   "Moderate infiltration capacity"),
        ("Agricultural",         "Agri",       4, "Good",       "Tilled soil enhances percolation"),
        ("Dense Forest/Wetland", "Forest",     5, "Very Good",  "High infiltration & moisture retention"),
    ],
    "RAIN": [
        ("< 400 mm",    "Very Low",  1, "Very Poor",  "Insufficient recharge source"),
        ("400-600 mm",  "Low",       2, "Poor",       "Limited annual recharge"),
        ("600-800 mm",  "Moderate",  3, "Moderate",   "Adequate seasonal recharge"),
        ("800-1200 mm", "High",      4, "Good",       "Good recharge potential"),
        ("> 1200 mm",   "Very High", 5, "Very Good",  "Excellent primary recharge source"),
    ],
    "GEO": [
        ("Massive Igneous/Metamorphic", "Massive",   1, "Very Poor",  "Impermeable; negligible groundwater"),
        ("Shale/Slate",                 "Shale",     2, "Poor",       "Very low permeability"),
        ("Sandstone/Weathered Granite", "Sandstone", 3, "Moderate",   "Secondary porosity, moderate yield"),
        ("Limestone/Karst",             "Karst",     4, "Good",       "Solution cavities, high storage"),
        ("Alluvium/Unconsolidated",     "Alluvium",  5, "Very Good",  "Highest porosity & permeability"),
    ],
    "SOIL": [
        ("Clay",         "Clay",       1, "Very Poor",  "Near-zero infiltration capacity"),
        ("Clay Loam",    "Clay Loam",  2, "Poor",       "Very slow percolation"),
        ("Loam",         "Loam",       3, "Moderate",   "Moderate water retention & flow"),
        ("Sandy Loam",   "Sandy Loam", 4, "Good",       "Good drainage & infiltration"),
        ("Sandy/Gravel", "Sandy",      5, "Very Good",  "Excellent percolation & recharge"),
    ],
}

# ─── RI TABLE (Saaty, 1980) ───────────────────────────────────────────────────
RI_TABLE = {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def separator(char="=", width=78):
    print(char * width)

def header(title):
    separator()
    print(f"  {title}")
    separator()

def section(title):
    print()
    print(f"  {'─' * 74}")
    print(f"  {title}")
    print(f"  {'─' * 74}")

def fmt_frac(v):
    """Format a float as a fraction string where applicable."""
    fracs = {round(1/9, 6): "1/9", round(1/7, 6): "1/7", round(1/6, 6): "1/6",
             round(1/5, 6): "1/5", round(1/4, 6): "1/4", round(1/3, 6): "1/3",
             round(1/2, 6): "1/2", 1.0: "1",   2.0: "2",   3.0: "3",
             4.0: "4",  5.0: "5",   6.0: "6",   7.0: "7",   8.0: "8",   9.0: "9"}
    key = round(v, 6)
    return fracs.get(key, f"{v:.3f}")

# ─── STEP 1: PRINT RAW MATRIX ─────────────────────────────────────────────────
def print_raw_matrix():
    section("STEP 1 | PAIRWISE COMPARISON MATRIX (A)  [7 x 7]")
    short = FACTOR_IDS
    col_w = 8
    header_row = f"  {'Factor':<22}" + "".join(f"{s:>{col_w}}" for s in short)
    print(header_row)
    print("  " + "-" * (22 + col_w * 7))
    col_sums = RAW_MATRIX.sum(axis=0)
    for i, row in enumerate(RAW_MATRIX):
        vals = "".join(f"{fmt_frac(v):>{col_w}}" for v in row)
        print(f"  {FACTOR_IDS[i]:<6} {FACTOR_NAMES[i][:14]:<16}{vals}")
    print("  " + "-" * (22 + col_w * 7))
    col_sum_row = "".join(f"{s:>{col_w}.4f}" for s in col_sums)
    print(f"  {'Col Sum':<22}{col_sum_row}")
    return col_sums

# ─── STEP 2: NORMALIZED MATRIX & WEIGHTS ──────────────────────────────────────
def compute_weights():
    col_sums = RAW_MATRIX.sum(axis=0)
    norm_matrix = RAW_MATRIX / col_sums          # divide each column by its sum
    weights = norm_matrix.mean(axis=1)           # row averages = priority weights
    return norm_matrix, weights, col_sums

def print_normalized_matrix(norm_matrix, weights):
    section("STEP 2 | NORMALIZED MATRIX & PRIORITY WEIGHTS")
    short = FACTOR_IDS
    col_w = 8
    print(f"  Formula: N[i,j] = A[i,j] / ColSum[j]   |   Weight(i) = RowAverage(i)")
    print()
    header_row = f"  {'Factor':<22}" + "".join(f"{s:>{col_w}}" for s in short) + f"{'Weight':>10}{'Wt (%)':>10}"
    print(header_row)
    print("  " + "-" * (22 + col_w * 7 + 20))
    for i, row in enumerate(norm_matrix):
        vals = "".join(f"{v:>{col_w}.4f}" for v in row)
        w    = weights[i]
        print(f"  {FACTOR_IDS[i]:<6} {FACTOR_NAMES[i][:14]:<16}{vals}{w:>10.4f}{w*100:>9.2f}%")
    print("  " + "-" * (22 + col_w * 7 + 20))
    print(f"  {'SUM':<22}{'':>{col_w*7}}{weights.sum():>10.4f}{'100.00%':>10}")

# ─── STEP 3: CONSISTENCY CHECK ────────────────────────────────────────────────
def compute_consistency(weights):
    n         = len(weights)
    Aw        = RAW_MATRIX.dot(weights)           # weighted sum vector
    lambdas   = Aw / weights                      # lambda_i = (Aw)_i / w_i
    lambda_max = lambdas.mean()
    CI        = (lambda_max - n) / (n - 1)
    RI        = RI_TABLE[n]
    CR        = CI / RI
    return Aw, lambdas, lambda_max, CI, RI, CR

def print_consistency(weights, Aw, lambdas, lambda_max, CI, RI, CR):
    section("STEP 3 | WEIGHTED SUM VECTOR & CONSISTENCY CHECK")
    n = len(weights)
    print(f"  Formula: Aw = A x w  |  lambda_i = (Aw)_i / w_i  |  lambda_max = mean(lambda_i)")
    print()
    print(f"  {'Factor':<30} {'Weight (w)':>12} {'Aw':>12} {'lambda_i':>12}")
    print("  " + "-" * 68)
    for i in range(n):
        print(f"  {FACTOR_NAMES[i]:<30} {weights[i]:>12.4f} {Aw[i]:>12.4f} {lambdas[i]:>12.4f}")
    print("  " + "-" * 68)
    print(f"  {'lambda_max (average)':>44}   {lambda_max:>12.4f}")
    print()
    print(f"  n  (number of factors)         = {n}")
    print(f"  lambda_max                     = {lambda_max:.4f}")
    print(f"  CI = (lambda_max - n) / (n-1)  = ({lambda_max:.4f} - {n}) / ({n}-1) = {CI:.4f}")
    print(f"  RI (Saaty table, n={n})         = {RI:.2f}")
    print(f"  CR = CI / RI                   = {CI:.4f} / {RI:.2f} = {CR:.4f}")
    print()
    if CR < 0.10:
        print(f"  [RESULT]  CR = {CR:.4f}  <  0.10  ===  CONSISTENT  ===  Weights are VALID")
    else:
        print(f"  [RESULT]  CR = {CR:.4f}  >=  0.10  === INCONSISTENT === Revise the matrix!")

# ─── STEP 4: WEIGHTS SUMMARY ──────────────────────────────────────────────────
def print_weights_summary(weights):
    section("STEP 4 | PRIORITY WEIGHTS - RANKED SUMMARY")
    ranked = sorted(zip(weights, FACTOR_IDS, FACTOR_NAMES), reverse=True)
    bar_max = 40
    print(f"  {'Rank':<6} {'ID':<6} {'Factor':<34} {'Weight':>8} {'%':>7}  Bar")
    print("  " + "-" * 74)
    for rank, (w, fid, fname) in enumerate(ranked, 1):
        bar = int(w / ranked[0][0] * bar_max)
        print(f"  #{rank:<5} {fid:<6} {fname:<34} {w:>8.4f} {w*100:>6.2f}%  {'|'*bar}")
    print()
    print(f"  Total weight = {sum(w for w,_,_ in ranked):.4f}  (should = 1.0000)")

# ─── STEP 5: SUB-CRITERIA TABLES ──────────────────────────────────────────────
def print_sub_criteria(weights):
    section("STEP 5 | SUB-CRITERIA CLASSIFICATION & SUITABILITY RATINGS (1-5)")
    weight_map = dict(zip(FACTOR_IDS, weights))
    for fid, rows in SUB_CRITERIA.items():
        idx   = FACTOR_IDS.index(fid)
        fname = FACTOR_NAMES[idx]
        w     = weight_map[fid]
        print()
        print(f"  [{fid}] {fname}   |   Weight = {w:.4f} ({w*100:.2f}%)")
        print(f"  {'Class/Range':<28} {'Category':<14} {'Rating':<8} {'Potential':<12} Significance")
        print("  " + "-" * 74)
        for cls, cat, rating, potential, desc in rows:
            dots = "*" * rating + "-" * (5 - rating)
            print(f"  {cls:<28} {cat:<14} [{dots}] {rating}  {potential:<12} {desc}")

# ─── STEP 6: FINAL FORMULA ────────────────────────────────────────────────────
def print_formula(weights):
    section("STEP 6 | FINAL GWPZ WEIGHTED OVERLAY FORMULA")
    terms = [f"({weights[i]:.4f} x {FACTOR_IDS[i]}_rating)" for i in range(len(FACTOR_IDS))]
    print()
    print("  GWPZ_Score (S) =")
    # print in two lines for readability
    half = len(terms) // 2 + 1
    line1 = "    " + " + ".join(terms[:half])
    line2 = "    " + " + ".join(terms[half:])
    print(line1 + " +")
    print(line2)
    print()
    print("  Expanded:")
    print(f"  S = (0.4055 x GEO)  + (0.2147 x RAIN) + (0.1492 x SOIL)")
    print(f"    + (0.1034 x LD)   + (0.0728 x LULC) + (0.0272 x DD)")
    print(f"    + (0.0272 x SLP)")
    print()
    print("  GWPZ Classification:")
    print(f"  {'Score Range':<16} {'Zone':<14} Action")
    print("  " + "-" * 62)
    zones = [
        ("1.0 - 1.8", "Very Poor",  "Avoid drilling; poor aquifer potential"),
        ("1.8 - 2.6", "Poor",       "Low yield expected; expensive drilling"),
        ("2.6 - 3.4", "Moderate",   "Moderate yield; requires detailed survey"),
        ("3.4 - 4.2", "Good",       "Recommended for exploration"),
        ("4.2 - 5.0", "Very Good",  "Excellent recharge; high priority zone"),
    ]
    for score, zone, action in zones:
        print(f"  {score:<16} {zone:<14} {action}")

# ─── STEP 7: GIS WORKFLOW ─────────────────────────────────────────────────────
def print_gis_workflow():
    section("STEP 7 | GIS IMPLEMENTATION WORKFLOW")
    steps = [
        ("Data Collection",  "SRTM DEM (30m), Sentinel/LISS imagery, GSI geology maps, "
                              "IMD/TRMM rainfall, NBSS soil surveys, ASTER lineaments."),
        ("Preprocessing",    "Reproject all layers to common CRS (UTM). Resample to "
                              "30m resolution. Clip to study area boundary."),
        ("Layer Generation", "Slope from DEM | Drainage Density from DEM | Lineaments via "
                              "PCA/edge detection | LULC classification | Rainfall rasters | "
                              "Geology & Soil digitisation."),
        ("Reclassification", "Reclassify each layer to 1-5 suitability scale as per "
                              "sub-criteria table above."),
        ("Weighted Overlay", "Apply AHP weights in ArcGIS Weighted Index Overlay tool or "
                              "QGIS Raster Calculator using the formula in Step 6."),
        ("GWPZ Map",         "Classify output raster into 5 zones. Add legend, "
                              "scale bar, north arrow, and graticule."),
        ("Validation",       "Validate GWPZ map against borewell yield data, water table "
                              "records, or ROC/AUC accuracy assessment."),
    ]
    for i, (title, desc) in enumerate(steps, 1):
        print(f"\n  [{i}] {title}")
        # wrap description at 70 chars
        words = desc.split()
        line, lines = [], []
        for w in words:
            if len(" ".join(line + [w])) > 66:
                lines.append(" ".join(line))
                line = [w]
            else:
                line.append(w)
        lines.append(" ".join(line))
        for l in lines:
            print(f"      {l}")

# ─── STEP 8: REFERENCES ───────────────────────────────────────────────────────
def print_references():
    section("REFERENCES")
    refs = [
        "Saaty, T.L. (1980). The Analytic Hierarchy Process. McGraw-Hill, New York.",
        "Jha, M.K. et al. (2010). Groundwater assessment using AHP & GIS. Hydrogeology Journal.",
        "Singh, A.K. et al. (2013). GWPZ mapping using MCA & GIS. J. Earth System Science.",
        "Rahmati, O. et al. (2015). GWP assessment using AHP & ML. Environ. Earth Sciences.",
    ]
    for r in refs:
        print(f"  * {r}")

# ─── EXAMPLE SCORE CALCULATOR ─────────────────────────────────────────────────
def calculate_example_score(weights):
    section("BONUS | EXAMPLE GWPZ SCORE CALCULATOR")
    print("  Example pixel/polygon with the following class ratings:")
    example = {"SLP": 4, "DD": 3, "LD": 4, "LULC": 3, "RAIN": 4, "GEO": 4, "SOIL": 3}
    score = 0.0
    print(f"\n  {'Factor':<34} {'Weight':>8}  {'Rating':>7}  {'Contribution':>13}")
    print("  " + "-" * 66)
    for i, fid in enumerate(FACTOR_IDS):
        w = weights[i]
        r = example[fid]
        contrib = w * r
        score  += contrib
        print(f"  {FACTOR_NAMES[i]:<34} {w:>8.4f}  {r:>7d}  {contrib:>13.4f}")
    print("  " + "-" * 66)
    print(f"  {'GWPZ Score (S)':<34} {'':>8}  {'':>7}  {score:>13.4f}")
    print()
    if   score >= 4.2: zone = "Very Good"
    elif score >= 3.4: zone = "Good"
    elif score >= 2.6: zone = "Moderate"
    elif score >= 1.8: zone = "Poor"
    else:              zone = "Very Poor"
    print(f"  => Groundwater Potential Zone: [{zone}]")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    header("GROUNDWATER POTENTIAL ZONE (GWPZ) MAPPING")
    print("  Method  : Analytic Hierarchy Process (AHP)")
    print("  MCDM    : Weighted Index Overlay")
    print("  Factors : 7 Thematic Layers")
    print("  Reference: Saaty (1980)")

    col_sums                        = print_raw_matrix()
    norm_matrix, weights, col_sums  = compute_weights()
    print_normalized_matrix(norm_matrix, weights)
    Aw, lambdas, lmax, CI, RI, CR   = compute_consistency(weights)
    print_consistency(weights, Aw, lambdas, lmax, CI, RI, CR)
    print_weights_summary(weights)
    print_sub_criteria(weights)
    print_formula(weights)
    print_gis_workflow()
    calculate_example_score(weights)
    print_references()

    separator()
    print(f"  AHP ANALYSIS COMPLETE  |  CR = {CR:.4f}  |  n = 7  |  Status: VALID")
    separator()

if __name__ == "__main__":
    main()
