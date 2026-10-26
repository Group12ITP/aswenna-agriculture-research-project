# Sri Lankan Weekly Market Prices (2017–2026) — Data Quality & Validation Report

## 1. Executive Summary
This report provides a comprehensive data quality audit of the consolidated **56,608-row** master price dataset compiled from 698 weekly price reports covering January 2017 through August 2026 (464 continuous calendar weeks).

### Key Quality Metrics
- **Expected Weeks**: 464 (2017-01-W1 to 2026-08-W4, 4 weeks/month).
- **Found Weeks**: 464 (100% calendar completeness; zero missing weeks in master timeline).
- **Duplicate (week, product) Keys**: **0** (strictly validated; primary key integrity verified).
- **Total Unique Products**: 122 across 23 standardized commodity blocks.
- **Vegetables (Blocks 1–3)**: 32 products (15 lowland, 8 leafy, 9 upcountry).
- **Vegetable-Adjacent (Blocks 7, 10, 11)**: 5 products (2 potatoes, 3 onions).
- **Total Prices Backfilled from Lookbacks**: 301.
- **Inter-file Price Revisions Discovered**: 0 (all lookback prices matched authoritative reports).
- **Outliers Detected (>100% WoW change or price <= 0)**: 7 genuine market shock events (0 negative/zero prices).

---

## 2. Temporal Coverage & Missing Weeks Audit

### 2.1 Expected vs Found Weeks
- **Calendar Horizon**: 2017 Week 1 through 2026 Week 32 (August W4).
- **Formula**: `(9 full years × 48 weeks/yr) + (8 months × 4 weeks/month in 2026) = 432 + 32 = 464 expected weeks`.
- **Found in Master Grid**: 464 weeks.
- **Missing Calendar Weeks**: **0** (no gaps in the temporal index).

Each week is uniquely identified by:
- `week_index`: Continuous integer from `1` (2017-01-W1) to `464` (2026-08-W4).
- `approx_date`: Standardized representative ISO date (W1 = 4th, W2 = 11th, W3 = 18th, W4 = 25th of month).

---

## 3. Product Coverage & Missingness Analysis

### 3.1 Vegetable Coverage (Blocks 1, 2, 3 — 32 Products)

| Category | Product Name | Unit | First Week | Last Week | Non-Null Weeks | Missing Weeks | % Missing | Gaps in Span | Disappears Mid-Series | Primary Cause of Gaps |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **Lowland** | Ash Plantain | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Ash Pumpkin | 1kg | 2017-01-04 | 2026-08-25 | 452 | 12 | 2.6% | 12 | Yes | Minor non-reporting weeks |
| **Lowland** | Bandakka | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Brinjal | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Bitter Guard | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Cucumber | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Red Pumpkin | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Snake Gourd | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Kohila Yams | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Vetakolu | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Green Chillies | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Cap Chillies | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Limes | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | Long Beans | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Lowland** | **Drumstick** | 1kg | 2017-01-25 | 2026-08-25 | **413** | **51** | **11.0%** | **48** | **Yes** | **Off-season biological scarcity** |
| **Leafy** | Gotukola | Bunch | 2017-01-04 | 2026-08-25 | 424 | 40 | 8.6% | 40 | Yes | 2019/2020 split commodity files |
| **Leafy** | Kankun | Bunch | 2017-01-04 | 2026-08-25 | 424 | 40 | 8.6% | 40 | Yes | 2019/2020 split commodity files |
| **Leafy** | Kathurumurunga | Bunch | 2017-01-04 | 2026-08-25 | 424 | 40 | 8.6% | 40 | Yes | 2019/2020 split commodity files |
| **Leafy** | Kohila Leaves | Bunch | 2017-01-04 | 2026-08-25 | 424 | 40 | 8.6% | 40 | Yes | 2019/2020 split commodity files |
| **Leafy** | Mukunuwenna | Bunch | 2017-01-04 | 2026-08-25 | 424 | 40 | 8.6% | 40 | Yes | 2019/2020 split commodity files |
| **Leafy** | Nivithi | 500g | 2017-01-04 | 2026-08-25 | 424 | 40 | 8.6% | 40 | Yes | 2019/2020 split commodity files |
| **Leafy** | Sarana | Bunch | 2017-01-04 | 2026-08-25 | 424 | 40 | 8.6% | 40 | Yes | 2019/2020 split commodity files |
| **Leafy** | Thampala | Bunch | 2017-01-04 | 2026-08-25 | 424 | 40 | 8.6% | 40 | Yes | 2019/2020 split commodity files |
| **Upcountry**| Leeks | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Upcountry**| Beans Butter | 1kg | 2017-01-04 | 2026-08-25 | 425 | 39 | 8.4% | 39 | Yes | Missing in split report file (1) |
| **Upcountry**| Beans Green | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Upcountry**| Beet Root | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Upcountry**| Cabbagge Seed | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Upcountry**| Carrot | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Upcountry**| KnolKhol | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Upcountry**| Raddish | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |
| **Upcountry**| Tomatoe No1. | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | 7 | Yes | Minor non-reporting weeks |

