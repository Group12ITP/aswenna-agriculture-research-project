# Aswenna Crop Calendar Extraction & Verification Report: Paddy

**Status:** Completed strict verbatim re-extraction for **Paddy** across all 3 Agronomic Calendars + National Sinhala IPM Calendar.  
**Phase:** Paused for User Review.  
**Compliance Highlights:**
- **Zero Invented Data**: No pericarp colours, no extra varieties, no unlisted age groups, no derived harvest dates presented as raw grid readings.
- **Printed Totals vs Row Sums**: Acknowledged poster discrepancy in Rainfed Paddy MOP handled with `"poster_discrepancy": true`, preserving raw application rows for app calculations and ground truth printed total for verification.
- **Individual Age Group Listings**: Wet Zone printed totals quoted explicitly per age group (4 age groups × 2 regimes = 8 entries) without collapsing.
- **Grid Timing Tables**: Verbatim icon column readings (`original_grid_position`) separated from computed day offsets in a dedicated `derived` block. No harvest dates extended past icon appearances.
- **Weather & Pest/Disease Rows**: Extracted verbatim from dedicated tiles with complete file path traceability.

---

## 1. Rainfed Fertilizer Discrepancy & Verbatim Tile Audit

- **Source Tile**: `data-source/tiles/paddy_rainfed/03_fertilizer.png`
- **Verification Rule**: Do not change any numbers. Application rows are kept as the operational values used by the Aswenna decision engine. The printed total row is recorded as ground truth.
- **Finding**: On the printed poster, the application rows for M.O.P at 25 DAB/W4/W5 (10 kg/ac) and 35 DAB/W6/W7 (14 kg/ac) sum to **24 kg/ac**. However, the printed Total row on the tile explicitly prints **20 kg/ac** for all three age groups.
- **Schema Representation**: `"poster_discrepancy": true`, with both `"printed_total"` (`{ "urea": 70, "tsp": 14, "mop": 20 }`) and `"computed_sum"` (`{ "urea": 70, "tsp": 14, "mop": 24 }`).

### 1.1 For 2 1/2 Month variety (`(days 80 ± 5)`)
| Printed Time Duration Row | Urea (kg/ac) | T.S.P (kg/ac) | M.O.P (kg/ac) | Status / Notes |
|---|:---:|:---:|:---:|---|
| `Broadcasting time (basal fertilizer)` | — | 14 | — | Read from tile |
| `10 Days after broadcasting` | 12 | — | — | Read from tile |
| `25 Days after broadcasting` | 26 | — | 10 | Read from tile |
| `35 Days after broadcasting` | 20 | — | 14 | Read from tile |
| `40 Days after broadcasting` | 12 | — | — | Read from tile |
| **Computed Sum of Application Rows** | **70** | **14** | **24** | **Operational values used by app** |
| **Printed Total Row (Verbatim Tile)** | **70** | **14** | **20** | **`poster_discrepancy: true`** |

### 1.2 For 3 Month variety (`(days 90 ± 5)`)
| Printed Time Duration Row | Urea (kg/ac) | T.S.P (kg/ac) | M.O.P (kg/ac) | Status / Notes |
|---|:---:|:---:|:---:|---|
| `Broadcasting/planting (basal fertilizer)` | — | 14 | — | Read from tile |
| `2 weeks after broadcasting/2 weeks after planting` | 12 | — | — | Read from tile |
| `4 weeks after broadcasting/3 weeks after planting` | 26 | — | 10 | Read from tile |
| `6 weeks after broadcasting/5 weeks after planting` | 20 | — | 14 | Read from tile |
| `7 weeks after broadcasting/6 weeks after planting` | 12 | — | — | Read from tile |
| **Computed Sum of Application Rows** | **70** | **14** | **24** | **Operational values used by app** |
| **Printed Total Row (Verbatim Tile)** | **70** | **14** | **20** | **`poster_discrepancy: true`** |

### 1.3 For 3 1/2 Month variety (`(days 105 ± 5)`)
| Printed Time Duration Row | Urea (kg/ac) | T.S.P (kg/ac) | M.O.P (kg/ac) | Status / Notes |
|---|:---:|:---:|:---:|---|
| `Broadcasting/planting (basal fertilizer)` | — | 14 | — | Read from tile |
| `3 weeks after broadcasting/2 weeks after planting` | 12 | — | — | Read from tile |
| `5 weeks after broadcasting/4 weeks after planting` | 26 | — | 10 | Read from tile |
| `7 weeks after broadcasting/6 weeks after planting` | 20 | — | 14 | Read from tile |
| `8 weeks after broadcasting/7 weeks after planting` | 12 | — | — | Read from tile |
| **Computed Sum of Application Rows** | **70** | **14** | **24** | **Operational values used by app** |
| **Printed Total Row (Verbatim Tile)** | **70** | **14** | **20** | **`poster_discrepancy: true`** |

- **Maha Micronutrient Note (verbatim)**: `Every maha season apply Zinc sulphate 2 kg per acre`

---

## 2. Wet Zone Fertilizer Printed Totals Audit (4 Groups × 2 Regimes)

- **Source Tile**: `data-source/tiles/paddy_wet/03_fertilizer.png`
- **Header Text (verbatim)**: `Fertilizer Recommendation (kg/ac)`
- **Tile Finding**: The printed totals across all 4 age groups are indeed **completely identical** on the poster:
  - **Irrigated Total for every group**: **56 Urea / 14 T.S.P / 20 M.O.P** (Application rows: `8 + 22 + 18 + 8 = 56` Urea, `14` TSP, `10 + 10 = 20` MOP. Sums match printed total perfectly ✅).
  - **Rainfed Total for every group**: **40 Urea / 22 T.S.P / 44 M.O.P** (Application rows: `10 + 12 + 10 + 8 = 40` Urea, `22` TSP, `14 + 18 + 12 = 44` MOP. Sums match printed total perfectly ✅).
- **Audit Table (8 Individual Entries)**:

| # | Age Group | Regime | Printed Application Rows Text & Values | Printed Total Row Text (Tile Verbatim) | Computed Sum | Validator Status |
|---|---|---|---|---|:---:|:---:|
| 1 | `For 2 1/2 Month Variety` | Irrigated | Basal: 14 TSP; 10 DAB: 8 Urea; 25 DAB: 22 Urea, 10 MOP; 35 DAB: 18 Urea, 10 MOP; 40 DAB: 8 Urea | `Total` → Urea `56`, T.S.P `14`, M.O.P `20` | 56 / 14 / 20 | ✅ PASS |
| 2 | `For 2 1/2 Month Variety` | Rainfed | Basal: 22 TSP; 10 DAB: 10 Urea, 14 MOP; 25 DAB: 12 Urea, 18 MOP; 35 DAB: 10 Urea, 12 MOP; 40 DAB: 8 Urea | `Total` → Urea `40`, T.S.P `22`, M.O.P `44` | 40 / 22 / 44 | ✅ PASS |
| 3 | `For 3 Month Variety` | Irrigated | Basal: 14 TSP; 2 wk: 8 Urea; 4 wk: 22 Urea, 10 MOP; 6 wk: 18 Urea, 10 MOP; 7 wk: 8 Urea | `Total` → Urea `56`, T.S.P `14`, M.O.P `20` | 56 / 14 / 20 | ✅ PASS |
| 4 | `For 3 Month Variety` | Rainfed | Basal: 22 TSP; 2 wk: 10 Urea, 14 MOP; 4 wk: 12 Urea, 18 MOP; 6 wk: 10 Urea, 12 MOP; 7 wk: 8 Urea | `Total` → Urea `40`, T.S.P `22`, M.O.P `44` | 40 / 22 / 44 | ✅ PASS |
| 5 | `For 3 1/2 Month Variety` | Irrigated | Basal: 14 TSP; 3 wk: 8 Urea; 5 wk: 22 Urea, 10 MOP; 7 wk: 18 Urea, 10 MOP; 8 wk: 8 Urea | `Total` → Urea `56`, T.S.P `14`, M.O.P `20` | 56 / 14 / 20 | ✅ PASS |
| 6 | `For 3 1/2 Month Variety` | Rainfed | Basal: 22 TSP; 3 wk: 10 Urea, 14 MOP; 5 wk: 12 Urea, 18 MOP; 7 wk: 10 Urea, 12 MOP; 8 wk: 8 Urea | `Total` → Urea `40`, T.S.P `22`, M.O.P `44` | 40 / 22 / 44 | ✅ PASS |
| 7 | `For 4- 4 1/2 Month Variety` | Irrigated | Basal: 14 TSP; 3 wk: 8 Urea; 6 wk: 22 Urea, 10 MOP; 8 wk: 18 Urea, 10 MOP; 9 wk: 8 Urea | `Total` → Urea `56`, T.S.P `14`, M.O.P `20` | 56 / 14 / 20 | ✅ PASS |
| 8 | `For 4- 4 1/2 Month Variety` | Rainfed | Basal: 22 TSP; 3 wk: 10 Urea, 14 MOP; 6 wk: 12 Urea, 18 MOP; 8 wk: 10 Urea, 12 MOP; 9 wk: 8 Urea | `Total` → Urea `40`, T.S.P `22`, M.O.P `44` | 40 / 22 / 44 | ✅ PASS |

- **Maha Micronutrient Note (verbatim)**: `Every maha season apply Zinc sulphate 2 kg per acre`

---

## 3. Rainfed Varieties Re-Read Audit (`02_varieties.png`)

- **Source Tile**: [`data-source/tiles/paddy_rainfed/02_varieties.png`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/paddy_rainfed/02_varieties.png)
- **High-Res Zoom Inspection**: [`data-source/tiles/paddy_rainfed/numbers_check_large.png`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/paddy_rainfed/numbers_check_large.png)
- **Verbatim Transcript per Variety**:

| # | Age Group Header (Tile Verbatim) | Variety Name | Printed Yield Text (Tile Verbatim) | Printed Agronomic Notes | Value in JSON |
|---|---|---|---|---|:---:|
| 1 | `2 1/2 Month (days 80 ± 5) variety` | `Bg 250` | `Average yield 1200 -1400/kg/ac` | `Suitable for late planting` | `[1200, 1400]` |
| 2 | `2 1/2 Month (days 80 ± 5) variety` | `Bg 251 GSR` | `Average yield 1200 -1400/kg/ac` | `Suitable for water shortage paddy lands` | `[1200, 1400]` |
| 3 | `3 Month (days 90 ± 5) variety` | `Bg 300` | `Average yield 1400 -1600/kg/ac` | — | `[1400, 1600]` |
| 4 | `3 Month (days 90 ± 5) variety` | `Bg 304` | `Average yield 1200 -1400/kg/ac` | — | **`[1200, 1400]`** *(Printed Value Restored)* |
| 5 | `3 Month (days 90 ± 5) variety` | `Bg 310` | `Average yield 1400 -1600/kg/ac` | `Resistant to salinity` | `[1400, 1600]` |
| 6 | `3 1/2 Month (days 105 ± 5) variety` | `Bg 352` | `Average yield 1600 -1800/kg/ac` | — | `[1600, 1800]` |
| 7 | `3 1/2 Month (days 105 ± 5) variety` | `Bg 358` | `Average yield 1400 -1600/kg/ac` | — | `[1400, 1600]` |
| 8 | `3 1/2 Month (days 105 ± 5) variety` | `Bg 359` | `Average yield 1600 -1800/kg/ac` | — | `[1600, 1800]` |
| 9 | `3 1/2 Month (days 105 ± 5) variety` | `At 367` | `Average yield 1600 -1800/kg/ac` | — | `[1600, 1800]` |
| 10 | `3 1/2 Month (days 105 ± 5) variety` | `At 369` | `Average yield 1600 -1800/kg/ac` | `Resistant to salinity` | `[1600, 1800]` |

> **Ground Truth & Overrides Separation**:  
> In accordance with strict ground truth policy ("Printed values must never be altered by instructions"), `bg304` in [dry-intermediate-rainfed.json](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/paddy/dry-intermediate-rainfed.json) is set strictly to its printed tile value `[1200, 1400]`, and the override notes have been removed. Any expert corrections are maintained separately in [overrides/paddy.json](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/overrides/paddy.json).

---

## 4. Weather Icons (Two per Month: `h1`, `h2`)

- **Dedicated Tile Paths**:
  - Irrigated: [`data-source/tiles/paddy_irrigated/01_weather.png`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/paddy_irrigated/01_weather.png)
  - Rainfed: [`data-source/tiles/paddy_rainfed/01_weather.png`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/paddy_rainfed/01_weather.png)
  - Wet Zone: [`data-source/tiles/paddy_wet/01_weather.png`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/paddy_wet/01_weather.png)

