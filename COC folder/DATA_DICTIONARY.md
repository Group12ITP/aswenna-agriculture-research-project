# Sri Lanka Cost of Cultivation (COC) Dataset — Data Dictionary

## Overview
This dataset consolidates agricultural **Cost of Cultivation (COC)** reports published by the **Socio Economics & Planning Centre (SEPC), Department of Agriculture, Peradeniya, Sri Lanka**. 

The dataset was constructed for **SO1 (Predictive Cost Estimator)** of **IT4010: Intelligent Decision Support System for Agricultural Production Cost Prediction**. It aggregates 19 cultivation seasons (**2014-15 Maha** through **2025 Yala**), spanning **658 verified crop-district cultivation records** across **24 distinct crops** and **25 agricultural districts/regions**.

---

## Output Files
1. **`coc_master.csv`**: The master training tabular dataset with 658 rows and 46 standardized columns.
2. **`coc_master_v2.csv`**: The exchange-rate augmented training dataset (658 rows, 48 columns) including `USD_LKR_Rate` and `Total_Cost_Incl_Imputed_USD`.
3. **`coc_features.csv`**: The feature-engineered dataset (658 rows, 55 columns) prior to cross-season deduplication.
4. **`coc_features_dedup.csv`**: The cleaned, deduplicated training dataset (642 rows, 55 columns) with regenerated time-series lag and ratio features.
5. **`coc_model_ready.csv`**: Filtered modeling dataset (641 rows, 23 crops) restricted to High and Medium sample size categories.
6. **`model_evaluation.csv`**: Comprehensive model evaluation metrics (GroupKFold and LOSO) across Linear Regression, Decision Tree, Random Forest, and Gradient Boosting.
7. **`model_evaluation_loso_per_year.csv`**: Detailed year-by-year temporal holdout (LOSO) performance across all 12 cultivation years (2014–2025).
8. **`ablation_results.csv`**: 5-variant feature ablation results evaluating the contributions of lag, macro/temporal, and structural features.
9. **`baselines.csv`**: Benchmark metrics for Naive Carry-Forward (B1) and Out-of-Fold Crop-District Mean (B2).
10. **`feature_importances.png`**: High-resolution chart contrasting relative feature importances for Gradient Boosting and Random Forest.
11. **`residuals_plot.png`**: Out-of-fold predicted vs actual cultivation costs under Leave-One-Season-Out, colored by cultivation start year.
12. **`best_model_pipeline.pkl`**: Fully fitted, production-ready scikit-learn pipeline (preprocessor + target regressor) serialized via joblib.
13. **`train_evaluate_pipeline.py`**: The complete end-to-end Python pipeline script implementing leak-free preprocessing, validation, tuning, ablation, and diagnostics.
14. **`parse_report.csv`**: Complete audit log recording the disposition of every worksheet (658 SUCCESS, 9 DROPPED_IDENTICAL_DUPLICATE, 1 SKIPPED_DRAFT, 4 MERGED_CONTINUATION, 14 SKIPPED_BLANK, 14 SKIPPED_COVER_TOC, 8 SKIPPED_SUMMARY).
15. **`consolidate_coc.py`**: The fully automated, self-contained extraction pipeline with modular alias, deduplication, and parsing functions.
16. **`add_exchange_rate.py`**: Script merging annual LKR/USD rates and generating the dual-panel inflation/devaluation analysis chart (`exchange_rate_check.png`).
17. **`build_features.py`**: Script implementing grouped time-series lag calculation, ratio features, and sample size tiering.
18. **`deduplicate_and_engineer.py`**: Script detecting cross-season identical placeholder records, dropping earlier duplicates, and recomputing downstream features.
19. **`exchange_rate_check.png`**: High-resolution two-panel comparative plot showing Raw LKR costs vs USD-adjusted costs across 2014–2025.
20. **`predict_with_intervals.py`**: Standalone prediction interval module with stratified residual standard deviations and macroeconomic deviation checks.
21. **`interval_calibration.png`**: Dual-panel calibration diagnostic comparing nominal vs empirical coverage and coverage sorted by interval width.
22. **`prediction_api.py`**: Production FastAPI service exposing `/predict`, `/health`, and `/metadata` with CORS, strict Pydantic validation, and audit logging.
23. **`test_api.py`**: Automated test suite executing live requests tests against `/health`, `/metadata`, `/predict`, and HTTP 422 validation cases.
24. **`README_API.md`**: Complete API documentation with startup commands, endpoint cURL examples, schema specifications, and troubleshooting.
25. **`sample_response.json`**: Concrete real-world response JSON payload generated from live model inference.
26. **`predictions.log`**: Audit log recording every incoming request, response, UUID, and ISO timestamp.