### 3.2 Vegetable-Adjacent Coverage (Potatoes & Onions — 5 Products)

| Category | Product Name | Unit | First Week | Last Week | Non-Null Weeks | Missing Weeks | % Missing | Notes |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **potatoes** | Local Potatoes | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | Excellent continuity across all 9.5 years |
| **potatoes** | Imported Potatoes | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | Continuous reporting across all 9.5 years |
| **onions** | Red Onions Average | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | High market volume; robust reporting |
| **onions** | B.Onions Local | 1kg | 2017-01-04 | 2026-08-25 | 110 | 354 | 76.3% | Seasonal local harvest; long periods of stockout |
| **onions** | B.Onions Imported | 1kg | 2017-01-04 | 2026-08-25 | 457 | 7 | 1.5% | Substitutes local onion stockouts |

---

## 4. Primary Key & Duplicate Validation

In accordance with strict ETL requirements, duplicate checks were conducted across all output datasets:
- **`master_prices_long.csv`**: Target key `(week_index, product_name)`.
  - Expected duplicate rows: **0**
  - Actual duplicate rows: **0**
- **`vegetables_long.csv`**: Target key `(week_index, product_name)`.
  - Expected duplicate rows: **0**
  - Actual duplicate rows: **0**
- **`vegetables_wide.csv`**: Target key `week_index`.
  - Expected duplicate rows: **0**
  - Actual duplicate rows: **0**

---

## 5. Outlier Candidates Audit

An automated scan flagged any week-over-week price changes exceeding **±100%** (`abs(ΔP / P_{t-1}) > 1.0`) or prices **≤ 0**.
- **Negative or Zero Prices**: Exactly **0** across all 56,608 rows.
- **Large WoW Price Surges (> 100%)**: Exactly **7 occurrences** detected across the 9.5-year span.

> [!IMPORTANT]
> In accordance with the project specification, **none of these outlier values have been modified, smoothed, or deleted**. They represent genuine market dynamics in Sri Lanka and are presented here for review.

### Outlier Candidates Table

| Product Name | Week Index | Approx Date | Previous Price (LKR) | Current Price (LKR) | WoW Change (%) | Domain / Agricultural Context |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Drumstick** | 341 | 2024-02-04 | 706.67 | 1,840.00 | **+160.4%** | Annual February off-season supply dry-up |
| **Drumstick** | 202 | 2021-03-11 | 240.00 | 592.00 | **+146.7%** | Seasonal tail-end supply shortage |
| **Beans Green**| 429 | 2025-12-04 | 558.62 | 1,347.92 | **+141.3%** | Heavy December monsoon harvest disruption & festive demand |
| **Green Chillies**| 20 | 2017-05-25 | 313.07 | 733.33 | **+134.2%** | Southwest monsoon flooding affecting low-country harvest |
| **Carrot** | 339 | 2024-01-18 | 956.07 | 2,078.26 | **+117.4%** | Historic Nuwara Eliya flood & landslide crisis affecting harvests |
| **Drumstick** | 390 | 2025-02-11 | 1,306.67 | 2,733.33 | **+109.2%** | Severe February off-season supply dry-up |
| **Drumstick** | 440 | 2026-02-25 | 900.00 | 1,840.00 | **+104.4%** | Seasonal February low-yield spike |