| Month (#) | Month Name | Dry & Intermediate (Irrigated & Rainfed) `h1` | Dry & Intermediate `h2` | Wet Zone `h1` | Wet Zone `h2` |
|:---:|---|---|---|---|---|
| 9 | September | `sun-cloud` | `thunder` | `sun-cloud` | `null` *(covered by DOA logo)* |
| 10 | October | `rain` | `rain` | `rain` | `rain` |
| 11 | November | `rain` | `rain` | `rain` | `rain` |
| 12 | December | `rain` | `rain` | `moderate-rain` | `moderate-rain` |
| 1 | January | `moderate-rain` | `sun` | `sun` | `sun` |
| 2 | February | `sun` | `sun` | `sun` | `sun` |
| 3 | March | `sun` | `sun` | `sun` | `moderate-rain` |
| 4 | April | `thunder` | `thunder` | `thunder` | `thunder` |
| 5 | May | `thunder` | `sun-cloud` | `rain` | `rain` |
| 6 | June | `sun` | `sun` | `rain` | `rain` |
| 7 | July | `sun` | `sun` | `rain` | `rain` |
| 8 | August | `sun` | `sun` | `sun-cloud` | `sun` |

---

## 5. Pests & Diseases (Canonical snake_case + Verbatim Text Audit)

- **Dedicated Tile Paths**:
  - Irrigated: [`data-source/tiles/paddy_irrigated/07_pests_diseases_full.png`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/paddy_irrigated/07_pests_diseases_full.png)
  - Rainfed: [`data-source/tiles/paddy_rainfed/07_pests_diseases_full.png`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/paddy_rainfed/07_pests_diseases_full.png)
  - Wet Zone: [`data-source/tiles/paddy_wet/07_pests_diseases.png`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/paddy_wet/07_pests_diseases.png)

### 5.1 Wet Zone Column Boundary Audit (November vs December)
![Wet Zone Column Boundary Overlay](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/scratch/wet_nov_dec_boundary_overlay.png)

Inspection of [`scratch/wet_nov_dec_boundary_overlay.png`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/scratch/wet_nov_dec_boundary_overlay.png) with red vertical column boundary overlays confirms that:
- **November (Month 11)** strictly contains **5 pests** (and zero text from December):
  1. `canonical_name`: `thrips` | `verbatim_text`: `Thrips`
  2. `canonical_name`: `gall_midge` | `verbatim_text`: `Gall midge`
  3. `canonical_name`: `leaf_rolling_caterpillar` | `verbatim_text`: `Leaf rolling caterpiller`
  4. `canonical_name`: `stem_borer` | `verbatim_text`: `Stem borer`
  5. `canonical_name`: `white_backed_planthopper` | `verbatim_text`: `White back hopper`
- **December (Month 12)** strictly contains **7 pests** (and zero text from January):
  1. `canonical_name`: `leaf_rolling_caterpillar` | `verbatim_text`: `Leaf rolling caterpiller`
  2. `canonical_name`: `stem_borer` | `verbatim_text`: `Stem borer`
  3. `canonical_name`: `brown_planthopper` | `verbatim_text`: `Brown plant hopper`
  4. `canonical_name`: `white_backed_planthopper` | `verbatim_text`: `White back hopper`
  5. `canonical_name`: `sheath_and_leaf_mites` | `verbatim_text`: `Sheath & leaf mites`
  6. `canonical_name`: `rice_blast` | `verbatim_text`: `Blast`
  7. `canonical_name`: `bacterial_sheath_blight` | `verbatim_text`: `Bacterial sheath blight`
- **May (Month 5)** check:
  - Confirmed against tile: printed verbatim as `"Thips"` (missing 'r').
  - Stored in JSON: `{ "canonical_name": "thrips", "verbatim_text": "Thips" }`.

### 5.2 All Three Tiles Re-Checked for Neighboring Column Leaks
- **Irrigated Sheet**: Every month bounded strictly by Month column grid lines. October has 1 pest; November has 2; December has 8; January has 8; February has 2; April has 1; May has 2; June has 8; July has 5; August has 2.
- **Rainfed Sheet**: Bounded strictly. January includes verbatim `"Brown plant hoper"`, `"Blast,"`, and `"Bacteria sheath blights"`. August includes verbatim `"Pady bug"`.
- **Wet Sheet**: Bounded strictly. November has 5 pests; December has 7 pests; January has 6 pests; May has `"Thips"`.

---

## 6. Grid Timing, Harvest Month, & Durations Cleanup

1. **Harvest Month Only**:
   - `original_grid_position` for `harvesting` stores month only: `{ "maha_month": 2, "yala_month": 8 }`.
   - All weekly staggering (`weeks: [1]`, `weeks: [2]`, `weeks: [3]`) removed.
   - Marked with `verified: true`, `hint: false`.

2. **Planting Positions**:
   - Marked explicitly as `hint: true`, `verified: false` across all operations and `season_windows`.

3. **Duration Days & Tolerance**:
   - Stored with `duration_days` and `tolerance_days: 5`:
     - `2 1/2 Month`: `duration_days: 80`, `tolerance_days: 5`
     - `3 Month`: `duration_days: 90`, `tolerance_days: 5`
     - `3 1/2 Month`: `duration_days: 105`, `tolerance_days: 5`
     - `4 - 4 1/2 Month`: `duration_days: { "min": 120, "max": 135 }`, `tolerance_days: 5`

4. **Fertilizer Timing**:
   - Retains only printed days or weeks after broadcasting and planting (`timing_schemes`).

---

## 7. Validation Execution & Status

Ran validation script `node scripts/validate_calendars.js`:
- [dry-intermediate-irrigated.json](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/paddy/dry-intermediate-irrigated.json): ✅ **PASS**
- [dry-intermediate-rainfed.json](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/paddy/dry-intermediate-rainfed.json): ✅ **PASS** (3 acknowledged discrepancy warnings logged for printed total MOP 20 vs row sum 24)
- [wet.json](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/paddy/wet.json): ✅ **PASS**
- [ipm.json](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/paddy/ipm.json): ✅ **PASS**

All files in `src/data/calendars/paddy/` and mirrored copies in `profit_engine/frontend/src/data/calendars/paddy/` are synchronized and verified.

---

## 8. Big Onion Extraction & Audit (Dry & Intermediate Zone)

- **Source Image**: `data-source/rgb/Big Onion/BIg-onion-Dry-Inter-E.png` (2415 × 1785)
- **Tile Directory**: `data-source/tiles/big_onion/` (12 high-resolution tiles generated)
- **Verbatim Transcript**: [`data-source/transcripts/big_onion_dry_intermediate.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/big_onion_dry_intermediate.md)
- **Calendar JSON**: [`src/data/calendars/big-onion/dry-intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/big-onion/dry-intermediate.json)
- **Mirrored Frontend**: [`profit_engine/frontend/src/data/calendars/big-onion/dry-intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/big-onion/dry-intermediate.json)
- **Overrides Registry**: [`overrides/big_onion.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/overrides/big_onion.json) & [`src/data/overrides/big_onion.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/overrides/big_onion.json)

### 8.1 Key Audit Verifications

1. **Cultivation Scenarios**:
   - `main`: Main season bulb cultivation (Yala). Start nursery March 15; field planting April W4–May W2; harvest July–October (printed target: 20th October).
   - `off_season`: Off-season bulb cultivation (Maha). Nursery Dec W3–Jan W2; field planting Jan W4–Feb W1; stop irrigation 2 weeks before harvest; harvest April–June.
   - `true_seed`: True seed production across two cycles (Maha: bulb selection in Nov, planting Jan, seed harvest March; Yala: planting late April, seed harvest July). Includes vernalisation (10–15 °C for 2 weeks in Riverston, Sita-Eliya, Rahangala), polythene shelter, and pollination window (10:00 AM – 2:00 PM).

2. **Varieties & Yield**:
   - Exactly 8 varieties transcribed: `Kalpitiya Selection`, `Pusa Red`, `Rampur`, `Nasic Red`, `N 53`, `Asrifound Light Red`, `Dambulla Selection`, `Galewela Selection`.
   - Ground truth yield printed in Cost of Production table: `8800 kg/ac` (selling price Rs. 70.00/kg).

3. **Fertilizer Schedule & Ground Truth**:
   - Field Cultivation (kg/ac):
     - Basal Dressing: Urea 26, TSP 40, MOP 20.
     - Top Dressing 1 (2 WAP): Urea 26.
     - Top Dressing 2 (5–6 WAP): Urea 26, MOP 10.
     - Special note: Kalpitiya: Apply 150 kg of Ammonium Sulphate instead of Urea.
   - Nursery (per 300 cm × 75 cm × 15 cm bed):
     - Basal Dressing: Urea 15 g, TSP 30 g, MOP 15 g.
     - Top Dressing (2 WAP): Urea 15 g.
   - Total Row: *No Total row is printed on the tile.* Application rows sum to 78 Urea, 40 TSP, 30 MOP (cultivation kg/ac) and are stored in `derived` block to strictly avoid inventing unprinted total rows.

4. **Pests & Diseases Boundary Check**:
   - Bounded strictly against Month column grid lines:
     - December to June: exactly 5 pests per month (`purple_blotch`, `anthracnose`, `fungal_bulb_rot`, `bacterial_bulb_rot`, `big_onion_caterpillar`).
     - November, July, August, September, October: completely empty. Zero neighbouring column leakage.

5. **Weather (h1, h2)**:
   - November: `rain`, `rain`
   - December: `rain`, `rain`
   - January: `rain`, `sun-rain`
   - February: `sun`, `sun`
   - March: `sun`, `thunder`
   - April: `thunder`, `thunder`
   - May: `rain`, `sun-cloud`
   - June, July, August: `sun`, `sun`
   - September: `sun-cloud`, `sun`
   - October: `rain`, `rain`

6. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0).

---

## 9. Black Gram Extraction & Audit (Dry & Intermediate Zones)

- **Source Images**:
  - Dry Zone: `data-source/rgb/Black Gram/Blackgram_DRY.png` (1725 × 1275)
  - Intermediate Zone: `data-source/rgb/Black Gram/Blackgram_INTER.png` (1725 × 1275)
- **Tile Directories**:
  - Dry Zone: [`data-source/tiles/black_gram_dry/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/black_gram_dry) (10 clean tiles)
  - Intermediate Zone: [`data-source/tiles/black_gram_inter/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/black_gram_inter) (10 clean tiles)
- **Verbatim Transcripts**:
  - Dry Zone: [`data-source/transcripts/black_gram_dry.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/black_gram_dry.md)
  - Intermediate Zone: [`data-source/transcripts/black_gram_intermediate.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/black_gram_intermediate.md)
- **Calendar JSON Files**:
  - Dry Zone: [`src/data/calendars/black-gram/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/black-gram/dry.json)
  - Intermediate Zone: [`src/data/calendars/black-gram/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/black-gram/intermediate.json)
- **Frontend Mirrored Files**:
  - Dry Zone: [`profit_engine/frontend/src/data/calendars/black-gram/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/black-gram/dry.json)
  - Intermediate Zone: [`profit_engine/frontend/src/data/calendars/black-gram/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/black-gram/intermediate.json)
- **Overrides Registry**:
  - [`overrides/black_gram.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/overrides/black_gram.json) & [`src/data/overrides/black_gram.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/overrides/black_gram.json)

### 9.1 Key Audit Verifications

1. **Cultivation Scenarios**:
   - `main`: Main seasons cultivation (Maha & Yala).
     - Maha: Land prep Oct W3–W4; Seeding & Basal Nov W1–W2; Weeding Nov W4–Dec W1; Weeding & Top dressing Dec W2–W3; Harvest Jan W1–W3 (`maha_month: 1`).
     - Yala: Land prep Mar W3–W4; Seeding & Basal Apr W1–W2; Weeding Apr W4–May W1; Weeding & Top dressing May W1–W2; Harvest Jun W1–W3 (`yala_month: 6`).
   - `third_season`:
     - Dry Zone: Direct seeding / broadcasting into stubble late March to early April (W4–W1); Harvest mid-to-late June (`yala_month: 6`).
     - Intermediate Zone: Direct seeding / broadcasting on paddy fields during early Yala season (June W2–July W2); Harvest late August to early September (`yala_month: 8`).
2. **Varieties & Durations**:
   - Exactly 2 varieties printed on both sheets:
     - `MI - 1`: Duration `90` days.
     - `Anuradha`: Duration `65-70` days.
   - Seed rate: `12 kg/ac (30 kg/ha)`.
   - Spacing: `60 x 10 cm`.
   - Average yield from cost table: `465 kg/ac` (selling price Rs. 150.00/kg).
3. **Fertilizer Schedule (Ground Truth)**:
   - Basal Dressing: Urea `14 kg/ac`, TSP `40 kg/ac`, MOP `30 kg/ac`.
   - Top Dressing: Urea `12 kg/ac` (applied with second weeding).
   - No Total row is printed on the table; row sums (26 Urea, 40 TSP, 30 MOP) are recorded in `derived.computed_fertilizer_sums_kg_ac`.
4. **Pests & Diseases Boundary Check**:
   - Checked strictly against Month column grid lines:
     - October: `collar_rot`
     - November: `anthracnose`
     - December: `anthracnose`, `collar_rot`, `powdery_mildew`
     - January: `cercospora_leaf_spot`, `anthracnose`, `powdery_mildew`, `pod_borer`, `mosaic_virus`, `whitefly`, `collar_rot`
     - February: `mosaic_virus`, `whitefly`, `aphids`, `mites`, `leafhopper`
     - April: `collar_rot`
     - May: `collar_rot`, `mosaic_virus`, `bean_fly`
     - June: `cercospora_leaf_spot`, `anthracnose`, `collar_rot`, `bean_fly`, `mosaic_virus`, `pod_borer`, `blister_beetle`, `aphids`, `leafhopper`, `mites`
     - July: `bruchids`
     - September, March, August: completely empty. Zero neighbouring column leakage.
5. **Weather (`h1`, `h2`)**:
   - Dry Zone: Sep: `sun-cloud`, `rain` | Oct–Dec: `rain`, `rain` | Jan: `rain`, `sun-rain` | Feb: `sun`, `sun` | Mar: `sun`, `thunder` | Apr: `thunder`, `thunder` | May: `rain`, `sun-rain` | Jun–Aug: `sun`, `sun`
   - Intermediate Zone: Sep: `sun-cloud`, `rain` | Oct–Dec: `rain`, `rain` | Jan: `rain`, `sun` | Feb: `sun`, `sun` | Mar: `sun`, `rain` | Apr: `thunder`, `thunder` | May: `rain`, `rain` | Jun: `sun`, `sun-cloud` | Jul–Aug: `sun-cloud`, `sun-cloud`
6. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0).

---

## 10. Chilli Extraction & Audit (Dry, Intermediate, & Wet Zones)

- **Source Images**:
  - Dry Zone: `data-source/rgb/Chilli/Chilli_Dry.png` (2415 × 1785)
  - Intermediate Zone: `data-source/rgb/Chilli/inter-chilli-english.png` (2415 × 1785)
  - Wet Zone: `data-source/rgb/Chilli/Chili_wet.png` (2415 × 1785)
- **Tile Directories**:
  - Dry Zone: [`data-source/tiles/chilli_dry/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/chilli_dry) (10 clean tiles)
  - Intermediate Zone: [`data-source/tiles/chilli_inter/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/chilli_inter) (10 clean tiles)
  - Wet Zone: [`data-source/tiles/chilli_wet/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/chilli_wet) (10 clean tiles)
- **Verbatim Transcripts**:
  - Dry Zone: [`data-source/transcripts/chilli_dry.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/chilli_dry.md)
  - Intermediate Zone: [`data-source/transcripts/chilli_intermediate.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/chilli_intermediate.md)
  - Wet Zone: [`data-source/transcripts/chilli_wet.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/chilli_wet.md)
- **Calendar JSON Files**:
  - Dry Zone: [`src/data/calendars/chilli/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/chilli/dry.json)
  - Intermediate Zone: [`src/data/calendars/chilli/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/chilli/intermediate.json)
  - Wet Zone: [`src/data/calendars/chilli/wet.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/chilli/wet.json)
- **Frontend Mirrored Files**:
  - Dry Zone: [`profit_engine/frontend/src/data/calendars/chilli/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/chilli/dry.json)
  - Intermediate Zone: [`profit_engine/frontend/src/data/calendars/chilli/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/chilli/intermediate.json)
  - Wet Zone: [`profit_engine/frontend/src/data/calendars/chilli/wet.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/chilli/wet.json)
- **Overrides Registry**:
  - [`overrides/chilli.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/overrides/chilli.json) & [`src/data/overrides/chilli.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/overrides/chilli.json)

### 10.1 Key Audit Verifications

1. **Cultivation Scenarios & Timelines**:
   - **Dry & Intermediate Zones** (`main`):
     - Maha: Nursery Sep W3–Oct W2; Land prep Oct W1–W2; Planting Oct W3–Nov W1 (`plant_from: 10/W3`, `plant_to: 11/W1`); Green chilli harvest Dec W3–Jan W4 (`maha_month: 1`); Dry chilli harvest Jan W2–Feb W2/W3 (`maha_month: 2`).
     - Yala: Nursery Feb W4–Mar W3; Land prep Mar W3–Apr W1; Planting Apr W1–W3 (`plant_from: 4/W1`, `plant_to: 4/W3`); Green chilli harvest May W4–Jun W4 (`yala_month: 6`); Dry chilli harvest Jun W3–Aug W1 (`yala_month: 7`).
   - **Wet Zone** (`main` - Alternative Cropping Time table):
     - Cycle 1 (Maha Cultivation): Nursery Dec W3–Jan W2; Land prep Jan W1–W2; Planting Jan W2–W4 (`plant_from: 1/W2`, `plant_to: 1/W4`); Green chilli harvest Mar W3–Apr W2 (`maha_month: 3`); Dry chilli harvest Apr W1–May W1 (`maha_month: 4`).
     - Cycle 2 (Yala Cultivation): Nursery Apr W3–May W2; Land prep May W1–W2; Planting May W2–W4 (`plant_from: 5/W2`, `plant_to: 5/W4`); Green chilli harvest Jul W3–Aug W2 (`yala_month: 7`); Dry chilli harvest Aug W1–Aug W4 (`yala_month: 8`).
2. **Varieties & Durations**:
   - Exactly 6 varieties across 2 spacing groups:
     - Group 1: `M.I 2`, `K.A 2` (Spacing: Two plants per hole `60 cm x 45 cm`).
     - Group 2: `M.I. Green`, `Galkiriyagama Selection`, `I Veraniya 01` (or `I veraniya 01`), `M.I.C.H -3` (Spacing: Two plants per hole `60 cm x 60 cm`).
   - Seed requirement: `400 g /ac`.
   - Standard yield printed: `4000 kg/ha` (or 4000 kg/ac), Selling price: `Rs. 90.00/kg`.
3. **Fertilizer Schedule (Ground Truth)**:
   - Basal Dressing: Urea null, TSP `40 kg/ac`, MOP `20 kg/ac` (applied 3 days before planting).
   - Top Dressing 1 (2 WAP): Urea `50 kg/ac`.
   - Top Dressing 2 (4 WAP): Urea `50 kg/ac`.
   - Top Dressing 3 (8 WAP): Urea `50 kg/ac`, MOP `20 kg/ac`.
   - Top Dressing 4 (12 WAP): Urea `50 kg/ac`.
   - Top Dressing 5 (16 WAP): Urea `50 kg/ac`.
   - No Total row printed on poster; row sums (250 Urea, 40 TSP, 40 MOP) strictly recorded in `derived.computed_fertilizer_sums_kg_ac`.
4. **Pests & Diseases Boundary Check**:
   - Checked strictly against Month column grid lines to prevent neighbouring column leakage:
     - Sep: `damping_off`
     - Oct: blank
     - Nov: `virus`, `damping_off`, `anthracnose`, `leaf_spot`, `choanephora_blight` (in Wet: `damping_off`, `anthracnose`, `leaf_spot`, `choanephora_blight`)
     - Dec: `virus`, `damping_off`, `anthracnose`
     - Jan: Dry & Wet blank; Inter has `leaf_spot`, `anthracnose`, `choanephora_blight`, `pod_borer`
     - Feb: `whitefly`, `mites`, `thrips`, `aphids` (Dry: `aphids`, `whitefly`, `mites`, `thrips`; Inter: `chilli_leaf_curl_complex`, `whitefly`, `mites`, `thrips`)
     - Mar: Dry blank; Inter has `whitefly`, `mites`, `aphids`, `thrips`, `damping_off`; Wet has `aphids`, `whitefly`, `mites`, `thrips`
     - Apr: `chilli_leaf_curl_complex` (Inter/Wet also have `bacterial_wilt`)
     - May: `chilli_leaf_curl_complex`, `collar_rot`
     - Jun: blank
     - Jul: `virus`, `chilli_leaf_curl_complex` (Inter also has `whitefly`, `aphids`, `thrips`, `collar_rot`)
     - Aug: blank
5. **Weather (`h1`, `h2`)**:
   - Dry Zone: Sep: `sun-cloud`, `rain` | Oct–Dec: `rain`, `rain` | Jan: `rain`, `sun-rain` | Feb: `sun`, `sun` | Mar: `sun`, `thunder` | Apr: `thunder`, `thunder` | May: `rain`, `sun-cloud` | Jun–Aug: `sun`, `sun`
   - Intermediate Zone: Sep: `sun-cloud`, `rain` | Oct–Dec: `rain`, `rain` | Jan: `rain`, `sun-rain` | Feb: `sun`, `sun` | Mar: `sun`, `thunder` | Apr: `thunder`, `thunder` | May: `rain`, `rain` | Jun: `sun`, `sun-cloud` | Jul–Aug: `sun-cloud`, `sun-cloud`
   - Wet Zone: Sep: `sun-cloud`, `rain` | Oct–Dec: `rain`, `rain` | Jan: `rain`, `sun-rain` | Feb: `sun`, `sun` | Mar: `sun`, `thunder` | Apr: `thunder`, `thunder` | May–Jul: `rain`, `rain` | Aug: `sun-cloud`, `sun`
6. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0, all 10 calendar JSON files validated).

---

## 11. Cowpea Extraction & Audit (Dry & Intermediate Zones)

- **Source Images**:
  - Dry Zone: `data-source/rgb/Cowpea/Cowpea_DRY.png` (1725 × 1275)
  - Intermediate Zone: `data-source/rgb/Cowpea/Cowpea_INTER.png` (1725 × 1275)
- **Tile Directories**:
  - Dry Zone: [`data-source/tiles/cowpea_dry/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/cowpea_dry) (10 clean tiles)
  - Intermediate Zone: [`data-source/tiles/cowpea_inter/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/cowpea_inter) (10 clean tiles)
- **Verbatim Transcripts**:
  - Dry Zone: [`data-source/transcripts/cowpea_dry.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/cowpea_dry.md)
  - Intermediate Zone: [`data-source/transcripts/cowpea_intermediate.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/cowpea_intermediate.md)
- **Calendar JSON Files**:
  - Dry Zone: [`src/data/calendars/cowpea/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/cowpea/dry.json)
  - Intermediate Zone: [`src/data/calendars/cowpea/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/cowpea/intermediate.json)
- **Frontend Mirrored Files**:
  - Dry Zone: [`profit_engine/frontend/src/data/calendars/cowpea/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/cowpea/dry.json)
  - Intermediate Zone: [`profit_engine/frontend/src/data/calendars/cowpea/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/cowpea/intermediate.json)
- **Overrides Registry**:
  - [`overrides/cowpea.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/overrides/cowpea.json) & [`src/data/overrides/cowpea.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/overrides/cowpea.json)

### 11.1 Key Audit Verifications

1. **Cultivation Scenarios & Timelines**:
   - `main`: Main seasons cultivation (Maha & Yala).
     - Maha: Land prep, Seeding & Basal Nov W1–W2 (`plant_from: 11/W1`, `plant_to: 11/W2`); Weed control Nov W3; Weed control & Top dressing Nov W4; Harvest mature pods Dec W3–W4 (`maha_month: 12`).
     - Yala: Land prep, Seeding & Basal Apr W1–W2 (`plant_from: 4/W1`, `plant_to: 4/W2`); Weed control Apr W3; Weed control & Top dressing Apr W4; Harvest mature pods May W3–W4 (`yala_month: 5`).
   - `third_season`: Third season / paddy stubble cultivation.
     - Direct seeding into paddy stubble March W3–April W1 (`plant_from: 3/W3`, `plant_to: 4/W1`, printed note: *Paddy fields are not cultivated in Yala season*); Harvest May W2–W3 (`yala_month: 5`).
     - Early cultivation cycle in paddy fields during Yala: sowing July W3–W4, harvest September W1–W2.
2. **Varieties & Durations**:
   - Exactly 5 varieties printed:
     - `MI -35`: Duration `65-80` days.
     - `Dhawala`: Duration `60-70` days.
     - `Waruni`: Duration `55` days.
     - `Bombe`: Duration `75-90` days.
     - `MICP`: Duration `60-70` days.
   - Seed rate: `14-16 kg/ac (35-40 kg/ha)`.
   - Spacing: `30 x 15 cm`.
   - Printed yield from cost table: `380-400 kg/ac` (selling price `Rs. 135.00/kg`, gross income `Rs. 54,000.00`).
3. **Fertilizer Schedule (Ground Truth)**:
   - Basal Dressing: Urea `14 kg/ac`, TSP `40 kg/ac`, MOP `30 kg/ac`.
   - Top Dressing: Urea `12 kg/ac` (applied during Nitrogen deficiency with second weed control).
   - No Total row printed on table; row sums (26 Urea, 40 TSP, 30 MOP) strictly recorded in `derived.computed_fertilizer_sums_kg_ac`.
4. **Pests & Diseases Boundary Check**:
   - Checked strictly against Month column grid lines:
     - Sep, Oct: completely empty.
     - Nov: `collar_rot`.
     - Dec: `cercospora_leaf_spot`, `anthracnose`, `powdery_mildew`, `ascochyta_blight`, `collar_rot`, `pod_borer`, `wilt`.
     - Jan: `cercospora_leaf_spot`, `anthracnose`, `powdery_mildew`, `ascochyta_blight`, `collar_rot`, `pod_borer`, `wilt`.
     - Feb: `aphids`, `whitefly`, `planthopper`, `mites`, `leafhopper` (printed advice: *The pest attacks can be reduced by harvesting at the end of January*).
     - Mar: completely empty.
     - Apr: `collar_rot`.
     - May: `collar_rot`, `anthracnose`, `mosaic_virus`, `ascochyta_blight`, `bean_fly`.
     - Jun: `mosaic_virus`, `ascochyta_blight`, `bean_fly`, `pod_borer`, `pod_sucking_bug`, `blister_beetle`, `aphids`, `mites`.
     - Jul: `mosaic_virus`, `ascochyta_blight`, `bean_fly`, `pod_borer`, `pod_sucking_bug`, `blister_beetle`, `aphids`, `mites` (printed advice: *The pest attacks can be reduced by harvesting at the end of June*).
     - Aug: completely empty.
5. **Weather (`h1`, `h2`)**:
   - Both Dry & Intermediate Zones:
     - Sep: `sun-cloud`, `rain`
     - Oct–Dec: `rain`, `rain`
     - Jan: `rain`, `sun`
     - Feb: `sun`, `sun`
     - Mar: `sun`, `thunder`
     - Apr: `thunder`, `thunder`
     - May: `thunder`, `rain`
     - Jun: `rain`, `sun-cloud`
     - Jul–Aug: `sun-cloud`, `sun-cloud`
6. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0, all 12 calendar JSON files validated).

---

## 12. Finger Millet Extraction & Audit (Dry & Intermediate Zones)

- **Source Image**: `data-source/rgb/Finger Millet/fingerMillet_dryinter-1024x757.png` (1024 × 757)
- **Tile Directory**: [`data-source/tiles/finger_millet/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/finger_millet) (11 clean tiles)
- **Verbatim Transcript**: [`data-source/transcripts/finger_millet_dry_intermediate.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/finger_millet_dry_intermediate.md)
- **Calendar JSON File**: [`src/data/calendars/finger-millet/dry-intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/finger-millet/dry-intermediate.json)
- **Frontend Mirrored File**: [`profit_engine/frontend/src/data/calendars/finger-millet/dry-intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/finger-millet/dry-intermediate.json)
- **Overrides Registry**: [`overrides/finger_millet.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/overrides/finger_millet.json) & [`src/data/overrides/finger_millet.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/overrides/finger_millet.json)

### 12.1 Key Audit Verifications

1. **Cultivation Scenarios & Timelines**:
   - `main`: Main seasons cultivation (Maha & Yala).
     - Maha: Land prep, Seeding & Basal Oct W1–W2 (`plant_from: 10/W1`, `plant_to: 10/W2`); Weed control & Top dressing Oct W3–Nov W1; Harvest mature heads Dec W1–Jan W2 (`maha_month: 1`).
     - Yala: Land prep, Seeding & Basal Apr W1–W2 (`plant_from: 4/W1`, `plant_to: 4/W2`); Weed control & Top dressing Apr W3–May W1; Harvest mature heads Jun W1–Jul W2 (`yala_month: 7`).
   - Month Order on Printed Poster: Printed starting with **March** and ending with **February**.
2. **Varieties & Durations**:
   - Exactly 3 varieties printed: `Ravi`, `Ravana`, `Oshadi` (resistant to blast).
   - Duration in days is not printed in the table (set to null, strictly avoiding interpolation).
   - Seed rate: `Seeding 8kg/ac`, `Cultivate on rows 3-5 kg/ac`.
   - Spacing: `30 X 10-15 cm`.
   - Yield from Cost of Production table: `530 kg/ac`, Selling price: `Rs. 80.00/kg` (printed as *Selling Pice/ kg*).
3. **Fertilizer Schedule (Ground Truth)**:
   - Header specifies `Fertilizing kg/ha` (Basal Dressing: Urea 65, TSP 55, MOP 82.5 kg/ha).
   - Converted to kg/ac (26.3 Urea, 22.3 TSP, 33.4 MOP kg/ac) for operational fields, with exact kg/ha values documented in `derived`.
   - No Total row is printed; row values recorded directly.
4. **Pests & Diseases Boundary Check**:
   - Checked strictly against Month column grid lines:
     - Mar, Apr, May: completely empty.
     - Jun: `stem_borer`, `aphids`.
     - Jul, Aug, Sep, Oct: completely empty.
     - Nov: `blast`.
     - Dec: completely empty.
     - Jan: `blast`, `stem_borer`, `brown_spot`, `erwinia_collar_rot` (printed as *Arvinia Collar rot*).
     - Feb: completely empty.
5. **Weather (`h1`, `h2`)**:
   - Stored in calendar order (Jan–Dec):
     - Jan: `rain`, `rain`
     - Feb: `sun-rain`, `sun`
     - Mar: `sun`, `thunder`
     - Apr: `thunder`, `rain`
     - May: `rain`, `sun-rain`
     - Jun: `sun-rain`, `sun`
     - Jul–Aug: `sun`, `sun`
     - Sep: `sun-cloud`, `sun-cloud`
     - Oct–Dec: `rain`, `rain`
6. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0, all 13 calendar JSON files validated).

---

## 13. Green Gram Extraction & Audit (Dry & Intermediate Zones)

- **Source Images**:
  - Dry Zone: `data-source/rgb/Green Gram/GreenGram_DRY.png` (1725 × 1275)
  - Intermediate Zone: `data-source/rgb/Green Gram/GreenGram_INTER.png` (1725 × 1275)
- **Tile Directories**:
  - Dry Zone: [`data-source/tiles/green_gram_dry/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/green_gram_dry) (11 clean tiles)
  - Intermediate Zone: [`data-source/tiles/green_gram_inter/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/green_gram_inter) (11 clean tiles)
- **Verbatim Transcripts**:
  - Dry Zone: [`data-source/transcripts/green_gram_dry.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/green_gram_dry.md)
  - Intermediate Zone: [`data-source/transcripts/green_gram_intermediate.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/green_gram_intermediate.md)
- **Calendar JSON Files**:
  - Dry Zone: [`src/data/calendars/green-gram/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/green-gram/dry.json)
  - Intermediate Zone: [`src/data/calendars/green-gram/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/green-gram/intermediate.json)
- **Frontend Mirrored Files**:
  - Dry Zone: [`profit_engine/frontend/src/data/calendars/green-gram/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/green-gram/dry.json)
  - Intermediate Zone: [`profit_engine/frontend/src/data/calendars/green-gram/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/green-gram/intermediate.json)
- **Overrides Registry**:
  - [`overrides/green_gram.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/overrides/green_gram.json) & [`src/data/overrides/green_gram.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/overrides/green_gram.json)

### 13.1 Key Audit Verifications

1. **Cultivation Scenarios & Timelines**:
   - `main`: Main seasons cultivation (Maha & Yala).
     - Maha: Land prep Oct W3–W4; Seeding & Basal Nov W1–W2 (`plant_from: 11/W1`, `plant_to: 11/W2`); Weed control & Top dressing Dec W1–W2; Harvest Jan W3–Feb W1 (`maha_month: 1`).
     - Yala: Land prep Mar W4–Apr W1; Seeding & Basal Apr W2–W3 (`plant_from: 4/W2`, `plant_to: 4/W3`); Weed control & Top dressing May W1–W2; Harvest Jun W4–Jul W1 (`yala_month: 6`).
   - `third_season`: Third season / Mid-season cultivation in paddy fields (`plant_from: 3/W4`, `plant_to: 4/W2`, harvest in June/July).
   - Calendar timeline order on printed poster: Starts with **September** and ends with **August**.
2. **Varieties & Durations**:
   - Exactly 4 varieties printed:
     - `MI -5`: Duration `60-65` days, Yield `1500 kg/ha` (~607 kg/ac).
     - `Ari`: Duration `60-65` days, Yield `1600 kg/ha` (~648 kg/ac).
     - `Harsha`: Duration `55-60` days, Yield `1200 kg/ha` (~486 kg/ac).
     - `MI-6`: Duration `55-58` days, Yield `1800 kg/ha` (~728 kg/ac; printed note: *Suitable for mid-season cultivation*).
   - Seed rate: `30 kg/ha` (~12 kg/ac; cost of cultivation table lists `Seed 12 kg x Rs.265/=` for 1 acre).
   - Spacing: `30 x 10 cm` and `60 x 10 cm`.
   - Yield from Cost table: `400 kg/ac`, Selling price: `Rs. 170.00/kg`, Gross income: `Rs. 68,000.00`.
3. **Fertilizer Schedule (Ground Truth)**:
   - Table header explicitly states: `Fertilizer Requirement kg/ha`.
   - Basal Dressing: Urea `30`, TSP `100`, MOP `75 kg/ha`.
   - Top Dressing: Urea `35 kg/ha`.
   - Converted to operational kg/ac: Basal 12.1 Urea, 40.5 TSP, 30.4 MOP; Top 14.2 Urea.
   - No Total row is printed; row sums (26.3 Urea, 40.5 TSP, 30.4 MOP kg/ac) preserved in `derived.computed_fertilizer_sums_kg_ac`.
4. **Cost of Production Table & Printed Labels**:
   - `Including Family Labour 11 x Rs.800/=` = `8800.00` (represents hired-only labour; total expenditure `16480.00`, gross profit `51520.00`).
   - `Excluding Family Labour 30 x Rs.800/=` = `24000.00` (represents all labour including family labour; total expenditure `31680.00`, gross profit `36320.00`).
   - Both printed values and arithmetic are preserved verbatim.
5. **Pests & Diseases Boundary Check**:
   - Checked strictly against Month column grid lines:
     - Sep, Oct: completely empty.
     - Nov: `cercospora_brown_spot`, `anthracnose_brown_spot`.
     - Dec: `cercospora_brown_spot`, `anthracnose_brown_spot`, `powdery_mildew`, `pod_sucking_bug`.
     - Jan: `cercospora_brown_spot`, `anthracnose_brown_spot`, `powdery_mildew`, `pod_sucking_bug`, `whitefly`.
     - Feb: `aphids`, `whitefly`, `mites`, `leafhopper`, `planthopper`.
     - Mar: completely empty.
     - Apr: `collar_rot`.
     - May: `collar_rot`, `mung_bean_mosaic_virus`, `bean_fly`.
     - Jun: `collar_rot`, `mung_bean_mosaic_virus`, `bean_fly`, `pod_sucking_bug`, `blister_beetle`, `pod_borer`, `leafhopper`, `aphids`, `mites`.
     - Jul: `bruchid`.
     - Aug: completely empty.
6. **Weather (`h1`, `h2`)**:
   - Dry Zone:
     - Sep: `sun-cloud`, `rain`
     - Oct–Dec: `rain`, `rain`
     - Jan: `rain`, `sun-rain`
     - Feb: `sun`, `sun`
     - Mar: `sun`, `thunder`
     - Apr: `thunder`, `thunder`
     - May: `rain`, `rain`
     - Jun: `sun-cloud`, `sun`
     - Jul–Aug: `sun`, `sun`
   - Intermediate Zone:
     - Sep: `sun-cloud`, `rain`
     - Oct–Dec: `rain`, `rain`
     - Jan: `rain`, `sun`
     - Feb: `sun`, `sun`
     - Mar: `sun`, `thunder`
     - Apr: `thunder`, `thunder`
     - May: `thunder`, `rain`
     - Jun: `rain`, `sun-cloud`
     - Jul: `sun-cloud`, `sun-cloud`
     - Aug: `sun-cloud`, `sun`
7. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0, all 15 calendar JSON files validated).

---

## 14. Ground Nut Extraction & Audit (Intermediate & Dry Zones)

- **Source Image**: `data-source/rgb/Ground Nut/groundNut.png` (1725 × 1275)
- **Tile Directory**: [`data-source/tiles/ground_nut/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/ground_nut) (11 clean tiles)
- **Verbatim Transcript**: [`data-source/transcripts/ground_nut_dry_intermediate.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/ground_nut_dry_intermediate.md)
- **Calendar JSON File**: [`src/data/calendars/ground-nut/dry-intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/ground-nut/dry-intermediate.json)
- **Frontend Mirrored File**: [`profit_engine/frontend/src/data/calendars/ground-nut/dry-intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/ground-nut/dry-intermediate.json)
- **Overrides Registry**: [`overrides/ground_nut.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/overrides/ground_nut.json) & [`src/data/overrides/ground_nut.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/overrides/ground_nut.json)

### 14.1 Key Audit Verifications

1. **Combined Agro-Ecological Scope & Region Listing**:
   - Single combined poster titled: `GROUNDNUT - Arachis hypogaea`, `INTERMEDIATE & DRY ZONES`.
   - Regions extracted verbatim from top banner:
     - `Kurunegala DL-1`, `Puttalam IL-1, DL-1, DL-3`, `Polonnaruwa DL-1`, `Badulla IL-2, DL-1`, `Ampara DL-2a, DL-2b`, `Hambantota DL-1, DL-5`, `Trincomalee DL-1c`, `Matale DL`, `Ratnapura IL-1`, `Batticaloa DL-2a`, `Monaragala IL-1, DL-1`, `Vavuniya DL-1, DL-1d`, `Kilinochchi DL-4`, `Mullaitivu DL-1`, `Anuradhapura DL-1d`, `Mahaweli System 'C'`.
2. **Cultivation Scenarios & Timelines**:
   - `main`: Main seasons cultivation (Maha & Yala).
     - Maha: Land prep, Seeding, Basal Oct W1–W4 (`plant_from: 10/W1`, `plant_to: 10/W4`); Weed control Nov W1–W4; Top dressing Dec W1–W2; Harvest Jan W3–Feb W1 (`maha_month: 1`); Drying Feb W3–Mar W1.
     - Yala: Land prep, Seeding, Basal Apr W1–W4 (`plant_from: 4/W1`, `plant_to: 4/W4`); Weed control May W1–W4; Top dressing Jun W1–W2; Harvest Jul W3–Aug W1 (`yala_month: 7`); Drying Aug W3–Sep W1.
   - Timeline order: Starts with **October** and ends with **September**.
3. **Varieties & Durations**:
   - Exactly 4 varieties printed: `Walawa`, `Indi`, `Thissa`, `Tikiri`.
   - Durations are not printed in the table; duration set to null (preventing speculative interpolation).
   - Seed rate:
     - Walawa: `With shells - 100 kg/ha` (40.5 kg/ac), `Without shells - 130 kg/ha` (52.6 kg/ac).
     - Other varieties: `70 kg/ha` (28.3 kg/ac), `Pods - 100 kg/ha` (40.5 kg/ac).
   - Spacing: `45 x 15 cm`.
   - Cost table lists: Seed `Rs. 10,200.00` (for 1 acre), Yield `700 kg/ac`, Selling Price `Rs. 180.00/kg`, Gross income `Rs. 126,000.00`.
4. **Fertilizer Schedule (Ground Truth)**:
   - Printed header: `Fertilizer Requirement kg/ha`.
   - Basic (Basal): Urea `35`, TSP `100`, MOP `75 kg/ha`.
   - Top Dressing: Urea `30 kg/ha`.
   - Operational kg/ac (divided by 2.471):
     - Basal: Urea `14.2`, TSP `40.5`, MOP `30.4 kg/ac`.
     - Top: Urea `12.1 kg/ac`.
     - Total: Urea `26.3`, TSP `40.5`, MOP `30.4 kg/ac` (retained in `derived.computed_fertilizer_sums_kg_ac`).
   - No printed totals row; verified zero artificial total rows injected.
5. **Cost of Production Table**:
   - Expenditure: Seed `10200.00`, Fertilizer `2400.00`, Chemical `3000.00`, Land preparation `6000.00`, Other `1500.00`.
   - Labour Cost: Including Family Labour `59800.00`, Excluding Family Labour `46955.00`.
   - Gross Profit:
     - Including Family Labour: `66200.00` (Income 126000 - 59800).
     - Excluding Family Labour: `79045.00` (Income 126000 - 46955).
   - All arithmetic and verbatim values documented and preserved.
6. **Pests & Diseases Boundary Check**:
   - Bounded strictly by month column grid lines:
     - Oct: completely empty.
     - Nov: `collar_rot`, `bacterial_wilt`.
     - Dec: `leaf_spot`, `rust`, `collar_rot`, `bud_rot`.
     - Jan: `leaf_spot`, `rust`, `collar_rot`, `bacterial_wilt`.
     - Feb, Mar, Apr: completely empty.
     - May: `leaf_spot`, `collar_rot`, `bacterial_wilt`.
     - Jun: `bacterial_wilt`, `collar_rot`, `bud_rot`.
     - Jul: `leaf_spot`, `rust`, `collar_rot`, `bud_rot`.
     - Aug, Sep: completely empty.
7. **Weather (`h1`, `h2`)**:
   - Jan–Feb: `sun`, `sun`
   - Mar: `sun`, `thunder`
   - Apr: `thunder`, `thunder`
   - May: `rain`, `sun-rain`
   - Jun: `sun-cloud`, `sun`
   - Jul–Aug: `sun`, `sun`
   - Sep: `sun-cloud`, `sun-cloud`
   - Oct: `thunder`, `thunder`
   - Nov: `rain`, `rain`
   - Dec: `rain`, `sun-rain`
8. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0, 16/16 calendar JSON files validated).

---

## 15. Maize Extraction & Audit (Dry & Intermediate Zones)

- **Source Images**:
  - Dry Zone: `data-source/rgb/Maize/maiz_dry.png` (1725 × 1275)
  - Intermediate Zone: `data-source/rgb/Maize/maiz_inter.png` (1725 × 1275)
- **Tile Directories**:
  - Dry Zone: [`data-source/tiles/maize_dry/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/maize_dry) (11 clean tiles)
  - Intermediate Zone: [`data-source/tiles/maize_inter/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/maize_inter) (11 clean tiles)
- **Verbatim Transcripts**:
  - Dry Zone: [`data-source/transcripts/maize_dry.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/maize_dry.md)
  - Intermediate Zone: [`data-source/transcripts/maize_intermediate.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/maize_intermediate.md)
- **Calendar JSON Files**:
  - Dry Zone: [`src/data/calendars/maize/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/maize/dry.json)
  - Intermediate Zone: [`src/data/calendars/maize/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/maize/intermediate.json)
- **Frontend Mirrored Files**:
  - Dry Zone: [`profit_engine/frontend/src/data/calendars/maize/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/maize/dry.json)
  - Intermediate Zone: [`profit_engine/frontend/src/data/calendars/maize/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/maize/intermediate.json)
- **Overrides Registry**:
  - [`overrides/maize.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/overrides/maize.json) & [`src/data/overrides/maize.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/overrides/maize.json)

### 15.1 Key Audit Verifications

1. **Dual Harvesting Timelines (Green Cobs vs Grains)**:
   - The maize poster provides distinct dual harvesting timelines for both seasons:
     - **Maha**:
       - Green Cobs: Dec W2–W3 (harvested fresh at milky dough stage).
       - Grains: Dec W4–Jan W2 (Dry) / Dec W3–Jan W2 (Intermediate) (harvested at full dry grain maturity).
     - **Yala**:
       - Green Cobs: Jun W4–Jul W1 (Dry) / Jun W3–Jul W1 (Intermediate).
       - Grains: Jul W2–W4 (Dry) / Jul W1–W3 (Intermediate).
   - Season windows:
     - Maha: Land preparation Sep W1–W2; Seeding & Basal Sep W3–W4 (`plant_from: 9/W3`, `plant_to: 9/W4`).
     - Yala: Land preparation Mar W4–Apr W1 (Dry) / Mar W3–W4 (Intermediate); Seeding & Basal Apr W1–W3 (Dry) / Mar W4–Apr W2 (Intermediate).
   - Calendar order: Starts at **September** and ends at **August**.
2. **Alternative Cropping Time Table (Row 3)**:
   - Explicitly schedules relay seeding and irrigation for pulse/oilseed alternatives (Gingelly, Cowpea, Green Gram):
     - Maha direct seeding: Jan W3–Feb W1 into standing stubble.
     - Staggered planting windows with supplemental irrigation across Dec–Jan and May–Jun.
3. **Varieties & Printed Discrepancies**:
   - 4 varieties documented:
     - `Ruwan`: Open-pollinated, 8 kg/ac (20 kg/ha), seed price Rs. 115/kg.
     - `Bhadra` (Dry) / `Badhara` (Intermediate): Open-pollinated, 8 kg/ac (20 kg/ha). Printed with letter transposition `Badhara` in Intermediate Zone poster.
     - `Aruna`: Open-pollinated, 8 kg/ac (20 kg/ha).
     - `Pacific or any other Hybrids` (Dry) / `Pasific or any other` (Intermediate): Hybrid varieties, 5–7 kg/ac (12.5–17 kg/ha). Printed as `Pasific` in Intermediate Zone poster.
   - Spacings: `60 x 30 cm` (1 plant), `60 x 60 cm` (2 plants), `80 x 15 cm` (1 plant), `75 x 18 cm` (1 plant).
   - Hybrid plant density: `55,000–75,000 Plants/ha` (printed as `550000-75000 Plants / ha` due to typographical error on poster), `22,000–30,000 Plants/ac`.
4. **Fertilizer Recommendation (Dual Unit & Dual Regime)**:
   - Printed in both `kg/ha` and `kg/ac`:
     - Basal Dressing (-3 days before planting): Urea `75 kg/ha` (`37 kg/ac`), TSP `100 kg/ha` (`50 kg/ac`), MOP `50 kg/ha` (`25 kg/ac`).
     - Top Dressing (4 weeks after planting):
       - Rain-fed: Urea `250 kg/ha` (`100 kg/ac`). Total computed: Urea 137, TSP 50, MOP 25 kg/ac.
       - Irrigated: Urea `140 kg/ha` (`56 kg/ac`). Total computed: Urea 93, TSP 50, MOP 25 kg/ac.
   - No printed totals row; values preserved in `derived.computed_fertilizer_sums_kg_ac`.
5. **Cost of Production Table & Cross-Zone Discrepancy**:
   - Total Gross Expenditure: Rain-fed `41,000.00` (Labour 24500 + Inputs 8000 + Machinery 8500); Irrigated `55,000.00` (Labour 38500 + Inputs 8000 + Machinery 8500).
   - Income Green Cobs: Yield 30,000 cobs/ac; Price Rs. 5.00–6.00/cob; Income: Rain-fed 150,000.00, Irrigated 180,000.00.
     - Gross profit Rain-fed: `109,000.00` (150,000 - 41,000).
     - Gross profit Irrigated: Printed verbatim as `180,000.00` on Dry poster (reproducing the revenue instead of profit); printed correctly as `125,000.00` on Intermediate poster (180,000 - 55,000 = 125,000.00). Both documented verbatim.
   - Income Grain: Yield Rain-fed 2,000 kg, Irrigated 3,000 kg; Selling price Rs. 30/kg; Income: Rain-fed 60,000.00, Irrigated 90,000.00.
     - Gross profit Rain-fed: `19,000.00` (60,000 - 41,000).
     - Gross profit Irrigated: `35,000.00` (90,000 - 55,000).
6. **Mechanization & Risk Advice**:
   - Mechanization note: *Mechanization reduces maize cost of cultivation around Rs. 10,000 under commercial cultivations* (seeding and top dressing injector planter coupled with 4-wheel tractor; 2-wheel tractor rotovator inter-cultivator).
   - Drought: *Irrigation requires two weeks before male flowering and few weeks after female flowering; Pest - Aphids*.
   - Flood: *Maha Season - Plant on ridges; Pest - Rust*.
7. **Pests & Diseases Boundary Check**:
   - Dry Zone:
     - Oct: `penicillium_seedling_blight`, `stem_borer`
     - Nov: `brown_leaf_spot`, `stem_borer`, `erwinia_stalk_rot`
     - Dec: `sheath_rot_blight`, `brown_leaf_spot`, `erwinia_stalk_rot`, `rust`
     - Apr: `penicillium_seedling_blight`
     - May: `aphids`, `stem_borer`, `erwinia_stalk_rot`
     - Jul: `pod_borer`
     - Jan–Mar, Jun, Aug–Sep: completely empty.
   - Intermediate Zone:
     - Oct: `stem_borer`
     - Nov: `erwinia_stalk_rot`, `stem_borer`
     - Dec: `brown_leaf_spot`, `erwinia_stalk_rot`, `rust`
     - May: `stem_borer`, `erwinia_stalk_rot`
     - Jan–Apr, Jun–Sep: completely empty.
8. **Weather (`h1`, `h2`)**:
   - Dry Zone:
     - Sep: `sun-cloud`, `rain`
     - Oct–Nov: `rain`, `rain`
     - Dec: `rain`, `sun-rain`
     - Jan–Feb: `sun`, `sun`
     - Mar: `sun`, `thunder`
     - Apr: `thunder`, `rain`
     - May: `rain`, `sun`
     - Jun–Aug: `sun`, `sun`
   - Intermediate Zone:
     - Sep: `sun-cloud`, `rain`
     - Oct–Dec: `rain`, `rain`
     - Jan–Feb: `sun`, `sun`
     - Mar: `sun`, `thunder`
     - Apr: `thunder`, `thunder`
     - May: `thunder`, `rain`
     - Jun–Aug: `sun-cloud`, `sun-cloud`
9. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0, 18/18 calendar JSON files validated).

---

## 16. Potato Extraction & Multi-Zone Audit (Dry, Intermediate & Wet Zones)

- **Source Images**:
  - Dry Zone: `data-source/rgb/Potato/POTATO_-Dry-jaffna-Kalpitiya.png` (1725 × 1275)
  - Intermediate Zone: `data-source/rgb/Potato/POTATO_-Inter-badulla.png` (1725 × 1275)
  - Wet Zone: `data-source/rgb/Potato/POTATO_Wet-Nuwaraeliya.png` (1840 × 1360)
- **Tile Directories**:
  - Dry Zone: [`data-source/tiles/potato_dry/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/potato_dry) (25 clean tiles)
  - Intermediate Zone: [`data-source/tiles/potato_inter/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/potato_inter) (26 clean tiles)
  - Wet Zone: [`data-source/tiles/potato_wet/`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/tiles/potato_wet) (26 clean tiles)
- **Verbatim Transcripts**:
  - Dry Zone: [`data-source/transcripts/potato_dry.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/potato_dry.md)
  - Intermediate Zone: [`data-source/transcripts/potato_intermediate.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/potato_intermediate.md)
  - Wet Zone: [`data-source/transcripts/potato_wet.md`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/data-source/transcripts/potato_wet.md)
- **Calendar JSON Files**:
  - Dry Zone: [`src/data/calendars/potato/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/potato/dry.json)
  - Intermediate Zone: [`src/data/calendars/potato/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/potato/intermediate.json)
  - Wet Zone: [`src/data/calendars/potato/wet.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/calendars/potato/wet.json)
- **Frontend Mirrored Files**:
  - Dry Zone: [`profit_engine/frontend/src/data/calendars/potato/dry.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/potato/dry.json)
  - Intermediate Zone: [`profit_engine/frontend/src/data/calendars/potato/intermediate.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/potato/intermediate.json)
  - Wet Zone: [`profit_engine/frontend/src/data/calendars/potato/wet.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/calendars/potato/wet.json)
- **Overrides Registry**:
  - [`overrides/potato.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/overrides/potato.json) & [`src/data/overrides/potato.json`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/src/data/overrides/potato.json)

### 16.1 Key Audit Verifications

1. **Agro-Ecological Scope & Region Listing Across 3 Zones**:
   - **Dry Zone (Jaffna & Kalpitiya)**:
     - `Jaffna DL-3`: `Kopai, Neerveli, Urumpirai, Punnaleikattuwan, Kuppulan, Chunnakam, Achchuveli, Siruppatti, Puttur`.
     - `Kalpitiya DL-3`: `Kandakkuliya, Norochchole, Palavi`.
     - System: Dedicated cool season `For Uplands` only.
   - **Intermediate Zone (Badulla)**:
     - `Badulla IU-3`: `Atampitiya, Bandarawela, Bambarapane North & North East, Boralanda, Ballaketuwa North & West, Dambavinna, Diyatalawa, Gorandiyawaka, Haldummulla North, Hali-Ela, Keppetipola East, Rambukpotha South, Uva-Paranagama, Kotawehera, Kumbalwela, Maspanne South, Nikapotha North (Except Passara East), Welimada`.
     - Dual Systems: `For Uplands` (Maha Season) and `For Paddy fields` (Yala Season).
   - **Wet Zone (Nuwara-Eliya)**:
     - `Nuwara-Eliya WU-1`: `Ginigathhena North/West, Harangala, Vidulipura`.
     - `Nuwara-Eliya WU-2`: `Helboda East, Lindula, Mandaram-Nuwara West, Maldeniya West, Nuwara-Eliya West, Pallebowala, Pundalu-Oya`.
     - `Nuwara-Eliya WU-3`: `Kandapola, Mandaram-Nuwara South, Nuwara-Eliya East`.
     - Dual Systems: `For Uplands` (Dual Season: Maha Aug–Dec & Yala Jan–Jun) and `For paddy fields` (Yala Apr–Aug).

2. **Timeline Structures & Calendar Ordering**:
   - **Dry & Intermediate Zone Posters**: Calendar begins in **October** and terminates in **September**.
     - Dry Zone Seeding: Nov W1–W2 (`plant_from: 11/W1`, `plant_to: 11/W2`); Harvesting: Jan W3–W4, Feb W2–W3, Mar W1–W2.
     - Intermediate Upland Seeding: Oct W3–W4 (`plant_from: 10/W3`, `plant_to: 10/W4`); Harvesting: Jan W4–Feb W1, Feb W4–Mar W1.
     - Intermediate Paddy Field Seeding: May W1–W3 (`plant_from: 5/W1`, `plant_to: 5/W3`); Harvesting: Jul W4–Aug W1, Aug W2–W3, Aug W4–Sep W1.
   - **Wet Zone Poster**: Calendar begins in **August** and terminates in **July** (aligned with upcountry agro-climatic conditions).
     - Wet Zone Upland Season 1 Seeding: Aug W4–Sep W1 (`plant_from: 8/W4`, `plant_to: 9/W1`); Harvesting: Nov W2–W3, Nov W4–Dec W1.
     - Wet Zone Upland Season 2 Seeding: Jan W3–W4 (`plant_from: 1/W3`, `plant_to: 1/W4`); Harvesting: May W1–W2, May W4–Jun W1.
     - Wet Zone Paddy Field Seeding: Apr W4–May W1 (`plant_from: 4/W4`, `plant_to: 5/W1`); Harvesting: Aug W1–W2.

3. **Varieties & Seed Potato Specifications**:
   - **Dry Zone (4 Varieties)**: `Calwhite`, `Redlasoda`, `Arnova`, `Desiree`.
   - **Intermediate Zone (6 Varieties)**: `Desiree (Red)`, `Granola`, `Rudolph (Red)`, `Arnova`, `Redlasoda (Red)`, `Condor`.
   - **Wet Zone (8 Varieties)**: `Granola`, `Desiree (Red)`, `Hillstar`, `Golden Star`, `Bio Gold`, `Rodulph (Red)` *(printed verbatim as Rodulph)*, `Calwhite`, `Connect`.
   - **Seed Potato Standard Rate**: `1000 kg/ac (2500 kg/ha)` across all three zones; Intermediate Zone economics table specifies `720 kg/ac`.
   - **Seed Tuber Characteristics**: `Size - 28-55 mm`, `Having more than 5-6 active suckers of 2-3 cm in height`.
   - **Spacing & Soil Amendments**:
     - Consumption: `60 x 25 cm`.
     - Seed potato: `45 x 25 cm` (Intermediate & Wet).
     - Liming: `2 tons/ha (to maintain 5-5.3 pH)` (Intermediate & Wet).
     - Organic fertilizer: `10 tons/ha` across all zones.
   - **Tuber Diameter vs Spacing Table (Wet Zone Exclusive)**:
     - `15-27 mm`: `15 cm`
     - `29-35 mm`: `25 cm`
     - `36-46 mm`: `45 cm`
     - `46-55 mm`: `60 cm`

4. **Fertilizer Schedules & Distinct Regional Regimes**:
   - **Dry Zone (Jaffna vs Kalpitiya in kg/ha)**:
     - Jaffna: Basal Urea 55, TSP 270, MOP 125; Top 2 wk Urea 110; Top 3–4 wk Urea 165, MOP 125.
       - Total kg/ha: Urea 330, TSP 270, MOP 250 -> kg/ac: Urea 133.5, TSP 109.3, MOP 101.2.
     - Kalpitiya: Basal TSP 270; Top 2 wk Urea 65, MOP 50; Top 3–4 wk Urea 90, MOP 70; Top 6 wk Urea 90, MOP 70; Top 8 wk Urea 90, MOP 70.
       - Total kg/ha: Urea 335, TSP 270, MOP 260 -> kg/ac: Urea 135.6, TSP 109.3, MOP 105.2.
   - **Intermediate Zone (Dual Units: kg/ha & kg/ac)**:
     - Basal Dressing: Urea 55 kg/ha (22 kg/ac), TSP 270 kg/ha (108 kg/ac), MOP 125 kg/ha (50 kg/ac).
     - Top Dressing 2 wk: Urea 110 kg/ha (44 kg/ac).
     - Top Dressing 3–4 wk: Urea 165 kg/ha (66 kg/ac), MOP 125 kg/ha (50 kg/ac).
     - Total: Urea 330 kg/ha (132 kg/ac), TSP 270 kg/ha (108 kg/ac), MOP 250 kg/ha (100 kg/ac).
   - **Wet Zone (Dual Units: kg/ha & kg/ac)**:
     - Basal Dressing: Urea 55 kg/ha (22 kg/ac), TSP 270 kg/ha (108 kg/ac), MOP 125 kg/ha (48 kg/ac).
     - Top Dressing 3–4 wk: MOP 125 kg/ha (50 kg/ac).
     - Total: Urea 55 kg/ha (22 kg/ac), TSP 270 kg/ha (108 kg/ac), MOP 250 kg/ha (98 kg/ac).
   - Zero artificial total rows injected; row sums preserved in `derived`.

5. **Cost of Production & Verbatim Economic Numerals**:
   - **Dry Zone (1 Acre)**:
     - Seed Potato Rs. 440,000.00, Fertilizer Rs. 99,500.00, Pesticide (printed as *Pecticide*) Rs. 70,000.00, Machinery Rs. 25,000.00.
     - Labour: Including family Rs. 149,920.00, Excluding family Rs. 200,000.00.
     - Total Expenditure: Including Rs. 784,420.00, Excluding Rs. 834,500.00.
     - Yield: 16,000 kg, Selling Price: Rs. 60/kg, Income: Rs. 960,000.00.
     - Gross Profit: Including Rs. 175,580.00, Excluding Rs. 125,500.30 *(printed verbatim with .30 cents)*.
   - **Intermediate Zone (1 Acre)**:
     - Seed Potato 720 kg x Rs. 190/= = Rs. 136,800.00, Fertilizer Rs. 25,000.00, Pesticide Rs. 15,000.00, Machinery Rs. 7,600.00.
     - Labour: Including family Rs. 96,000.00, Excluding family Rs. 30,400.00.
     - Total Expenditure: Including Rs. 280,400.00, Excluding Rs. 214,800.00.
     - Yield: 6,000 kg, Selling Price: Rs. 65/kg, Income: Rs. 390,000.00.
     - Gross Profit: Including Rs. 109,600.00, Excluding Rs. 175,200.00.
   - **Wet Zone (1 Acre)**:
     - Seed Potato 1000 kg x Rs. 190/= = Rs. 190,000.00, Fertilizer Rs. 55,000.00, Pesticide Rs. 15,000.00, Machinery Rs. 7,600.00.
     - Labour: Including Family Labour (125 x Rs. 800/=) = Rs. 100,000.00.
     - Total Expenditure: Printed verbatim as `Rs. 324850.00`.
     - Yield: 8,000 kg, Selling Price: Rs. 80/kg.
     - Income: Printed verbatim as `Rs. 64000.00` *(missing trailing zero on poster; arithmetic 8000 x 80 = 640,000.00)*.
     - Net Profit: Printed verbatim as `Rs. 165150.00`.

6. **Pests & Diseases Boundary Checks**:
   - **Dry Zone**:
     - Nov: `aphids`, `thrips`, `mites`, `leaf_eating_caterpillar`
     - Dec: `blight`, `aphids`, `thrips`, `mites`, `leaf_eating_caterpillar`
     - Jan: `blight`, `aphids`, `leaf_miner`, `thrips`, `mites`
     - Feb: `white_mold`
   - **Intermediate Zone**:
     - Nov: `aphids`, `thrips`, `mites`, `cut_worms`, `leaf_eating_caterpillars`
     - Dec: `late_blight`, `early_blight`, `bacterial_wilt`, `aphids`, `thrips`, `mites`, `cut_worms`, `leaf_eating_caterpillars`
     - Jun: `cut_worms`, `leaf_miner`, `aphids`, `thrips`, `white_fly`
   - **Wet Zone**:
     - Sep: `cut_worms`, `late_blight`
     - Oct: `aphids`, `late_blight`
     - Nov: `leaf_miner`, `bacterial_wilt`, `late_blight`, `black_leg`
     - Mar: `late_blight`, `early_blight`, `bacterial_wilt`, `aphids`, `cut_worms`, `leaf_miner`, `black_leg`
     - Apr: `late_blight`, `early_blight`, `bacterial_wilt`, `aphids`, `cut_worms`, `leaf_miner`, `black_leg`

7. **Weather Patterns (`h1`, `h2`)**:
   - Fully mapped across all 12 calendar months for all 3 zones.

8. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0, all 21/21 calendar JSON files validated).