---

## Column Schema & Descriptions

| Column Name | Data Type | Unit | Source Block | Description & Extraction Notes |
|:---|:---|:---|:---|:---|
| **`Season`** | String | Categorical | Season Folder Name | Cultivation season: `"Maha"` (major wet season, Oct–Mar) or `"Yala"` (minor dry season, Apr–Sep). |
| **`Year_Start`** | Integer | Year (YYYY) | Season Folder Name | Calendar year cultivation commenced (e.g. `2014` for 2014-15 Maha, `2015` for 2015 Yala). |
| **`Year_End`** | Integer | Year (YYYY) | Season Folder Name | Calendar year cultivation concluded (e.g. `2015` for 2014-15 Maha, `2015` for 2015 Yala). |
| **`Year_Range`** | String | Range Label | Season Folder Name | Normalized season year label (e.g. `"2014-15"`, `"2015"`, `"2024-25"`). |
| **`Crop`** | String | Categorical | Header Title / Sheet Name / File | Normalized crop name (24 canonical crops, e.g. `Paddy`, `Big Onion`, `Maize`, `Green Chilli`, `Potato`). Merged typos/synonyms. |
| **`District`** | String | Categorical | Header Block / Sheet Name | Normalized administrative district or agricultural project system (e.g. `Anuradhapura`, `Ampara (East)`, `Mahaweli System H`, `Nuwara Eliya`). |
| **`Irrigation_Type`** | String | Categorical | Header Block / Title Line | Water regime under which crop was cultivated: `"Irrigated"`, `"Rainfed"`, or empty if unstated. |
| **`Field_Size_Basis`** | String | Constant | Metadata Standard | Benchmark land area basis: fixed to `"Per Acre"` across all official reports. |
| **`Labour_Cost`** | Float | LKR (Rs/ac) | Operations Table Subtotal | Total direct labour cost incurred across all operations per acre. Extracted from the `Total Including Imputed Cost` subtotal row. |
| **`Machinery_Cost`** | Float | LKR (Rs/ac) | Operations Table Subtotal | Total machinery, tractor, thresher, combine harvester, and equipment hire/power cost per acre. |
| **`Material_Cost`** | Float | LKR (Rs/ac) | Operations Table Subtotal | Total input materials cost (seeds, fertilizers, weedicides, pesticides) per acre. |
| **`Total_Cost_Incl_Imputed`** | Float | LKR (Rs/ac) | Operations Table Total | **Primary Prediction Target**: Full economic cost of cultivation per acre including imputed costs (family labour, owned equipment, farmer's own seed). |
| **`Total_Cost_Excl_Imputed`** | Float | LKR (Rs/ac) | Operations Table Total | **Secondary Prediction Target**: Actual out-of-pocket cash cultivation cost per acre excluding imputed costs. |
| **`Seed_Unit`** | String | Unit Label | Related Info (Inputs Block) | Unit of measurement for seed/planting material (e.g. `kg`, `Bags`, `no`). |
| **`Seed_Quantity`** | Float | Per Acre | Related Info (Inputs Block) | Quantity of seed/planting material used per acre. |
| **`Seed_Unit_Price`** | Float | LKR / Unit | Related Info (Inputs Block) | Price per unit of seed/planting material (Rs/kg or Rs/bag). |
| **`Labour_Wage_Rate`** | Float | LKR / Day | Related Info (Labour Block) / Operation Row | Prevailing average daily agricultural wage rate (Rs/man-day) for hired farm workers. |
| **`Hired_Labour_Days`** | Float | Man-days / Acre | Related Info (Labour Block) / Operation Row | Total hired labour man-days employed per acre. |
| **`Family_Labour_Days`** | Float | Man-days / Acre | Related Info (Labour Block) / Operation Row | Total unpaid family labour man-days contributed per acre. |
| **`Total_Labour_Days`** | Float | Man-days / Acre | Related Info (Labour Block) / Operation Row | Combined labour requirement (`Hired + Family` labour days) per acre. |
| **`Fertilizer_Urea_Price`** | Float | LKR / kg | Related Info (Fertilizer Block) | Unit price of Urea fertilizer (Rs/kg). |
| **`Fertilizer_Urea_Qty`** | Float | kg / Acre | Related Info (Fertilizer Block) | Total quantity of Urea fertilizer applied per acre across basal and top dressings. |
| **`Fertilizer_TSP_Price`** | Float | LKR / kg | Related Info (Fertilizer Block) | Unit price of Triple Super Phosphate (TSP) fertilizer (Rs/kg). |
| **`Fertilizer_TSP_Qty`** | Float | kg / Acre | Related Info (Fertilizer Block) | Quantity of TSP fertilizer applied per acre. |
| **`Fertilizer_MOP_Price`** | Float | LKR / kg | Related Info (Fertilizer Block) | Unit price of Muriate of Potash (MOP) fertilizer (Rs/kg). |
| **`Fertilizer_MOP_Qty`** | Float | kg / Acre | Related Info (Fertilizer Block) | Quantity of MOP fertilizer applied per acre. |
| **`Fertilizer_Basal_TSP_Price`** | Float | LKR / kg | Related Info (Fertilizer Block) | Unit price of TSP used specifically during basal fertilizer application (Rs/kg). |
| **`Fertilizer_Basal_TSP_Qty`** | Float | kg / Acre | Related Info (Fertilizer Block) | Quantity of TSP applied during basal application (kg/ac). |
| **`Fertilizer_Basal_Urea_Price`** | Float | LKR / kg | Related Info (Fertilizer Block) | Unit price of Urea applied at basal stage (Rs/kg). |
| **`Fertilizer_Basal_Urea_Qty`** | Float | kg / Acre | Related Info (Fertilizer Block) | Quantity of Urea applied at basal stage (kg/ac). |
| **`Fertilizer_Basal_MOP_Price`** | Float | LKR / kg | Related Info (Fertilizer Block) | Unit price of MOP applied at basal stage (Rs/kg). |
| **`Fertilizer_Basal_MOP_Qty`** | Float | kg / Acre | Related Info (Fertilizer Block) | Quantity of MOP applied at basal stage (kg/ac). |
| **`Fertilizer_Top_Urea_Price`** | Float | LKR / kg | Related Info (Fertilizer Block) | Unit price of Urea applied during vegetative top dressing stages (Rs/kg). |
| **`Fertilizer_Top_Urea_Qty`** | Float | kg / Acre | Related Info (Fertilizer Block) | Quantity of Urea applied during top dressing stages (kg/ac). |
| **`Fertilizer_Top_MOP_Price`** | Float | LKR / kg | Related Info (Fertilizer Block) | Unit price of MOP applied during top dressing stages (Rs/kg). |
| **`Fertilizer_Top_MOP_Qty`** | Float | kg / Acre | Related Info (Fertilizer Block) | Quantity of MOP applied during top dressing stages (kg/ac). |
| **`Average_Yield_kg_ac`** | Float | kg / Acre | Yield and Returns Block | Average harvested crop yield per acre (kg/ac). |
| **`Price_of_Produce`** | Float | LKR / kg | Yield and Returns Block | Average farm-gate selling price received by farmers per kilogram of harvested produce (Rs/kg). |
| **`Gross_Income`** | Float | LKR (Rs/ac) | Yield and Returns Block | Total gross revenue earned per acre (`Average_Yield_kg_ac * Price_of_Produce`). |
| **`Profit_Incl_Imputed`** | Float | LKR (Rs/ac) | Yield and Returns Block | Net economic profit per acre (`Gross_Income - Total_Cost_Incl_Imputed`). |
| **`Profit_Excl_Imputed`** | Float | LKR (Rs/ac) | Yield and Returns Block | Net cash margin per acre (`Gross_Income - Total_Cost_Excl_Imputed`). |
| **`Per_Unit_Cost_Incl_Imputed`**| Float | LKR / kg | Yield and Returns Block | Average cost of production per kilogram of produce including imputed costs (Rs/kg). |
| **`Per_Unit_Cost_Excl_Imputed`**| Float | LKR / kg | Yield and Returns Block | Average out-of-pocket production cost per kilogram of produce excluding imputed costs (Rs/kg). |
| **`Remarks`** | String | Free text | Notes / Footnotes / Bottom Rows | Field remarks capturing anomalous events (e.g. drought, flood during flowering, heavy pest attacks, government fertilizer subsidy). |
| **`Source_File`** | String | Traceability | Excel File Name | Name of the source `.xlsx` workbook from which the observation was extracted. |
| **`Source_Sheet`** | String | Traceability | Excel Sheet Name | Title of the worksheet inside the source workbook. |
| **`USD_LKR_Rate`** | Float | LKR / USD | Macro Table (v2) | Annual average foreign exchange rate used for currency normalization. |
| **`Total_Cost_Incl_Imputed_USD`** | Float | USD / acre | Computed Column (v2) | USD-adjusted economic cultivation cost per acre (`Total_Cost_Incl_Imputed / USD_LKR_Rate`). |
| **`Prev_Season_Total_Cost_Incl_Imputed`** | Float | LKR (Rs/ac) | Grouped Lag (Features) | Prior season's economic cultivation cost for the same `(Crop, District, Irrigation_Type)` group. `NaN` for first season. |
| **`Prev_Season_Year`** | Float | Year (YYYY) | Grouped Lag (Features) | Starting calendar year of the prior cultivation season for temporal verification. |
| **`Cost_Pct_Change_From_Prev_Season`** | Float | Percentage (%) | Computed Lag (Features) | Percentage change in cultivation cost relative to prior season: `(current - prev) / prev * 100`. |
| **`Fertilizer_Cost_Pct_of_Total`** | Float | Ratio [0.0–1.0] | Component Ratio (Features) | Material & input cost share of total economic cost: `Material_Cost / Total_Cost_Incl_Imputed`. |
| **`Labour_Cost_Pct_of_Total`** | Float | Ratio [0.0–1.0] | Component Ratio (Features) | Direct labour cost share of total economic cost: `Labour_Cost / Total_Cost_Incl_Imputed`. |
| **`Machinery_Cost_Pct_of_Total`** | Float | Ratio [0.0–1.0] | Component Ratio (Features) | Machinery, tractor, and equipment power share of total cost: `Machinery_Cost / Total_Cost_Incl_Imputed`. |
| **`Crop_Sample_Size_Category`** | String | Categorical | Sample Size Tier (Features) | Data sufficiency tier: `"High"` (>= 15 rows), `"Medium"` (5–14 rows), or `"Low"` (< 5 rows). |

---

## Crop and District Standardization Details

### 1. Crop Normalization (24 Categories)
- **Paddy**: Includes all varieties and water regimes (Irrigated, Rainfed).
- **Other Field Crops (OFC)**: `Maize`, `Black Gram`, `Cowpea`, `Green Gram`, `Kurakkan`, `Groundnut`, `Gingelly`, `Soybean`.
- **Condiments & Alliums**: `Big Onion`, `Red Onion`, `Green Chilli`, `Capsicum`.
- **Vegetables & Root Crops**: `Beetroot`, `Bitter Gourd`, `Brinjal`, `Cabbage`, `Carrot`, `Manioc`, `Pole Bean`, `Potato`, `Pumpkin`, `Sweet Potato`, `Tomato`.

### 2. District & Region Normalization (25 Categories)
- **Major Districts**: `Ampara`, `Ampara (East)`, `Ampara (West)`, `Anuradhapura`, `Badulla`, `Batticaloa`, `Gampaha`, `Hambantota`, `Jaffna`, `Kalutara`, `Kandy`, `Kurunegala`, `Mannar`, `Matale`, `Monaragala`, `Nuwara Eliya`, `Polonnaruwa`, `Puttalam`, `Trincomalee`, `Vavuniya`.
- **Agrarian Systems**: `Mahaweli System B`, `Mahaweli System C`, `Mahaweli System H`, `Udawalawa`.
- **Aggregates**: `Whole Island`.

---

## Data Quality & Verification Audits

### 1. Verification of 38 Duplicate Rows (Issue 1)
In the initial consolidation pass, 38 rows (19 pairs) shared identical `(Crop, District, Season, Irrigation_Type)`. An exhaustive audit of both source worksheets across all 19 pairs revealed two underlying phenomena:

1. **Exact Duplicate Workbooks/Sheets (10 rows dropped)**:
   - **2017 Yala Vegetables (7 pairs)**: `final sheets.xlsx` consolidated sheets from `Low country vegetables.xlsx` and `Up country vegetables.xlsx`. The tables for Bitter Gourd (Hambantota), Brinjal (Hambantota), Cabbage (Nuwara Eliya), Carrot (Nuwara Eliya), Pole Bean (Badulla), Tomato (Badulla), and Tomato (Kandy) were 100% byte-for-byte identical. The secondary workbook copies were dropped and logged as `DROPPED_IDENTICAL_DUPLICATE` in `parse_report.csv`.
   - **2020 Yala Paddy Kalutara (1 pair)**: Intra-workbook duplicate tabs `Paddy-Kalutara 2020` vs `Kalutara 20y` in `cheked final sheets 2020y .xlsx`. Exact identical figures; `Kalutara 20y` dropped and logged in `parse_report.csv`.
   - **2021-22 Maha Groundnut Monaragala (1 pair)**: Intra-workbook duplicate tabs `g'nut-m'gala` vs `G.nut-mona` in `OFC Final tables.xlsx`. Exact identical figures; `G.nut-mona` dropped and logged in `parse_report.csv`.
   - **2022-23 Maha Paddy Whole Island (1 pair)**: Two sheets existed in `2022- 23 maha Paddy finals.xlsx`: `WI(Irrigated)` (Total cost 137,705.9) and `s` (Total cost 146,055.9). Cross-referencing against the workbook's published `Stat table` proved that `s` was an unfinalized working draft copy, while `WI(Irrigated)` matched the official publication. Sheet `s` was dropped and logged as `SKIPPED_DRAFT` in `parse_report.csv`.

2. **Template Header Clones / Misattributed Districts (28 rows retained & disambiguated)**:
   - In 14 pairs, government officers cloned Excel worksheets as templates, renaming the sheet tab or title but failing to update the static district text in cell `C2`.
   - Examples: Tab `Potato-NÉliya` had `Badulla` in cell C2; tab `Tomato-KAndy` had `Badulla` in cell C2; tab `Sys C` had `Polonnaruwa` in cell C2; tabs `Sys B` and `Sys C` had `System B` in cell C2.
   - In Ampara, sub-districts were separated into `Ampara (East)` and `Ampara (West)` across 2021-22 Maha, 2022 Yala, 2023-24 Maha, and 2024 Yala.
   - By giving sheet tabs and titles precedence when they specify distinct regions, all 28 rows were correctly mapped to their true districts (`Nuwara Eliya`, `Kandy`, `Mahaweli System B`, `Mahaweli System C`, `Ampara (East)`, `Ampara (West)`). All figures genuinely differ and represent distinct agro-ecological domains; both rows were preserved.
   - **Final Duplicate Count**: **0 remaining duplicate groups** in `coc_master.csv`.

### 2. Verification of Yield * Price vs Gross Income Discrepancies (Issue 2)
12 rows exhibited differences between `Average_Yield_kg_ac * Price_of_Produce` and `Gross_Income` (> 1 LKR). Inspection of the original Excel cells revealed:

1. **Extraction Parser Bugs (3 rows — All Fixed)**:
   - **2015-16 Maha Black Gram Anuradhapura**: A secondary `#VALUE!` template table at row 38 was overwriting the primary yield block with 0. **Fix**: Parser stops scanning upon `#VALUE!` error blocks. Now Gross Income = 66,834 (423 kg * Rs 158).
   - **2015-16 Maha Paddy Kandy**: A secondary unedited template table at row 54 overwrote Gross Income with 51,920. **Fix**: Parser preserves primary Yield block and skips secondary blank tables. Now Gross Income = 42,089.62 (1,343 kg * Rs 31.34).
   - **2016-17 Maha Black Gram Vavuniya**: A 1-row vertical label shift placed Price (`Rs 225`) in the row of `YIELD AND RETURNS` header, shifting Gross Income to Price. **Fix**: Header-shifted layout detector extracts Price (`Rs 225`) and Gross Income (`Rs 37,125` = 165 kg * Rs 225).
2. **Official Published Rounding & Field Variances (9 rows — Verified Valid)**:
   - **Official Farm-gate Price Rounding (6 rows)**: In SEPC publications (e.g. 2024 Yala Big Onion Matale, Potato Badulla, Manioc Gampaha, Sweet Potato Matale; 2025 Yala Paddy Whole Island, Big Onion Matale; 2015 Yala Paddy Gampaha), reported farm-gate prices are rounded to the nearest integer rupee (e.g. Badulla Potato reported as Rs 199/kg, while exact unrounded farm receipts averaged Rs 198.71/kg, producing 4,447 * 198.70789 = 883,654). The original Excel sheet cells literally contain these exact numbers; they represent official SEPC reporting practice and must not be altered.
   - **Rainfed Kurunegala Paddy (2021-22 Maha)**: Yield = 623 kg/ac, Price = Rs 83/kg, Gross Income = Rs 48,158.26. The actual realized farm-gate price was Rs 77.30/kg due to moisture discounts, while Rs 83/kg was the official target price. Cell `R49:C7` is hardcoded as `48158.26`.
   - **Gampaha Paddy Crop Failure (2015-16 Maha)**: Yield is recorded as `0` due to localized flood failure, yet salvage gross income was recorded as Rs 53,905.
   - These 9 rows represent genuine source records and remain faithfully preserved.

---

## Special Parsing Features Implemented
1. **Multi-Era Handling**: Parses both older sheets (2014–2022) with metadata headers in rows 1–4 and newer sheets (2023–2025) with dynamic table title regex.
2. **Continuation Sheet Merging**: In newer reports (2023–2024), lengthy tables overflowed onto a 2nd page (e.g. `Sheet6` after `Sheet5`, `Sheet18` after `Sheet17`, `Sheet19` after `Sheet18`). The pipeline identifies orphan Yield & Return blocks and attaches them seamlessly to the primary crop record.
3. **Template Header Clone Disambiguation**: Cross-validates sheet tab names and title cells against header blocks, resolving officer copy-paste template errors.
4. **Junk Character Scrubbing**: Automatically removes stray commas, backticks (e.g. `` `(1579.00) ``), apostrophes, double quotes, and asterisks (e.g. `842*`) before casting to numeric floats.
5. **Parenthetical Sub-practice Isolation**: Ignores minority parenthesised practice lines (e.g. `"(with Buffaloes)"` with values in parentheses `"(1000)"`) to prevent double counting.
6. **No Data Loss Audit**: Every sheet examined is cataloged in `parse_report.csv` with its status and explanation, guaranteeing transparency for machine learning audits.