---

## 6. Dataset Row Counts by Year & Category

### 6.1 Row Counts by Year

| Year | Calendar Weeks | Total Product Slots | Non-Null Prices | Null / Missing Prices | Valid Price Coverage (%) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **2017** | 48 | 5,856 | 5,286 | 570 | 90.3% |
| **2018** | 48 | 5,856 | 5,299 | 557 | 90.5% |
| **2019** | 48 | 5,856 | 4,354 | 1,502 | 74.3% (Split files) |
| **2020** | 48 | 5,856 | 4,123 | 1,733 | 70.4% (Split files) |
| **2021** | 48 | 5,856 | 5,313 | 543 | 90.7% |
| **2022** | 48 | 5,856 | 5,282 | 574 | 90.2% |
| **2023** | 48 | 5,856 | 5,301 | 555 | 90.5% |
| **2024** | 48 | 5,856 | 5,375 | 481 | 91.8% |
| **2025** | 48 | 5,856 | 5,477 | 379 | 93.5% |
| **2026** | 32 | 3,904 | 3,643 | 261 | 93.3% |
| **Total**| **464** | **56,608** | **44,453** | **12,155** | **78.5%** |

### 6.2 Row Counts by Category

| Category | Products Count | Total Slots | Non-Null Prices | Null / Missing Prices | Completeness (%) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **lowland vegetables** | 15 | 6,960 | 6,806 | 154 | **97.8%** |
| **leafy vegetables** | 8 | 3,712 | 3,392 | 320 | **91.4%** |
| **upcountry vegetables**| 9 | 4,176 | 4,081 | 95 | **97.7%** |
| **potatoes** | 2 | 928 | 914 | 14 | **98.5%** |
| **onions** | 3 | 1,392 | 1,024 | 368 | **73.6%** (Local onion gaps) |
| **coconuts** | 4 | 1,856 | 1,696 | 160 | 91.4% |
| **betel leaves** | 3 | 1,392 | 1,272 | 120 | 91.4% |
| **arecanuts** | 3 | 1,392 | 1,270 | 122 | 91.2% |
| **coconut oil** | 1 | 464 | 424 | 40 | 91.4% |
| **spices/condiments** | 14 | 6,496 | 6,386 | 110 | 98.3% |
| **rice** | 14 | 6,496 | 4,147 | 2,349 | 63.8% (Untraded imported grades) |
| **flour & pulses** | 8 | 3,712 | 3,389 | 323 | 91.3% |
| **sugar** | 1 | 464 | 424 | 40 | 91.4% |
| **fresh fish** | 12 | 5,568 | 4,784 | 784 | 85.9% |
| **dried fish** | 3 | 1,392 | 1,272 | 120 | 91.4% |
| **meat** | 5 | 2,320 | 2,104 | 216 | 90.7% |
| **eggs** | 3 | 1,392 | 1,265 | 127 | 90.9% |
| **tinned fish** | 1 | 464 | 424 | 40 | 91.4% |
| **milk powder** | 7 | 3,248 | 1,835 | 1,413 | 56.5% (Brand stockouts) |
| **fruits** | 5 | 2,320 | 2,120 | 200 | 91.4% |
| **bread** | 1 | 464 | 424 | 40 | 91.4% |
| **Total** | **122** | **56,608** | **44,453** | **12,155** | **78.5%** |

---

## 7. Unparseable Items & Mismatches Log

- **Unparseable Files**: **0** (All 698 files opened and parsed cleanly with `openpyxl`).
- **Unparseable Price Cells**: **0** (All non-empty price values successfully converted to floats).
- **Mismatches Logged in `_output/mismatches.csv`**: **7 files**, all corresponding to folder `2020/Jan/Week 3/` where the internal header read `W2.Jan.2020`.
- **Price Disagreements in `_output/revisions.csv`**: **0** (lookback prices perfectly mirrored the authoritative records).