---

## 17. Red Onion (*Allium cepa*) — Extraction & Multi-Zone Audit

- **Crops Handled**:
  - Red Onion — Dry Zone (`data-source/rgb/Red Onion/redonion_dry.png`)
  - Red Onion — Intermediate Zone (`data-source/rgb/Red Onion/RedOnion_inter.png`)
- **JSON Targets Generated**:
  - `src/data/calendars/red-onion/dry.json`
  - `src/data/calendars/red-onion/intermediate.json`
  - Mirrored: `profit_engine/frontend/src/data/calendars/red-onion/dry.json`
  - Mirrored: `profit_engine/frontend/src/data/calendars/red-onion/intermediate.json`
- **Overrides Generated**:
  - `overrides/red_onion.json`
  - `src/data/overrides/red_onion.json`
- **Transcripts Created**:
  - `data-source/transcripts/red_onion_dry.md`
  - `data-source/transcripts/red_onion_intermediate.md`

### Audit & Verification Findings:

1. **Dual Parallel Cultivation Streams**:
   - Both posters define two parallel agricultural rows:
     - **Row 2: Agricultural Activities (Bulb Crop)**: Commercial ware onion production across two distinct planting seasons (Maha: Jan W3–W4 to Apr W2–W3; Yala: May W2–W3 to Aug W2–W3).
     - **Row 3: True Seed Production (Seed Crop)**: Vernalised mother bulb cultivation for botanical true seed umbel production (Maha: Vernalisation Dec W1–W4, Planting Jan W3–W4, Pollination Mar W4–Apr W1, Seed Harvest Apr W1–W2; Yala: Vernalisation May W1–W4, Planting May W3–W4, Pollination Aug W3–W4, Seed Harvest Sep W1–W2).

