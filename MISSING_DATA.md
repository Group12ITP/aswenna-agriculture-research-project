# Missing Data & Quality Audit Report

This report catalogs all corrupted images, partial/degraded files, unreadable fields, and missing zone variants across the Crop Calendar dataset.

---

## 1. Corrupted Images (Excluded from Extraction)

### `Red Onion/RedOnion_inter.jpg`
- **Location**: `data-source/crop-calendar-images/Red Onion/RedOnion_inter.jpg`
- **Resolution**: 1725 x 1275 (CMYK)
- **Status**: **CORRUPTED (PRINT / COMPOSITION ERROR)**
- **Defect Description**:
  - In the **Agricultural Activities** row (between the Weather timeline and Pest row), the colored operational timeline bars showing duration across months and weeks are completely absent.
  - Unlike `redonion_dry.jpg` which displays distinct horizontal bars for Land Preparation (beige), Direct Seeding (pink), Weed Control (green), and Harvesting (orange), the intermediate sheet only contains cartoon illustrations and speech bubbles on a blank white grid.
- **Extraction Directive**: **DO NOT EXTRACT**. Operational timing offsets (`start_day_offset`, `end_day_offset`) cannot be determined without inventing or fabricating dates.

---

## 2. Partial / Degraded Images

### 1. `Finger Millet/fingerMillet_dryinter-1024x757.jpg`
- **Location**: `data-source/crop-calendar-images/Finger Millet/fingerMillet_dryinter-1024x757.jpg`
- **Resolution**: 1024 x 757 (CMYK) — ~40% lower resolution than standard sheets
- **Status**: **PARTIAL LEGIBILITY**
- **Defect Description**:
  - The image is a downscaled thumbnail from a web publication rather than a master print export.
  - **Legible**: Header, weather row, high-level operational icons (Land Prep, Seeding, Basal Dressing, Top Dressing, Weed Control, Harvesting), variety names (Ravi, Ravana, Oshadi), spacing (30 x 10-15 cm), seed rate (8 kg/ac seeding, 3-5 kg/ac in rows), and basal fertilizer (Urea 65, TSP 55, MOP 82.5 kg/ha).
  - **Unreadable / Cut-off**: 
    - The bottom district table lists very small fonts that suffer from compression artifacts.
    - Inside the risk advisory triangle, under the "HEAVY RAIN OR FLOOD" section, the descriptive bullet points are washed out / omitted.
- **Extraction Directive**: Extract visible core agronomic parameters with appropriate `"confidence": "medium"` or `"low"`. Set unreadable district sub-lists to `null`.

### 2. `Paddy/IPMcalender.jpg`
- **Location**: `data-source/crop-calendar-images/Paddy/IPMcalender.jpg`
- **Resolution**: 1725 x 1275 (CMYK)
- **Status**: **SPECIALIZED / NON-CONFORMING**
- **Defect Description**:
  - Script is entirely in **Sinhala** ("වී වගාවේ ඒකාබද්ධ පළිබෝධ පාලනය කාල සටහන").
  - Content focuses strictly on Integrated Pest Management (IPM) across phenological growth stages (seedling, tillering, heading, ripening).
  - Lacks the standard DOA crop calendar schema components: no variety duration table, no NPK fertilizer schedule, no day-offset operations.
- **Extraction Directive**: Exclude from standard `src/data/calendars/paddy/` agronomic JSON extraction. Retain as supplementary pest data source.

---

## 3. Crops Lacking Separate Zone Variants (Combined / Single Sheets)

The following crops do not have individual Dry, Intermediate, and Wet zone files. Instead, they provide a single combined sheet covering both Dry & Intermediate zones:

| Crop Folder | File Name | Zone Coverage in Source | Output Target |
|---|---|---|---|
| `Big Onion` | `BIg-onion-Dry-Inter-E.jpg` | Combined Dry & Intermediate Zones | `big-onion/dry-intermediate.json` (or `all-zones.json`) |
| `Finger Millet` | `fingerMillet_dryinter-1024x757.jpg` | Combined Dry & Intermediate Zones | `finger-millet/dry-intermediate.json` |
| `Ground Nut` | `groundNut.jpg` | Combined Intermediate & Dry Zones | `ground-nut/dry-intermediate.json` |
| `Sesame` | `thala-Dry-Inter.jpg` | Combined Dry & Intermediate Zones | `sesame/dry-intermediate.json` |

---

## 4. Entirely Missing Crops (No Calendar Sheets)

The following 11 crops tracked in the Aswenna application currently have no calendar poster sheets in `Crop Calender/`:
- **Tomato**
- **Cabbage**
- **Carrot**
- **Brinjal**
- **Capsicum**
- **Bitter Gourd**
- **Pumpkin**
- **Pole Bean**
- **Beetroot**
- **Manioc**
- **Sweet Potato**
