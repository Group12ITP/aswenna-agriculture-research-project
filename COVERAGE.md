# Aswenna Crop Calendar Coverage Matrix (Crop × Zone)

This document audits the coverage of Department of Agriculture (DOA) / AFACI crop calendar sheets against the **23 crops** in the Aswenna cost-model crop list (`advisoryData.crops` denominator).

> [!NOTE]
> - **Beetroot** is excluded from this denominator as it is not in the cost-model crop list.
> - **Capsicum** (*Capsicum annuum var. grossum* / Bell Pepper / Malu Miris) has no calendar poster and stays marked as "No Calendar". The available `Chilli` calendar posters map strictly to **Green Chilli** (*Capsicum annuum* / Amu Miris).

---

## 1. Summary Statistics

- **Total App Crops Tracked (Denominator)**: 23 crops
- **Crops with At Least One Calendar**: 13 crops (56.5%)
- **Crops Completely Missing (All Zones)**: 10 crops (43.5%)
- **Zone Breakdown Across 23 Crops**:
  - **Dry Zone**: 13 / 23 crops covered (56.5%)
  - **Intermediate Zone**: 13 / 23 crops covered (56.5%)
  - **Wet Zone**: 3 / 23 crops covered (13.0% — Paddy, Potato, Green Chilli)

---

## 2. Crop × Zone Coverage Matrix

| # | Crop Name | Botanical Name | Category | Dry Zone | Intermediate Zone | Wet Zone | Calendar Files |
|---|---|---|---|:---:|:---:|:---:|---|
| 1 | **Paddy** | *Oryza sativa* | Grains | ✅ | ✅ | ✅ | `paddy-DRYINTER_Irrigated_English-scaled.png`<br>`paddy-DRYINTER_Rainfed_English-scaled.png`<br>`paddy-WET_English_New-scaled.png`<br>*(+ `IPMcalender.png` Sinhala supplement)* |
| 2 | **Potato** | *Solanum tuberosum* | Tubers | ✅ | ✅ | ✅ | `POTATO_-Dry-jaffna-Kalpitiya.png`<br>`POTATO_-Inter-badulla.png`<br>`POTATO_Wet-Nuwaraeliya.png` |
| 3 | **Green Chilli** | *Capsicum annuum* | Spices | ✅ | ✅ | ✅ | `Chilli_Dry.png`<br>`inter-chilli-english.png`<br>`Chili_wet.png` |
| 4 | **Big Onion** | *Allium cepa* | Vegetables | ✅ | ✅ | ❌ | `BIg-onion-Dry-Inter-E.png` |
| 5 | **Red Onion** | *Allium cepa var. aggregatum* | Vegetables | ✅ | ⚠️ *(Pending)* | ❌ | `redonion_dry.png`<br>`RedOnion_inter.png` *(sRGB verified)* |
| 6 | **Maize** | *Zea mays* | Grains | ✅ | ✅ | ❌ | `maiz_dry.png`<br>`maiz_inter.png` |
| 7 | **Kurakkan** *(Finger Millet)* | *Eleusine coracana* | Grains | ✅ *(Partial)* | ✅ *(Partial)* | ❌ | `fingerMillet_dryinter-1024x757.png` |
| 8 | **Gingelly** *(Sesame)* | *Sesamum indicum* | Grains | ✅ | ✅ | ❌ | `thala-Dry-Inter.png` |
| 9 | **Black Gram** | *Vigna mungo* | Pulses | ✅ | ✅ | ❌ | `Blackgram_DRY.png`<br>`Blackgram_INTER.png` |
| 10 | **Cowpea** | *Vigna unguiculata* | Pulses | ✅ | ✅ | ❌ | `Cowpea_DRY.png`<br>`Cowpea_INTER.png` |
| 11 | **Green Gram** | *Vigna radiata* | Pulses | ✅ | ✅ | ❌ | `GreenGram_DRY.png`<br>`GreenGram_INTER.png` |
| 12 | **Groundnut** | *Arachis hypogaea* | Pulses | ✅ | ✅ | ❌ | `groundNut.png` |
| 13 | **Soybean** | *Glycine max* | Pulses | ✅ | ✅ | ❌ | `soya_DRY.png`<br>`soya_INTER.png` |
| 14 | **Tomato** | *Solanum lycopersicum* | Vegetables | ❌ | ❌ | ❌ | *No calendar sheet* |
| 15 | **Cabbage** | *Brassica oleracea* | Vegetables | ❌ | ❌ | ❌ | *No calendar sheet* |
| 16 | **Carrot** | *Daucus carota* | Vegetables | ❌ | ❌ | ❌ | *No calendar sheet* |
| 17 | **Brinjal** | *Solanum melongena* | Vegetables | ❌ | ❌ | ❌ | *No calendar sheet* |
| 18 | **Capsicum** *(Bell Pepper)* | *Capsicum annuum var. grossum* | Vegetables | ❌ | ❌ | ❌ | *No calendar sheet (distinct from Green Chilli)* |
| 19 | **Bitter Gourd** | *Momordica charantia* | Vegetables | ❌ | ❌ | ❌ | *No calendar sheet* |
| 20 | **Pumpkin** | *Cucurbita moschata* | Vegetables | ❌ | ❌ | ❌ | *No calendar sheet* |
| 21 | **Pole Bean** | *Phaseolus vulgaris* | Vegetables | ❌ | ❌ | ❌ | *No calendar sheet* |
| 22 | **Manioc** *(Cassava)* | *Manihot esculenta* | Tubers | ❌ | ❌ | ❌ | *No calendar sheet* |
| 23 | **Sweet Potato** | *Ipomoea batatas* | Tubers | ❌ | ❌ | ❌ | *No calendar sheet* |

---

## 3. Strict Zone Fallback Policy

Per system architecture rules:
> **`getCalendar` must NEVER fall back across zones.**
> If a farmer in Gampaha (Wet Zone) requests a calendar for Big Onion (which only exists for Dry/Intermediate), the engine must return `no_calendar_for_zone`. It must NEVER serve the Dry Zone calendar as a substitute.