2. **Timeline Structures & Calendar Ordering**:
   - Both posters begin at **December** and terminate at **November**.
   - Bulb Crop Seeding:
     - Maha: Jan W3–W4 (`plant_from: 1/W3`, `plant_to: 1/W4`); Harvest: Apr W2–W3 (`maha_month: 4`).
     - Yala: May W2–W3 (`plant_from: 5/W2`, `plant_to: 5/W3`); Harvest: Aug W2–W3 (`yala_month: 8`).
   - True Seed Production:
     - Maha: Selecting bulbs & vernalisation Dec W1–W4; Mother bulb planting Jan W3–W4; Seed umbel harvest Apr W1–W2.
     - Yala: Vernalisation May W1–W4; Mother bulb planting May W3–W4; Seed umbel harvest Sep W1–W2.

3. **Regional Distribution & Agro-Ecological Regions**:
   - **Dry Zone (`redonion_dry.png`)**:
     - Regions: Trincomalee DL-1c, DL-2; Jaffna DL-3, DL-4; Puttalam DL-1; Mullaitivu DL-1, DL-4; Monaragala DL-1; Anuradhapura DL-1, DL-1d; Badulla DL-1; Vavuniya DL-1, DL-1d; Mahaweli G, B, H & Uda Walawe; Mannar DL-1, DL-3; Kilinochchi DL-3, DL-4; Kurunegala DL-1; Rathnapura DL-1; Hambantota DL-1, DL-5; Polonnaruwa DL-1; Batticaloa DL-2, DL-2a; Matale DL-1; Ampara DL-2.
   - **Intermediate Zone (`RedOnion_inter.png`)**:
     - Regions: Kurunegala IL-1, IL-3; Monaragala IM-2, IL-1, IL-2; Kandy IM-1, IL-2; Rathanapura IM-1; Badulla IU-2, IU-3, IM-1, IM-4, IM-2, IL-2; Matale IL-2, IM-3; Mahaweli System C; Puttalam IL - 1.

4. **Varieties & Agronomic Specifications**:
   - **Varieties (4)**:
     - Dry Zone: `Jaffna`, `Vedalan`, `Thirunalvely Red`, `Thelulla Selection`.
     - Intermediate Zone: `Jaffna`, `Vedalan`, `Thirunavely Red` *(verbatim spelling variant without 'l')*, `Thelulla selection` *(verbatim lowercase 's')*.
   - **Spacing & Bed Architecture**:
     - Commercial Bulb Crop: `10cm x 10cm` (Seed rate: 575 kg/ha or 232.7 kg/ac).
     - True Seed Production: `15cm x 15cm` (Vernalised mother bulbs).
     - Polythene Tunnel Cover: `Covered with 3ft high Polythene` (noted on Intermediate Zone poster as *"Crop should cover with a pholythene"*).
     - Wet Season Bed Management: `Maha Season - Cultivate on ridges` / `Cultivateon Raised beds` *(verbatim typographical compound word)*.
     - Organic Amendment: `Apply Cow dung 10-15 mt/ha (4-6 mt/ac) 1 to 2 weeks, before planting`.

5. **Fertilizer Recommendations & Arithmetic Audit**:
   - Printed in **kg/ha** without printed totals:
     - Basal Dressing: Urea 65 kg/ha (or Ammonium sulphate 100 kg/ha), TSP 100 kg/ha, MOP 50 kg/ha.
     - Top Dressing 1 (3 weeks after planting): Urea 65 kg/ha or Ammonium sulfate 100 kg/ha.
     - Top Dressing 2 (6 weeks after planting for true seeds / bulb): Urea 65 kg/ha (or Ammonium sulphate), MOP 35 kg/ha.
   - Mathematical Sums (kg/ha):
     - Urea Regime: Urea 195 kg/ha, TSP 100 kg/ha, MOP 85 kg/ha.
     - Ammonium Sulphate Regime: Ammonium sulphate 300 kg/ha, TSP 100 kg/ha, MOP 85 kg/ha.
   - Acre Conversions (/ 2.471):
     - Urea Regime: Urea 78.9 kg/ac, TSP 40.5 kg/ac, MOP 34.4 kg/ac.
     - Ammonium Sulphate Regime: Ammonium sulphate 121.4 kg/ac, TSP 40.5 kg/ac, MOP 34.4 kg/ac.
   - Retained verbatim without inventing synthetic total rows.

6. **Economics & Printed Label Inversion Typo**:
   - **Gross Cost of Production (1 ha) - 2013**:
     - Seed bulbs: 575 kg x Rs. 120/= = Rs. 69,000.00.
     - Fertilizer: Rs. 10,500.00.
     - Chemical: Rs. 20,000.00.
     - Labour (Without family labour: 90 x Rs. 800/=): Rs. 72,000.00.
     - Labour (With family labour: 60 x Rs. 800/=): Rs. 48,000.00.
     - Total Expenditures:
       - Without family labour: Rs. 153,500.00.
       - With family labour: Rs. 129,500.00.
     - Income: Yield 3400 kg, Selling Price Rs. 70.00/kg, Net Income: Rs. 306,000.00.
     - Printed Net Profit:
       - Printed as `With family labour`: Rs. 152,500.00.
       - Printed as `Without family labour`: Rs. 176,500.00.
     - **Arithmetic Inversion Finding**:
       - 306,000.00 - 153,500.00 (without family labour expenditure) = 152,500.00. The printed poster inverted the label by attaching "With family labour" to this figure.
       - 306,000.00 - 129,500.00 (with family labour expenditure) = 176,500.00. The printed poster inverted the label by attaching "Without family labour" to this figure.
       - Documented verbatim in transcripts and JSON notes without altering raw printed numerals.

7. **Pollination & Typographical Findings**:
   - Pollination note in both posters: *"From 10 am to 11 pm is the best time to pollinate"* — identified as a typographical error for 11 am.
   - Backtick in pest list: *"Damping off`"* on Intermediate poster.
   - Spelling of *"infestes"* cultivations under fungal/bacterial rot control.

8. **Pests & Diseases Boundary Checks**:
   - Feb: `purple_blotch`, `anthracnose`, `bacterial_bulb_rot`, `fungal_bulb_rot`, `thrips`.
   - Mar: `damping_off`.
   - Apr: `big_onion_caterpillar`.
   - May: `fungal_bulb_rot`, `bacterial_bulb_rot`, `thrips`, `big_onion_caterpillar`.
   - Jun: `fungal_bulb_rot`, `bacterial_bulb_rot`, `thrips`, `big_onion_caterpillar`.
   - Jul: `fungal_bulb_rot`, `bacterial_bulb_rot`, `thrips`, `big_onion_caterpillar`.
   - Aug: `fungal_bulb_rot`, `bacterial_bulb_rot`, `thrips`, `big_onion_caterpillar`.
   - Sep–Jan: None listed.

9. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0, all 23/23 calendar JSON files validated).

---

## 18. Sesame (*Sesamum indicum*) — Extraction & Multi-Zone Audit

- **Crops Handled**:
  - Sesame — Dry & Intermediate Zone (`data-source/rgb/Sesame/thala-Dry-Inter.png`)
- **JSON Targets Generated**:
  - `src/data/calendars/sesame/dry-intermediate.json`
  - Mirrored: `profit_engine/frontend/src/data/calendars/sesame/dry-intermediate.json`
- **Overrides Generated**:
  - `overrides/sesame.json`
  - `src/data/overrides/sesame.json`
- **Transcripts Created**:
  - `data-source/transcripts/sesame_dry_intermediate.md`

### Audit & Verification Findings:

1. **Dual Parallel Cropping Systems**:
   - Poster defines two distinct cultivation streams:
     - **Row 3: Agricultural Activities**: Standard seasonal cultivation (Yala: Mar W1–W3 to Jun W3–Jul W2; Maha: Oct W2–W4 to Jan W3–Feb W2).
     - **Row 4: Alternative Cropping Time Table (Inter cropping with Maize for Northern Province)**: Dedicated intercrop system in Northern Province established Jan W2–W4 and harvested Apr W1–W4.

2. **Timeline Structures & Calendar Ordering**:
   - The calendar begins at **March** and terminates at **February**.
   - Standard Yala Seeding: Mar W1–W3 (`plant_from: 3/W1`, `plant_to: 3/W3`); Harvesting: Jun W3–Jul W2 (`yala_month: 6`).
   - Standard Maha Seeding: Oct W2–W4 (`plant_from: 10/W2`, `plant_to: 10/W4`); Harvesting: Jan W3–Feb W2 (`maha_month: 1`).
   - Alternative Northern Intercrop Seeding: Jan W2–W4 (`plant_from: 1/W2`, `plant_to: 1/W4`); Harvesting: Apr W1–W4 (`month: 4`).

3. **Regional Distribution & Agro-Ecological Regions**:
   - Scope: Dry & Intermediate Zones (`["dry", "intermediate"]`).
   - Regions: Puttalam DL-1, DL-3; Kilinochchi DL-4; Badulla District; Mannar DL-1, DL-3; Polonnaruwa DL-1; Ratnapura IL-1, DL-1 *(spelled Ratnapura)*; Vavuniya DL-1, DL-1a; Kurunegala DL-1; Ampara DL-2b; Matale DL-1, IL-1; Monaragala IM-2, IL-2, DL-1; Hambantota DL-5, IL-1; Mullaittivu DL-1, DL-4 *(spelled Mullaittivu)*; Batticaloa DL-2a; Jaffna DL-3, DL-4; Anuradhapura District; Mahaweli System C, H & Uda Walawe Project.

4. **Varieties & Agronomic Specifications**:
   - **Varieties (4)**: `Uma`, `Mali`, `MI 1`, `MI 3`. Standard yield: `400 kg/ac`.
   - **Seed Rates & Spacing**:
     - Broadcasting: `3 kg/ac`.
     - Row Cultivation: `2 kg/ac` at `30 cm x 15 cm` spacing.
   - **Soil Amendment Advice**:
     - `To improve soil fertility, Control soil erosion, Use Gliricidia loppings to improve soil fertilitiy` *(spelled fertilitiy)*.

5. **Fertilizer Recommendations & Arithmetic Verification**:
   - Printed in **kg/ac** (with table header typo: `Fertilizer - kg/ae`):
     - Basal Dressing: Urea 20 kg/ac, TSP 48 kg/ac, MOP 24 kg/ac.
     - Top Dressing (4 weeks after planting): Urea 24 kg/ac.
   - Total Computed Sums: Urea 44 kg/ac, TSP 48 kg/ac, MOP 24 kg/ac.
   - Retained verbatim without inventing synthetic total rows.

6. **Economics & Printed Typographical Omission**:
   - **Estimane of Gross Profit and Expenditure (Acre) - 2013** *(printed typo: "Estimane")*:
     - Seeds: Rs. 900.00.
     - Other inputs (Fertilizer): Rs. 250.00.
     - Machinery: Rs. 500.00.
     - Labour (Without family labour: 30 x Rs. 800/=): Rs. 24,000.00.
     - Labour (With family labour: 8 x Rs. 800/=): Rs. 6,400.00.
     - Expenditures:
       - Without family labour: Rs. 32,400.00.
       - With family labour: Rs. 14,800.00.
     - Income: Yield 400 kg, Selling price Rs. 175.00/kg, Net Income: Rs. 70,000.00.
     - Printed Gross Profit:
       - Printed as `without family labour`: `7600.00`.
       - Printed as `with family labour`: `55200.00`.
     - **Typographical Finding**:
       - With family labour: 70,000.00 - 14,800.00 = 55,200.00 (Exact arithmetic match).
       - Without family labour: 70,000.00 - 32,400.00 = 37,600.00. The printed poster omitted the leading digit '3', producing `7600.00`. Documented verbatim in transcripts and JSON notes.

7. **Pests & Diseases Boundary Audit**:
   - The timeline pest row contains no monthly bounded pests, displaying a global banner: *"Insect pest attacts are low in sesame cultivation"* *(verbatim spelling: "attacts")*.
   - Target pests and specific control measures detailed in Tile 05:
     - `Leaf webber` (*Antigastra catalaunalis*): Tebufenozide 20 SC (15 ml/10 ltr), Chlorfluazuron 52 EC (30 ml/10 ltr), Neem extract (400 gm/10 ltr).
     - `Mites` & `Tomato bug`: Sanitation, crop rotation, destruction of infected parts.
     - `Phyllody`: Vector control (plant hoppers).
     - `Stem and foot rot`: Crop rotation, improved drainage, deep summer ploughing.

8. **Risk Advice Typographical Notes**:
   - Drought: `Excess irrigation`.
   - Flood: `Make drains to improve draining ridges to avoid flowing of outside water`, `Improve soil fertilizing : Avoid Soil erosion Plant Gliriuidia on ridges, lopped and add to soil` *(spelled Gliriuidia)*.

9. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0, all 24/24 calendar JSON files validated).

---

## 19. Soya Bean (*Glycine max*) — Extraction & Multi-Zone Audit

- **Crops Handled**:
  - Soya Bean — Dry Zone (`data-source/rgb/Soya Bean/soya_DRY.png`)
  - Soya Bean — Intermediate Zone (`data-source/rgb/Soya Bean/soya_INTER.png`)
- **JSON Targets Generated**:
  - `src/data/calendars/soya-bean/dry.json`
  - `src/data/calendars/soya-bean/intermediate.json`
  - Mirrored: `profit_engine/frontend/src/data/calendars/soya-bean/dry.json`
  - Mirrored: `profit_engine/frontend/src/data/calendars/soya-bean/intermediate.json`
- **Overrides Generated**:
  - `overrides/soya_bean.json`
  - `src/data/overrides/soya_bean.json`
- **Transcripts Created**:
  - `data-source/transcripts/soya_bean_dry.md`
  - `data-source/transcripts/soya_bean_intermediate.md`

### Audit & Verification Findings:

1. **Timeline Structures & Seasonal Windows**:
   - Both posters begin at **September** and terminate at **August**.
   - **Maha Season**:
     - Land Preparation: Oct W2–W3.
     - Seeding, Basal Dressing & Inoculation: Oct W3–W4 (`plant_from: 10/W3`, `plant_to: 10/W4`).
     - Weeding & Fertilizer Application: Nov W2–W4.
     - Harvesting: Jan W1–W2 (`maha_month: 1`).
   - **Yala Season**:
     - Land Preparation: Apr W4–May W1.
     - Seeding, Basal Dressing & Inoculation: May W1–W2 (`plant_from: 5/W1`, `plant_to: 5/W2`).
     - Weeding & Fertilizer Application: May W3–W4.
     - Harvesting: Jul W2–W3 (`yala_month: 7`).

2. **Regional Distribution & Agro-Ecological Regions**:
   - **Dry Zone (`soya_DRY.png`)**:
     - Regions: Anuradhapura District; Puttalam DL-1; Mannar DL-1; Hambantota DL-1, DL-5; Monaragala DL-1; Kurunegala DL-1; Ratnapura DL-1; Badulla DL-1; Matale DL-1; Polonnaruwa DL-1; Vavuniya DL-1, DL-1d; Mahaweli System 'H and G'.
   - **Intermediate Zone (`soya_INTER.png`)**:
     - Regions: Kandy IM-1, IL-2; Badulla IM-1, IM-2, IL-2; Matale IL-2; Monaragala IL-2.

3. **Varieties, Duration & Agronomic Specifications**:
   - **Varieties (3)**:
     - `PB -1`: Duration `80-85 days`.
     - `PM -13`: Duration `90-95 days`.
     - `MISB1`: Duration `90-95 days`.
   - **Seed Rate & Spacing**:
     - Seed Rate: `50-60 kg/ha` (Economics table calculates `22 kg/ac` at Rs. 145/kg).
     - Spacing: `40 x 5 cm`.
   - **Rhizobium Inoculation**:
     - Detailed 2-method protocol using 250g bacteria medium per 50–60 kg seed.
     - Key biological rule: `No urea is required if the seeds are inoculated` / `Do not use Urea to the basal dressing of fertilizer`.

4. **Fertilizer Recommendations & Biological Regimes**:
   - Printed in **kg/ha** without printed totals:
     - Basal Dressing: Urea 50 kg/ha, TSP 100 kg/ha, MOP 75 kg/ha.
     - Top Dressing: Urea 50 kg/ha.
   - Dual Operational Regimes:
     - Standard (Uninoculated): Urea 100 kg/ha (40.5 kg/ac), TSP 100 kg/ha (40.5 kg/ac), MOP 75 kg/ha (30.4 kg/ac).
     - Inoculated (Rhizobium): Urea 0 kg/ac, TSP 40.5 kg/ac, MOP 30.4 kg/ac.
   - Zero synthetic total rows injected; row sums preserved in `derived`.

5. **Economics & Printed Transposition Typo**:
   - **Estimate of Gross Profit & Expenditure (Acre) - 2013**:
     - Seeds: 22 kg x Rs. 145/= = Rs. 3,190.00.
     - Chemical: Rs. 4,402.00.
     - Machinery: Rs. 8,000.00.
     - Labour (Including family: 30 x Rs. 800/=): Rs. 24,000.00.
     - Labour (Excluding family: 47 x Rs. 800/=): Rs. 37,600.00.
     - Total Expenditures: Including Rs. 39,592.00; Excluding Rs. 53,192.00 (Exact arithmetic sum of inputs).
     - Income: Yield 1120 kg, Selling Price Rs. 70.00/kg.
     - Printed Income: `Rs. 74,800.00`.
     - **Arithmetic Transposition Finding**: 1120 kg x Rs. 70.00/kg = Rs. 78,400.00. The printed poster displays `74800.00` (transposing 84 to 48).
     - Gross Profit calculations strictly follow the printed income:
       - Including family labour: 74,800.00 - 39,592.00 = 35,208.00 (Exact match).
       - Excluding family labour: 74,800.00 - 53,192.00 = 21,608.00 (Exact match).
     - Documented verbatim in transcripts and JSON notes.

6. **Pests & Diseases Boundary Checks**:
   - Monthly bound cells:
     - Oct: `collar_rot` (W3–W4).
     - Nov: `collar_rot`, `cercospora_leaf_spot`, `anthracnose`.
     - Dec: `collar_rot`, `cercospora_leaf_spot`, `anthracnose`, `powdery_mildew`, `pod_borer`, `purple_seed_stain`.
     - Jan: `cercospora_leaf_spot`, `anthracnose`, `powdery_mildew`, `purple_seed_stain`, `white_fly`, `pod_sucking_bug`, `aphids`, `mites`, `leaf_hopper`, `pod_borer`.
     - May: `collar_rot` (W1–W2).
     - Jun: `collar_rot`, `cercospora_leaf_spot`, `anthracnose`.
     - Jul: `purple_seed_stain`, `mosaic_virus`, `bean_fly`, `pod_borer`, `blister_beetle`, `pod_sucking_bug`, `aphids`, `mites`.
     - Feb–Apr, Aug–Sep: None listed.

7. **Risk Advice & Agronomic Measures**:
   - Drought: `Mulching`, `Timely cultivation`.
   - Flood: `Improve drainage system`, `Ridge and furrow cultivation` / `Practice ridge and furrow cultivation`.

8. **Validation Status**:
   - `node scripts/validate_calendars.js` executed: ✅ **PASS** (Exit code 0, all 26/26 calendar JSON files validated).

---

## 20. Final Complete Extraction Summary: Sri Lanka DOA/AFACI National Crop Calendars

All 12 major field crops (plus Paddy) across all agro-ecological zones (Dry, Intermediate, Wet) have been 100% extracted, transcribed, schema-validated, and cross-audited:

| # | Crop Name | App Slug | Zone Files Generated | Total Files | Status |
| :-: | :--- | :--- | :--- | :-: | :-: |
| 1 | Big Onion (*Allium cepa*) | `Big Onion` | `dry-intermediate.json` | 1 | ✅ Validated |
| 2 | Black Gram (*Vigna mungo*) | `Black Gram` | `dry.json`, `intermediate.json` | 2 | ✅ Validated |
| 3 | Chilli (*Capsicum annuum*) | `Green Chilli` | `dry.json`, `intermediate.json`, `wet.json` | 3 | ✅ Validated |
| 4 | Cowpea (*Vigna unguiculata*) | `Cowpea` | `dry.json`, `intermediate.json` | 2 | ✅ Validated |
| 5 | Finger Millet (*Eleusine coracana*) | `Kurakkan` | `dry-intermediate.json` | 1 | ✅ Validated |
| 6 | Green Gram (*Vigna radiata*) | `Green Gram` | `dry.json`, `intermediate.json` | 2 | ✅ Validated |
| 7 | Ground Nut (*Arachis hypogaea*) | `Groundnut` | `dry-intermediate.json` | 1 | ✅ Validated |
| 8 | Maize (*Zea mays*) | `Maize` | `dry.json`, `intermediate.json` | 2 | ✅ Validated |
| 9 | Paddy (*Oryza sativa*) | `Paddy` | `dry-intermediate-irrigated.json`, `dry-intermediate-rainfed.json`, `wet.json`, `ipm.json` | 4 | ✅ Validated |
| 10 | Potato (*Solanum tuberosum*) | `Potato` | `dry.json`, `intermediate.json`, `wet.json` | 3 | ✅ Validated |
| 11 | Red Onion (*Allium cepa*) | `Red Onion` | `dry.json`, `intermediate.json` | 2 | ✅ Validated |
| 12 | Sesame (*Sesamum indicum*) | `Gingelly` | `dry-intermediate.json` | 1 | ✅ Validated |
| 13 | Soya Bean (*Glycine max*) | `Soybean` | `dry.json`, `intermediate.json` | 2 | ✅ Validated |
| **Total** | **13 Crops** | | | **26 JSONs** | **100% COMPLETE** |







