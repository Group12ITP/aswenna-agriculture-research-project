# Aswenna Crop Calendar Data Layer Audit (DATA_AUDIT.md)

**Generated:** 2026-10-15T11:36:19.175Z  
**Target Directory:** `src/data/calendars/`  
**Total Validated Calendar Files:** 26  

---

## 1. Executive Summary & Verification Matrix

| # | Crop Calendar File | App Crop | Zones | Scenarios | Durations? | Yields? | Timing Ops (Parsed / Fail) | Weather Icons | Pests (Has Img / Missing) | Raw Eco Keys Found | Sanitized Surviving |
|---|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `big-onion/dry-intermediate.json` | **Big Onion** | dry, intermediate | 3 | ⚠️ Null (Typical) | ✅ Ref Yield | 0/27 (27 advice) | 5 (✅ 100% mapped) | 0 / 5 | 0 | **0 (Clean)** |
| 2 | `black-gram/dry.json` | **Black Gram** | dry | 2 | ✅ Present | ✅ Ref Yield | 5/7 (2 advice) | 5 (✅ 100% mapped) | 0 / 13 | 1 | **0 (Clean)** |
| 3 | `black-gram/intermediate.json` | **Black Gram** | intermediate | 2 | ✅ Present | ✅ Ref Yield | 6/7 (1 advice) | 4 (✅ 100% mapped) | 0 / 13 | 1 | **0 (Clean)** |
| 4 | `chilli/dry.json` | **Green Chilli** | dry | 1 | ⚠️ Null (Typical) | ✅ Ref Yield | 5/7 (2 advice) | 5 (✅ 100% mapped) | 0 / 11 | 1 | **0 (Clean)** |
| 5 | `chilli/intermediate.json` | **Green Chilli** | intermediate | 1 | ⚠️ Null (Typical) | ✅ Ref Yield | 5/7 (2 advice) | 5 (✅ 100% mapped) | 0 / 13 | 1 | **0 (Clean)** |
| 6 | `chilli/wet.json` | **Green Chilli** | wet | 1 | ⚠️ Null (Typical) | ✅ Ref Yield | 5/7 (2 advice) | 5 (✅ 100% mapped) | 0 / 12 | 1 | **0 (Clean)** |
| 7 | `cowpea/dry.json` | **Cowpea** | dry | 2 | ✅ Present | ✅ Ref Yield | 7/7 (0 advice) | 4 (✅ 100% mapped) | 0 / 16 | 1 | **0 (Clean)** |
| 8 | `cowpea/intermediate.json` | **Cowpea** | intermediate | 2 | ✅ Present | ✅ Ref Yield | 7/7 (0 advice) | 4 (✅ 100% mapped) | 0 / 16 | 1 | **0 (Clean)** |
| 9 | `finger-millet/dry-intermediate.json` | **Kurakkan** | dry, intermediate | 1 | ⚠️ Null (Typical) | ✅ Ref Yield | 4/4 (0 advice) | 5 (✅ 100% mapped) | 0 / 5 | 1 | **0 (Clean)** |
| 10 | `green-gram/dry.json` | **Green Gram** | dry | 2 | ✅ Present | ✅ Ref Yield | 4/7 (3 advice) | 5 (✅ 100% mapped) | 0 / 15 | 2 | **0 (Clean)** |
| 11 | `green-gram/intermediate.json` | **Green Gram** | intermediate | 2 | ✅ Present | ✅ Ref Yield | 4/7 (3 advice) | 4 (✅ 100% mapped) | 0 / 15 | 2 | **0 (Clean)** |
| 12 | `ground-nut/dry-intermediate.json` | **Groundnut** | dry, intermediate | 1 | ⚠️ Null (Typical) | ✅ Ref Yield | 7/7 (0 advice) | 5 (✅ 100% mapped) | 0 / 5 | 5 | **0 (Clean)** |
| 13 | `maize/dry.json` | **Maize** | dry | 1 | ⚠️ Null (Typical) | ✅ Ref Yield | 9/9 (0 advice) | 5 (✅ 100% mapped) | 0 / 8 | 13 | **0 (Clean)** |
| 14 | `maize/intermediate.json` | **Maize** | intermediate | 1 | ⚠️ Null (Typical) | ✅ Ref Yield | 8/8 (0 advice) | 4 (✅ 100% mapped) | 0 / 4 | 13 | **0 (Clean)** |
| 15 | `paddy/dry-intermediate-irrigated.json` | **Paddy** | dry, intermediate | 1 | ✅ Present | ✅ Ref Yield | 0/34 (34 advice) | 5 (✅ 100% mapped) | 0 / 11 | 0 | **0 (Clean)** |
| 16 | `paddy/dry-intermediate-rainfed.json` | **Paddy** | dry, intermediate | 1 | ✅ Present | ✅ Ref Yield | 0/33 (33 advice) | 5 (✅ 100% mapped) | 0 / 10 | 0 | **0 (Clean)** |
| 17 | `paddy/ipm.json` | **Paddy** |  | 0 | ⚠️ Null (Typical) | ⚠️ None | 0/0 (0 advice) | 0 (✅ 100% mapped) | 0 / 9 | 5 | **0 (Clean)** |
| 18 | `paddy/wet.json` | **Paddy** | wet | 2 | ✅ Present | ✅ Ref Yield | 0/92 (92 advice) | 5 (✅ 100% mapped) | 0 / 12 | 0 | **0 (Clean)** |
| 19 | `potato/dry.json` | **Potato** | dry | 1 | ⚠️ Null (Typical) | ✅ Ref Yield | 10/10 (0 advice) | 4 (✅ 100% mapped) | 0 / 7 | 6 | **0 (Clean)** |
| 20 | `potato/intermediate.json` | **Potato** | intermediate | 2 | ⚠️ Null (Typical) | ✅ Ref Yield | 20/20 (0 advice) | 4 (✅ 100% mapped) | 0 / 9 | 13 | **0 (Clean)** |
| 21 | `potato/wet.json` | **Potato** | wet | 2 | ⚠️ Null (Typical) | ✅ Ref Yield | 20/20 (0 advice) | 4 (✅ 100% mapped) | 0 / 6 | 10 | **0 (Clean)** |
| 22 | `red-onion/dry.json` | **Red Onion** | dry | 2 | ⚠️ Null (Typical) | ✅ Ref Yield | 21/21 (0 advice) | 6 (✅ 100% mapped) | 0 / 7 | 8 | **0 (Clean)** |
| 23 | `red-onion/intermediate.json` | **Red Onion** | intermediate | 2 | ⚠️ Null (Typical) | ✅ Ref Yield | 21/21 (0 advice) | 4 (✅ 100% mapped) | 0 / 7 | 8 | **0 (Clean)** |
| 24 | `sesame/dry-intermediate.json` | **Gingelly** | dry, intermediate | 2 | ⚠️ Null (Typical) | ✅ Ref Yield | 14/14 (0 advice) | 3 (✅ 100% mapped) | 0 / 0 | 8 | **0 (Clean)** |
| 25 | `soya-bean/dry.json` | **Soybean** | dry | 1 | ✅ Present | ✅ Ref Yield | 6/6 (0 advice) | 4 (✅ 100% mapped) | 0 / 14 | 9 | **0 (Clean)** |
| 26 | `soya-bean/intermediate.json` | **Soybean** | intermediate | 1 | ✅ Present | ✅ Ref Yield | 6/6 (0 advice) | 4 (✅ 100% mapped) | 0 / 14 | 9 | **0 (Clean)** |

**Totals & Coverage:**
- **Calendar Files:** 26 (across 13 crops)
- **Economic Data Sanitization:** **119 raw poster economic keys detected -> 0 survived sanitization (100% purged)**. Live calculations use strictly the ML endpoints.
- **Timing String Expressions:** **194 of 395 parsed into structured calendar windows**. 201 general agronomic text strings safely flagged as `parseFailed: true` rather than guessing.
- **Weather Icons:** 7 unique weather states: `rain, sun-rain, sun, thunder, sun-cloud, moderate-rain, rain-thunder`. **Unmapped weather icons: 0** (100% matched to Sky Weather visual system).
- **Pests & Diseases:** 66 unique canonical pests/diseases cataloged across all crops.

---

## 2. Weather Icon Mapping Audit

All weather values extracted from the calendars are mapped to the 3D Sky Dome and particle weather system:

| Raw Calendar Icon | Visual Shader / Particle State | Fallback 2D Icon | Status |
|---|---|---|:---:|
| `sun` | Clear blue sky, intense sun rays, slight lens flare | `Sun` | ✅ Mapped |
| `sun-cloud` | Partly cloudy, drifting cumulus clouds, filtered sunlight | `CloudSun` | ✅ Mapped |
| `sun-rain` | Sun-shower, light rain particles with bright sun lighting | `CloudSunRain` | ✅ Mapped |
| `moderate-rain` | Overcast grey sky, steady moderate rain particles | `CloudRain` | ✅ Mapped |
| `rain` | Deep overcast sky, heavy rain particle emitter, wet surface reflection | `CloudRain` | ✅ Mapped |
| `rain-thunder` | Dark storm clouds, heavy rain, periodic lightning flash shaders | `CloudLightning` | ✅ Mapped |
| `thunder` | Dark thunderstorm sky, distant thunder sound, lightning illumination | `CloudLightning` | ✅ Mapped |

---

## 3. Pest Canonical Catalog & Missing Image Audit

Pests use `canonical_name` for asset lookup while displaying `verbatim_text` as the farmer label. Where an illustrated asset is missing, the fallback system presents an illustrated pest card with icon and agronomic advice, and registers the asset in `ASSETS_NEEDED.md`.

Total cataloged canonical pests across all 26 calendars: **66**

| # | Canonical Name | Crop Sample | Verbatim Display Label | Illustrated Image File | Asset Status |
|---|---|---|---|---|:---:|
| 1 | `purple_blotch` | pest | "Purple blotch" | `images/pests/purple_blotch.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 2 | `anthracnose` | pest | "Anthracnose" | `images/pests/anthracnose.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 3 | `fungal_bulb_rot` | pest | "Fungal bulb rot" | `images/pests/fungal_bulb_rot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 4 | `bacterial_bulb_rot` | pest | "Bacteria bulb rot" | `images/pests/bacterial_bulb_rot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 5 | `big_onion_caterpillar` | pest | "Big onion caterpillar" | `images/pests/big_onion_caterpillar.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 6 | `collar_rot` | pest | "Collar rot" | `images/pests/collar_rot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 7 | `powdery_mildew` | pest | "Powdery mildew" | `images/pests/powdery_mildew.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 8 | `cercospora_leaf_spot` | pest | "Cercospora leaf spot" | `images/pests/cercospora_leaf_spot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 9 | `pod_borer` | pest | "Pod borer" | `images/pests/pod_borer.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 10 | `mosaic_virus` | pest | "Mosaic Virus" | `images/pests/mosaic_virus.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 11 | `whitefly` | pest | "White fly" | `images/pests/whitefly.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 12 | `aphids` | pest | "Aphids" | `images/pests/aphids.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 13 | `mites` | pest | "Mites" | `images/pests/mites.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 14 | `leafhopper` | pest | "Leaf Hopper" | `images/pests/leafhopper.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 15 | `bean_fly` | pest | "Bean fly" | `images/pests/bean_fly.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 16 | `blister_beetle` | pest | "Blister beetle" | `images/pests/blister_beetle.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 17 | `bruchids` | pest | "Bruchids" | `images/pests/bruchids.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 18 | `damping_off` | pest | "Damping off" | `images/pests/damping_off.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 19 | `virus` | pest | "Virus" | `images/pests/virus.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 20 | `leaf_spot` | pest | "Leaf spot" | `images/pests/leaf_spot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 21 | `choanephora_blight` | pest | "Choanephora blight" | `images/pests/choanephora_blight.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 22 | `thrips` | pest | "Thrips" | `images/pests/thrips.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 23 | `chilli_leaf_curl_complex` | pest | "Leaf curl complex" | `images/pests/chilli_leaf_curl_complex.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 24 | `bacterial_wilt` | pest | "Bacteria wilt" | `images/pests/bacterial_wilt.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 25 | `ascochyta_blight` | pest | "Ascochyta blight" | `images/pests/ascochyta_blight.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 26 | `wilt` | pest | "Wilt" | `images/pests/wilt.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 27 | `planthopper` | pest | "Plant hopper" | `images/pests/planthopper.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 28 | `pod_sucking_bug` | pest | "Pod sucking bug" | `images/pests/pod_sucking_bug.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 29 | `blast` | pest | "Blast" | `images/pests/blast.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 30 | `stem_borer` | pest | "Stem borer" | `images/pests/stem_borer.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 31 | `brown_spot` | pest | "Brown spot" | `images/pests/brown_spot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 32 | `erwinia_collar_rot` | pest | "Arvinia Collar rot" | `images/pests/erwinia_collar_rot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 33 | `cercospora_brown_spot` | pest | "Cercospora brown spot" | `images/pests/cercospora_brown_spot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 34 | `anthracnose_brown_spot` | pest | "Anthracnose brown spot" | `images/pests/anthracnose_brown_spot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 35 | `mung_bean_mosaic_virus` | pest | "Mung bean mosaic virus" | `images/pests/mung_bean_mosaic_virus.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 36 | `bruchid` | pest | "Bruchid" | `images/pests/bruchid.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 37 | `rust` | pest | "Rust" | `images/pests/rust.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 38 | `bud_rot` | pest | "Bud rot" | `images/pests/bud_rot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 39 | `penicillium_seedling_blight` | pest | "Penicillium seedling blight" | `images/pests/penicillium_seedling_blight.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 40 | `erwinia_stalk_rot` | pest | "Erwinia stalk rot disease" | `images/pests/erwinia_stalk_rot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 41 | `brown_leaf_spot` | pest | "Brown leaf spot" | `images/pests/brown_leaf_spot.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 42 | `sheath_rot_blight` | pest | "Sheath rot blight" | `images/pests/sheath_rot_blight.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 43 | `gall_midge` | pest | "Gall midge" | `images/pests/gall_midge.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 44 | `leaf_rolling_caterpillar` | pest | "Leaf rolling caterpiller" | `images/pests/leaf_rolling_caterpillar.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 45 | `white_backed_planthopper` | pest | "White back hopper" | `images/pests/white_backed_planthopper.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 46 | `sheath_and_leaf_mites` | pest | "Sheath & leaf mites" | `images/pests/sheath_and_leaf_mites.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 47 | `rice_blast` | pest | "Blast" | `images/pests/rice_blast.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 48 | `bacterial_sheath_blight` | pest | "Bacterial sheath blight" | `images/pests/bacterial_sheath_blight.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 49 | `brown_planthopper` | pest | "Brown plant hopper" | `images/pests/brown_planthopper.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 50 | `paddy_bug` | pest | "Paddy bug" | `images/pests/paddy_bug.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 51 | `bph` | pest | "Brown Planthopper" | `images/pests/bph.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 52 | `leaf_folder` | pest | "Rice Leaf Folder" | `images/pests/leaf_folder.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 53 | `field_rat` | pest | "Rice Field Rat" | `images/pests/field_rat.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 54 | `sheath_mite` | pest | "Rice Sheath Mite" | `images/pests/sheath_mite.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 55 | `leaf_mite` | pest | "Rice Leaf Mite" | `images/pests/leaf_mite.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 56 | `bacterial sheath blights` | pest | "Bacterial sheath blights" | `images/pests/bacterial sheath blights.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 57 | `leaf_eating_caterpillar` | pest | "Leaf eating caterpillar" | `images/pests/leaf_eating_caterpillar.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 58 | `blight` | pest | "Blight" | `images/pests/blight.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 59 | `leaf_miner` | pest | "Leaf miner" | `images/pests/leaf_miner.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 60 | `white_mold` | pest | "White mold" | `images/pests/white_mold.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 61 | `cut_worms` | pest | "Cut worms" | `images/pests/cut_worms.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 62 | `late_blight` | pest | "Late Blight and Early blight" | `images/pests/late_blight.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 63 | `white_fly` | pest | "White fly" | `images/pests/white_fly.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 64 | `black_leg` | pest | "Black leg disease" | `images/pests/black_leg.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 65 | `purple_seed_stain` | pest | "Purple seed stain" | `images/pests/purple_seed_stain.webp` | ⚠️ Needed in ASSETS_NEEDED.md |
| 66 | `leaf_hopper` | pest | "Leaf hopper" | `images/pests/leaf_hopper.webp` | ⚠️ Needed in ASSETS_NEEDED.md |

---

## 4. Detailed Per-File Audit

### Big Onion (Big Onion) — `big-onion/dry-intermediate.json`
- **Zones:** dry, intermediate | **Irrigation:** irrigated | **Source Year:** 2013 (data-source/rgb/Big Onion/BIg-onion-Dry-Inter-E.png)
- **Regions Count:** 18 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 0 ()
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Season Bulb Cultivation (Yala)** (`main`): 8 varieties. Derived Yield: none
    - Variety *Kalpitiya Selection*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Pusa Red*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Rampur*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Nasic Red*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *N 53*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Asrifound Light Red*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Dambulla Selection*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Galewela Selection*: duration = `null`, yield = `8800-8800 kg/ac`
  - **Off-Season Bulb Cultivation (Maha)** (`off_season`): 8 varieties. Derived Yield: none
    - Variety *Kalpitiya Selection*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Pusa Red*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Rampur*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Nasic Red*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *N 53*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Asrifound Light Red*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Dambulla Selection*: duration = `null`, yield = `8800-8800 kg/ac`
    - Variety *Galewela Selection*: duration = `null`, yield = `8800-8800 kg/ac`
  - **True Seed Production** (`true_seed`): 8 varieties. Derived Yield: none
    - Variety *Kalpitiya Selection*: duration = `null`, yield = `null`
    - Variety *Pusa Red*: duration = `null`, yield = `null`
    - Variety *Rampur*: duration = `null`, yield = `null`
    - Variety *Nasic Red*: duration = `null`, yield = `null`
    - Variety *N 53*: duration = `null`, yield = `null`
    - Variety *Asrifound Light Red*: duration = `null`, yield = `null`
    - Variety *Dambulla Selection*: duration = `null`, yield = `null`
    - Variety *Galewela Selection*: duration = `null`, yield = `null`
- **Timing Details:** 0 parsed cleanly. 27 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Nursery establishment starting mid-March (15th March printed)" (Nurseries)
    - "Weedicide applied during nursery stage" (Application of Pre-Emergent Weedicide)
    - "Field preparation in April" (Land Preparation)
    - "Application of organic manure prior to basal dressing" (Organic Fertilizer)
    - "Basal fertilizer application before planting" (Basal Dressing)
    - ...and 22 more descriptive advice items.
- **Weather Icons:** `rain, sun-rain, sun, thunder, sun-cloud`
- **Pests & Diseases Count:** 5 items cataloged

### Black Gram (Black Gram) — `black-gram/dry.json`
- **Zones:** dry | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Black Gram/Blackgram_DRY.png)
- **Regions Count:** 12 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 1 (selling_price_rs_per_kg)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 2 varieties. Derived Yield: none
    - Variety *MI - 1*: duration = `90d`, yield = `465-465 kg/ac`
    - Variety *Anuradha*: duration = `65-70d`, yield = `465-465 kg/ac`
  - **Third Season Cultivation** (`third_season`): 2 varieties. Derived Yield: none
    - Variety *MI - 1*: duration = `90d`, yield = `465-465 kg/ac`
    - Variety *Anuradha*: duration = `65-70d`, yield = `465-465 kg/ac`
- **Timing Details:** 5 parsed cleanly. 2 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Relay broadcasting into post-harvest rice stubble late March to early April" (Direct Seeding / Broadcasting into Stubble)
    - "Harvesting in mid-to-late June" (Harvesting)
- **Weather Icons:** `sun-cloud, rain, sun-rain, sun, thunder`
- **Pests & Diseases Count:** 13 items cataloged

### Black Gram (Black Gram) — `black-gram/intermediate.json`
- **Zones:** intermediate | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Black Gram/Blackgram_INTER.png)
- **Regions Count:** 3 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 1 (selling_price_rs_per_kg)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 2 varieties. Derived Yield: none
    - Variety *MI - 1*: duration = `90d`, yield = `465-465 kg/ac`
    - Variety *Anuradha*: duration = `65-70d`, yield = `465-465 kg/ac`
  - **Third Season Cultivation** (`third_season`): 2 varieties. Derived Yield: none
    - Variety *MI - 1*: duration = `90d`, yield = `465-465 kg/ac`
    - Variety *Anuradha*: duration = `65-70d`, yield = `465-465 kg/ac`
- **Timing Details:** 6 parsed cleanly. 1 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Harvesting in late August to early September" (Harvesting)
- **Weather Icons:** `sun-cloud, rain, sun, thunder`
- **Pests & Diseases Count:** 13 items cataloged

### Chilli (Green Chilli) — `chilli/dry.json`
- **Zones:** dry | **Irrigation:** irrigated, rainfed | **Source Year:** 2013 (data-source/rgb/Chilli/Chilli_Dry.png)
- **Regions Count:** 14 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 1 (selling_price_rs_per_kg)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 6 varieties. Derived Yield: none
    - Variety *M.I 2*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *K.A 2*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *M.I. Green*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *Galkiriyagama Selection*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *I Veraniya 01*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *M.I.C.H -3*: duration = `null`, yield = `1600-1600 kg/ac`
- **Timing Details:** 5 parsed cleanly. 2 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Organic fertilizer and basal chemical dressing applied 3 days before planting" (Organic Fertilizer & Basal Dressing)
    - "Top dressings at 2, 4, 8, 12, 16 weeks after planting with mechanical weed control" (Mechanical Control & Top Dressing)
- **Weather Icons:** `sun-cloud, rain, sun-rain, sun, thunder`
- **Pests & Diseases Count:** 11 items cataloged

### Chilli (Green Chilli) — `chilli/intermediate.json`
- **Zones:** intermediate | **Irrigation:** irrigated, rainfed | **Source Year:** 2013 (data-source/rgb/Chilli/inter-chilli-english.png)
- **Regions Count:** 9 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 1 (selling_price_rs_per_kg)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 6 varieties. Derived Yield: none
    - Variety *M.I 2*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *K.A 2*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *M.I. Green*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *Galkiriyagama Selection*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *I Veraniya 01*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *M.I.C.H -3*: duration = `null`, yield = `1600-1600 kg/ac`
- **Timing Details:** 5 parsed cleanly. 2 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Organic fertilizer and basal chemical dressing applied 3 days before planting" (Application of Organic Fertilizer & Basal Dressing)
    - "Top dressings at 2, 4, 8, 12, 16 weeks after planting with mechanical weed control" (Mechanical Control & Top Dressing)
- **Weather Icons:** `sun-cloud, rain, sun-rain, sun, thunder`
- **Pests & Diseases Count:** 13 items cataloged

### Chilli (Green Chilli) — `chilli/wet.json`
- **Zones:** wet | **Irrigation:** irrigated, rainfed | **Source Year:** 2013 (data-source/rgb/Chilli/Chili_wet.png)
- **Regions Count:** 5 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 1 (selling_price_rs_per_kg)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Alternative Cropping Cultivation (Maha & Yala)** (`main`): 6 varieties. Derived Yield: none
    - Variety *M.I 2*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *K.A 2*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *M.I. Green*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *Galkiriyagama Selection*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *I veraniya 01*: duration = `null`, yield = `1600-1600 kg/ac`
    - Variety *M.I.C.H -3*: duration = `null`, yield = `1600-1600 kg/ac`
- **Timing Details:** 5 parsed cleanly. 2 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Organic fertilizer application and basal chemical dressing applied 3 days before planting" (Organic Fertilizer Application & Basal Dressing)
    - "Top dressings at 2, 4, 8, 12, 16 weeks after planting with mechanical weed control" (Mechanical Control & Top Dressing)
- **Weather Icons:** `sun-cloud, rain, sun-rain, sun, thunder`
- **Pests & Diseases Count:** 12 items cataloged

### Cowpea (Cowpea) — `cowpea/dry.json`
- **Zones:** dry | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Cowpea/Cowpea_DRY.png)
- **Regions Count:** 14 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 1 (selling_price_rs_per_kg)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 5 varieties. Derived Yield: 400 kg/ac (DOA reference yield)
    - Variety *MI -35*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *Dhawala*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *Waruni*: duration = `55d`, yield = `380-400 kg/ac`
    - Variety *Bombe*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *MICP*: duration = `null`, yield = `380-400 kg/ac`
  - **Third Season / Paddy Field Stubble Cultivation** (`third_season`): 5 varieties. Derived Yield: none
    - Variety *MI -35*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *Dhawala*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *Waruni*: duration = `55d`, yield = `380-400 kg/ac`
    - Variety *Bombe*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *MICP*: duration = `null`, yield = `380-400 kg/ac`
- **Timing Details:** 7 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `sun-cloud, rain, sun, thunder`
- **Pests & Diseases Count:** 16 items cataloged

### Cowpea (Cowpea) — `cowpea/intermediate.json`
- **Zones:** intermediate | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Cowpea/Cowpea_INTER.png)
- **Regions Count:** 11 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 1 (selling_price_rs_per_kg)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 5 varieties. Derived Yield: 400 kg/ac (DOA reference yield)
    - Variety *MI -35*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *Dhawala*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *Waruni*: duration = `55d`, yield = `380-400 kg/ac`
    - Variety *Bombe*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *MICP*: duration = `null`, yield = `380-400 kg/ac`
  - **Third Season / Paddy Field Stubble Cultivation** (`third_season`): 5 varieties. Derived Yield: none
    - Variety *MI -35*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *Dhawala*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *Waruni*: duration = `55d`, yield = `380-400 kg/ac`
    - Variety *Bombe*: duration = `null`, yield = `380-400 kg/ac`
    - Variety *MICP*: duration = `null`, yield = `380-400 kg/ac`
- **Timing Details:** 7 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `sun-cloud, rain, sun, thunder`
- **Pests & Diseases Count:** 16 items cataloged

### Finger Millet (Kurakkan) — `finger-millet/dry-intermediate.json`
- **Zones:** dry, intermediate | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Finger Millet/fingerMillet_dryinter-1024x757.png)
- **Regions Count:** 15 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 1 (selling_price_rs_per_kg)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 3 varieties. Derived Yield: 530 kg/ac (DOA reference yield)
    - Variety *Ravi*: duration = `null`, yield = `530-530 kg/ac`
    - Variety *Ravana*: duration = `null`, yield = `530-530 kg/ac`
    - Variety *Oshadi*: duration = `null`, yield = `530-530 kg/ac`
- **Timing Details:** 4 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `rain, sun-rain, sun, thunder, sun-cloud`
- **Pests & Diseases Count:** 5 items cataloged

### Green Gram (Green Gram) — `green-gram/dry.json`
- **Zones:** dry | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Green Gram/GreenGram_DRY.png)
- **Regions Count:** 18 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 2 (selling_price_rs_per_kg, Printed seed rate 30 kg/ha (~1)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 4 varieties. Derived Yield: 400 kg/ac (DOA reference yield)
    - Variety *MI -5*: duration = `60-65d`, yield = `607-607 kg/ac`
    - Variety *Ari*: duration = `60-65d`, yield = `648-648 kg/ac`
    - Variety *Harsha*: duration = `55-60d`, yield = `486-486 kg/ac`
    - Variety *MI-6*: duration = `55-58d`, yield = `728-728 kg/ac`
  - **Third Season / Mid-Season Cultivation** (`third_season`): 4 varieties. Derived Yield: none
    - Variety *MI-6*: duration = `55-58d`, yield = `728-728 kg/ac`
    - Variety *Harsha*: duration = `55-60d`, yield = `486-486 kg/ac`
    - Variety *MI -5*: duration = `60-65d`, yield = `607-607 kg/ac`
    - Variety *Ari*: duration = `60-65d`, yield = `648-648 kg/ac`
- **Timing Details:** 4 parsed cleanly. 3 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Land preparation for mid season in rice fallows" (Land Preparation / Field Clearing)
    - "Seeding with residual moisture or light irrigation" (Seeding & Basal Dressing)
    - "Harvesting mid-season green gram" (Harvesting)
- **Weather Icons:** `rain, sun-rain, sun, thunder, sun-cloud`
- **Pests & Diseases Count:** 15 items cataloged

### Green Gram (Green Gram) — `green-gram/intermediate.json`
- **Zones:** intermediate | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Green Gram/GreenGram_INTER.png)
- **Regions Count:** 11 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 2 (selling_price_rs_per_kg, Printed seed rate 30 kg/ha (~1)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 4 varieties. Derived Yield: 400 kg/ac (DOA reference yield)
    - Variety *MI -5*: duration = `60-65d`, yield = `607-607 kg/ac`
    - Variety *Ari*: duration = `60-65d`, yield = `648-648 kg/ac`
    - Variety *Harsha*: duration = `55-60d`, yield = `486-486 kg/ac`
    - Variety *MI-6*: duration = `55-58d`, yield = `728-728 kg/ac`
  - **Third Season / Mid-Season Cultivation** (`third_season`): 4 varieties. Derived Yield: none
    - Variety *MI-6*: duration = `55-58d`, yield = `728-728 kg/ac`
    - Variety *Harsha*: duration = `55-60d`, yield = `486-486 kg/ac`
    - Variety *MI -5*: duration = `60-65d`, yield = `607-607 kg/ac`
    - Variety *Ari*: duration = `60-65d`, yield = `648-648 kg/ac`
- **Timing Details:** 4 parsed cleanly. 3 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Land preparation for mid season in rice fallows" (Land Preparation / Field Clearing)
    - "Seeding with residual moisture or light irrigation" (Seeding & Basal Dressing)
    - "Harvesting mid-season green gram" (Harvesting)
- **Weather Icons:** `rain, sun, thunder, sun-cloud`
- **Pests & Diseases Count:** 15 items cataloged

### Ground Nut (Groundnut) — `ground-nut/dry-intermediate.json`
- **Zones:** dry, intermediate | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Ground Nut/groundNut.png)
- **Regions Count:** 16 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 5 (selling_price_rs_per_kg, cost_of_cultivation_acre_rs, income, gross_profit_including_family_labour, gross_profit_excluding_family_labour)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 4 varieties. Derived Yield: 700 kg/ac (DOA reference yield)
    - Variety *Walawa*: duration = `null`, yield = `700-700 kg/ac`
    - Variety *Indi*: duration = `null`, yield = `700-700 kg/ac`
    - Variety *Thissa*: duration = `null`, yield = `700-700 kg/ac`
    - Variety *Tikiri*: duration = `null`, yield = `700-700 kg/ac`
- **Timing Details:** 7 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `sun, thunder, rain, sun-rain, sun-cloud`
- **Pests & Diseases Count:** 5 items cataloged

### Maize (Maize) — `maize/dry.json`
- **Zones:** dry | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Maize/maiz_dry.png)
- **Regions Count:** 14 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 13 (Open-pollinated variety. Seed , Hybrid varieties (Pacific, Sam, cost_of_cultivation_acre_rs, expenditure_rainfed, expenditure_irrigated...)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 4 varieties. Derived Yield: none
    - Variety *Ruwan*: duration = `null`, yield = `2000-3000 kg/ac`
    - Variety *Bhadra*: duration = `null`, yield = `2000-3000 kg/ac`
    - Variety *Aruna*: duration = `null`, yield = `2000-3000 kg/ac`
    - Variety *Pacific or any other Hybrids*: duration = `null`, yield = `2000-3000 kg/ac`
- **Timing Details:** 9 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `sun, thunder, rain, sun-cloud, sun-rain`
- **Pests & Diseases Count:** 8 items cataloged

### Maize (Maize) — `maize/intermediate.json`
- **Zones:** intermediate | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Maize/maiz_inter.png)
- **Regions Count:** 8 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 13 (Open-pollinated variety. Seed , Hybrid varieties (Pacific/Pasi, cost_of_cultivation_acre_rs, expenditure_rainfed, expenditure_irrigated...)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Cultivation (Maha & Yala)** (`main`): 4 varieties. Derived Yield: none
    - Variety *Ruwan*: duration = `null`, yield = `2000-3000 kg/ac`
    - Variety *Badhara*: duration = `null`, yield = `2000-3000 kg/ac`
    - Variety *Aruna*: duration = `null`, yield = `2000-3000 kg/ac`
    - Variety *Pasific or any other*: duration = `null`, yield = `2000-3000 kg/ac`
- **Timing Details:** 8 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `sun, thunder, rain, sun-cloud`
- **Pests & Diseases Count:** 4 items cataloged

### Paddy (Paddy) — `paddy/dry-intermediate-irrigated.json`
- **Zones:** dry, intermediate | **Irrigation:** irrigated | **Source Year:** 2015 (data-source/rgb/Paddy/paddy-DRYINTER_Irrigated_English-scaled.png)
- **Regions Count:** 0 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 0 ()
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Double Cropping Irrigated (Maha & Yala)** (`main`): 13 varieties. Derived Yield: none
    - Variety *Bg 250*: duration = `80d`, yield = `1400-1800 kg/ac`
    - Variety *Bg 251 GSR*: duration = `80d`, yield = `1400-1800 kg/ac`
    - Variety *Bg 300*: duration = `90d`, yield = `1800-2200 kg/ac`
    - Variety *At 307*: duration = `90d`, yield = `1800-2200 kg/ac`
    - Variety *At 308*: duration = `90d`, yield = `1600-2000 kg/ac`
    - Variety *Bg 310*: duration = `90d`, yield = `1800-2200 kg/ac`
    - Variety *Bg 352*: duration = `105d`, yield = `2000-2400 kg/ac`
    - Variety *Bg 357*: duration = `105d`, yield = `1600-2000 kg/ac`
    - Variety *Bg 358*: duration = `105d`, yield = `1800-2200 kg/ac`
    - Variety *Bg 360*: duration = `105d`, yield = `1800-2000 kg/ac`
    - Variety *At 362*: duration = `105d`, yield = `2200-2600 kg/ac`
    - Variety *At 366*: duration = `105d`, yield = `2000-2400 kg/ac`
    - Variety *Bw 367*: duration = `105d`, yield = `1800-2000 kg/ac`
- **Timing Details:** 0 parsed cleanly. 34 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Spreading straw in field read from tile" (Appling straw)
    - "First plowing read from tile" (Primary land preparation)
    - "Organic fertilizer application read from tile" (Appling leaf manure cow dung & paddy husk)
    - "Second plowing and rotovation read from tile" (Secondary land preparation)
    - "Field levelling, basal fertilizer application and seed broadcasting read from tile" (Levelling, Appling basal fertilizer & Seed broadcasting)
    - ...and 29 more descriptive advice items.
- **Weather Icons:** `sun-cloud, thunder, rain, moderate-rain, sun`
- **Pests & Diseases Count:** 11 items cataloged

### Paddy (Paddy) — `paddy/dry-intermediate-rainfed.json`
- **Zones:** dry, intermediate | **Irrigation:** rainfed | **Source Year:** 2015 (data-source/rgb/Paddy/paddy-DRYINTER_Rainfed_English-scaled.png)
- **Regions Count:** 0 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 0 ()
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Double Cropping Rainfed (Maha & Yala)** (`main`): 10 varieties. Derived Yield: none
    - Variety *Bg 250*: duration = `80d`, yield = `1200-1400 kg/ac`
    - Variety *Bg 251 GSR*: duration = `80d`, yield = `1200-1400 kg/ac`
    - Variety *Bg 300*: duration = `90d`, yield = `1400-1600 kg/ac`
    - Variety *Bg 304*: duration = `90d`, yield = `1200-1400 kg/ac`
    - Variety *Bg 310*: duration = `90d`, yield = `1400-1600 kg/ac`
    - Variety *Bg 352*: duration = `105d`, yield = `1600-1800 kg/ac`
    - Variety *Bg 358*: duration = `105d`, yield = `1400-1600 kg/ac`
    - Variety *Bg 359*: duration = `105d`, yield = `1600-1800 kg/ac`
    - Variety *At 367*: duration = `105d`, yield = `1600-1800 kg/ac`
    - Variety *At 369*: duration = `105d`, yield = `1600-1800 kg/ac`
- **Timing Details:** 0 parsed cleanly. 33 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Spreading straw in field read from tile" (Appling straw)
    - "First plowing with seasonal rains read from tile" (Primary land preparation)
    - "Organic fertilizer application read from tile" (Appling leaf manure cow dung & paddy husk)
    - "Second plowing and rotovation read from tile" (Secondary land preparation)
    - "Field levelling, basal fertilizer application and seed broadcasting read from tile" (Levelling, Appling basal dressing & Seed broadcasting)
    - ...and 28 more descriptive advice items.
- **Weather Icons:** `sun-cloud, thunder, rain, moderate-rain, sun`
- **Pests & Diseases Count:** 10 items cataloged

### Paddy (Paddy) — `paddy/ipm.json`
- **Zones:**  | **Irrigation:**  | **Source Year:** 2015 (data-source/rgb/Paddy/IPMcalender.png)
- **Regions Count:** 0 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 5 (Strong winds, high rainfall, s, Planthoppers, leafhoppers, ste, Planthoppers, leaf folder moth, Rice leaf folder caterpillars,, Planthoppers, leafhoppers, sma)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
- **Timing Details:** 0 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `None`
- **Pests & Diseases Count:** 9 items cataloged

### Paddy (Paddy) — `paddy/wet.json`
- **Zones:** wet | **Irrigation:** irrigated, rainfed | **Source Year:** 2015 (data-source/rgb/Paddy/paddy-WET_English_New-scaled.png)
- **Regions Count:** 2 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 0 ()
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Wet Zone Irrigated Cultivation** (`main`): 13 varieties. Derived Yield: none
    - Variety *Bg 250*: duration = `80d`, yield = `1000-1200 kg/ac`
    - Variety *Bg 251 GSR*: duration = `80d`, yield = `1000-1200 kg/ac`
    - Variety *Bg 300*: duration = `90d`, yield = `1200-1400 kg/ac`
    - Variety *Bw 272-6b*: duration = `90d`, yield = `1000-1200 kg/ac`
    - Variety *Bg 310*: duration = `90d`, yield = `1200-1400 kg/ac`
    - Variety *Bg 359*: duration = `105d`, yield = `1400-1600 kg/ac`
    - Variety *Bw 361*: duration = `105d`, yield = `1200-1400 kg/ac`
    - Variety *At 362*: duration = `105d`, yield = `1600-1800 kg/ac`
    - Variety *Ld 365*: duration = `105d`, yield = `1200-1400 kg/ac`
    - Variety *Bw 367*: duration = `105d`, yield = `1400-1600 kg/ac`
    - Variety *Bw 372*: duration = `105d`, yield = `1400-1600 kg/ac`
    - Variety *Bg 379-2*: duration = `120-135d`, yield = `1600-1800 kg/ac`
    - Variety *Bg 455*: duration = `120-135d`, yield = `1400-1600 kg/ac`
  - **Wet Zone Rainfed Cultivation** (`alternative`): 13 varieties. Derived Yield: none
    - Variety *Bg 250*: duration = `80d`, yield = `1000-1200 kg/ac`
    - Variety *Bg 251 GSR*: duration = `80d`, yield = `1000-1200 kg/ac`
    - Variety *Bg 300*: duration = `90d`, yield = `1200-1400 kg/ac`
    - Variety *Bw 272-6b*: duration = `90d`, yield = `1000-1200 kg/ac`
    - Variety *Bg 310*: duration = `90d`, yield = `1200-1400 kg/ac`
    - Variety *Bg 359*: duration = `105d`, yield = `1400-1600 kg/ac`
    - Variety *Bw 361*: duration = `105d`, yield = `1200-1400 kg/ac`
    - Variety *At 362*: duration = `105d`, yield = `1600-1800 kg/ac`
    - Variety *Ld 365*: duration = `105d`, yield = `1200-1400 kg/ac`
    - Variety *Bw 367*: duration = `105d`, yield = `1400-1600 kg/ac`
    - Variety *Bw 372*: duration = `105d`, yield = `1400-1600 kg/ac`
    - Variety *Bg 379-2*: duration = `120-135d`, yield = `1600-1800 kg/ac`
    - Variety *Bg 455*: duration = `120-135d`, yield = `1400-1600 kg/ac`
- **Timing Details:** 0 parsed cleanly. 92 non-week agronomic advice strings safely flagged `parseFailed: true`.
  - *Non-week details strings (flagged approximate advice):*
    - "Spreading straw in field read from tile" (Appling straw)
    - "First plowing read from tile" (Primary land preparation)
    - "Organic fertilizer application read from tile" (Appling leaf manure cow dung & paddy husk)
    - "Second plowing and rotovation read from tile" (Secondary land preparation)
    - "Levelling, basal fertilizer application and seed broadcasting read from tile" (Levelling, Appling basal fertilizer & Seed broadcasting)
    - ...and 87 more descriptive advice items.
- **Weather Icons:** `sun-cloud, rain, moderate-rain, sun, thunder`
- **Pests & Diseases Count:** 12 items cataloged

### Potato (Potato) — `potato/dry.json`
- **Zones:** dry | **Irrigation:** irrigated | **Source Year:** 2013 (data-source/rgb/Potato/POTATO_-Dry-jaffna-Kalpitiya.png)
- **Regions Count:** 2 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 6 (selling_price_rs_per_kg, total_expenditure_including_family_rs, total_expenditure_excluding_family_rs, income_rs, gross_profit_including_family_rs...)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Maha Season Upland Cultivation (Jaffna & Kalpitiya)** (`main`): 4 varieties. Derived Yield: 16000 kg/ac (DOA reference yield)
    - Variety *Calwhite*: duration = `null`, yield = `16000-16000 kg/ac`
    - Variety *Redlasoda*: duration = `null`, yield = `16000-16000 kg/ac`
    - Variety *Arnova*: duration = `null`, yield = `16000-16000 kg/ac`
    - Variety *Desiree*: duration = `null`, yield = `16000-16000 kg/ac`
- **Timing Details:** 10 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `rain, sun-cloud, sun, thunder`
- **Pests & Diseases Count:** 7 items cataloged

### Potato (Potato) — `potato/intermediate.json`
- **Zones:** intermediate | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Potato/POTATO_-Inter-badulla.png)
- **Regions Count:** 1 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 13 (selling_price_rs_per_kg, total_expenditure_including_family_rs, total_expenditure_excluding_family_rs, income_rs, gross_profit_including_family_rs...)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Upland Potato Cultivation (Maha Season)** (`main`): 6 varieties. Derived Yield: 6000 kg/ac (DOA reference yield)
    - Variety *Desiree (Red)*: duration = `null`, yield = `6000-6000 kg/ac`
    - Variety *Granola*: duration = `null`, yield = `6000-6000 kg/ac`
    - Variety *Rudolph (Red)*: duration = `null`, yield = `6000-6000 kg/ac`
    - Variety *Arnova*: duration = `null`, yield = `6000-6000 kg/ac`
    - Variety *Redlasoda (Red)*: duration = `null`, yield = `6000-6000 kg/ac`
    - Variety *Condor*: duration = `null`, yield = `6000-6000 kg/ac`
  - **Paddy Field Potato Cultivation (Yala Season)** (`main`): 6 varieties. Derived Yield: 6000 kg/ac (DOA reference yield)
    - Variety *Desiree (Red)*: duration = `null`, yield = `6000-6000 kg/ac`
    - Variety *Granola*: duration = `null`, yield = `6000-6000 kg/ac`
    - Variety *Rudolph (Red)*: duration = `null`, yield = `6000-6000 kg/ac`
    - Variety *Arnova*: duration = `null`, yield = `6000-6000 kg/ac`
    - Variety *Redlasoda (Red)*: duration = `null`, yield = `6000-6000 kg/ac`
    - Variety *Condor*: duration = `null`, yield = `6000-6000 kg/ac`
- **Timing Details:** 20 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `rain, sun, thunder, sun-cloud`
- **Pests & Diseases Count:** 9 items cataloged

### Potato (Potato) — `potato/wet.json`
- **Zones:** wet | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Potato/POTATO_Wet-Nuwaraeliya.png)
- **Regions Count:** 3 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 10 (selling_price_rs_per_kg, expenditure_rs, income_printed_rs, income_calculated_rs, net_profit_rs...)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Upland Potato Cultivation (Maha & Yala Seasons)** (`main`): 8 varieties. Derived Yield: 8000 kg/ac (DOA reference yield)
    - Variety *Granola*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Desiree (Red)*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Hillstar*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Golden Star*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Bio Gold*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Rodulph (Red)*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Calwhite*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Connect*: duration = `null`, yield = `8000-8000 kg/ac`
  - **Paddy Field Potato Cultivation (Yala Season)** (`main`): 8 varieties. Derived Yield: 8000 kg/ac (DOA reference yield)
    - Variety *Granola*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Desiree (Red)*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Hillstar*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Golden Star*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Bio Gold*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Rodulph (Red)*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Calwhite*: duration = `null`, yield = `8000-8000 kg/ac`
    - Variety *Connect*: duration = `null`, yield = `8000-8000 kg/ac`
- **Timing Details:** 20 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `sun, sun-cloud, rain, thunder`
- **Pests & Diseases Count:** 6 items cataloged

### Red Onion (Red Onion) — `red-onion/dry.json`
- **Zones:** dry | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Red Onion/redonion_dry.png)
- **Regions Count:** 18 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 8 (cost_of_production_ha_rs, expenditures_without_family_labour, expenditures_with_family_labour, selling_price_rs_per_kg, net_income...)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Agricultural Activities (Bulb Crop - Maha & Yala)** (`main`): 4 varieties. Derived Yield: none
    - Variety *Jaffna*: duration = `null`, yield = `1376-1376 kg/ac`
    - Variety *Vedalan*: duration = `null`, yield = `1376-1376 kg/ac`
    - Variety *Thirunalvely Red*: duration = `null`, yield = `1376-1376 kg/ac`
    - Variety *Thelulla Selection*: duration = `null`, yield = `1376-1376 kg/ac`
  - **True Seed Production (Mother Bulb Planting & Seed Harvesting - Maha & Yala)** (`true_seed`): 4 varieties. Derived Yield: none
    - Variety *Jaffna*: duration = `null`, yield = `null`
    - Variety *Vedalan*: duration = `null`, yield = `null`
    - Variety *Thirunalvely Red*: duration = `null`, yield = `null`
    - Variety *Thelulla Selection*: duration = `null`, yield = `null`
- **Timing Details:** 21 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `rain, sun-rain, sun, thunder, rain-thunder, sun-cloud`
- **Pests & Diseases Count:** 7 items cataloged

### Red Onion (Red Onion) — `red-onion/intermediate.json`
- **Zones:** intermediate | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Red Onion/RedOnion_inter.png)
- **Regions Count:** 8 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 8 (cost_of_production_ha_rs, expenditures_without_family_labour, expenditures_with_family_labour, selling_price_rs_per_kg, net_income...)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Agricultural Activities (Bulb Crop - Maha & Yala)** (`main`): 4 varieties. Derived Yield: none
    - Variety *Jaffna*: duration = `null`, yield = `1376-1376 kg/ac`
    - Variety *Vedalan*: duration = `null`, yield = `1376-1376 kg/ac`
    - Variety *Thirunavely Red*: duration = `null`, yield = `1376-1376 kg/ac`
    - Variety *Thelulla selection*: duration = `null`, yield = `1376-1376 kg/ac`
  - **True Seed Production (Mother Bulb Planting & Seed Harvesting - Maha & Yala)** (`true_seed`): 4 varieties. Derived Yield: none
    - Variety *Jaffna*: duration = `null`, yield = `null`
    - Variety *Vedalan*: duration = `null`, yield = `null`
    - Variety *Thirunavely Red*: duration = `null`, yield = `null`
    - Variety *Thelulla selection*: duration = `null`, yield = `null`
- **Timing Details:** 21 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `sun-cloud, sun, rain-thunder, rain`
- **Pests & Diseases Count:** 7 items cataloged

### Sesame (Gingelly) — `sesame/dry-intermediate.json`
- **Zones:** dry, intermediate | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Sesame/thala-Dry-Inter.png)
- **Regions Count:** 17 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 8 (cost_of_cultivation_acre_rs, expenditures_without_family_labour, expenditures_with_family_labour, selling_price_rs_per_kg, net_income...)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Sesame Cultivation (Maha & Yala)** (`main`): 4 varieties. Derived Yield: none
    - Variety *Uma*: duration = `null`, yield = `400-400 kg/ac`
    - Variety *Mali*: duration = `null`, yield = `400-400 kg/ac`
    - Variety *MI 1*: duration = `null`, yield = `400-400 kg/ac`
    - Variety *MI 3*: duration = `null`, yield = `400-400 kg/ac`
  - **Alternative Cropping Time Table (Inter cropping with Maize for Northern Province)** (`alternative`): 4 varieties. Derived Yield: none
    - Variety *Uma*: duration = `null`, yield = `400-400 kg/ac`
    - Variety *Mali*: duration = `null`, yield = `400-400 kg/ac`
    - Variety *MI 1*: duration = `null`, yield = `400-400 kg/ac`
    - Variety *MI 3*: duration = `null`, yield = `400-400 kg/ac`
- **Timing Details:** 14 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `sun, rain-thunder, rain`
- **Pests & Diseases Count:** 0 items cataloged

### Soya Bean (Soybean) — `soya-bean/dry.json`
- **Zones:** dry | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Soya Bean/soya_DRY.png)
- **Regions Count:** 12 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 9 (cost_of_cultivation_acre_rs, total_expenditure_including_family, total_expenditure_excluding_family, selling_price_rs_per_kg, income_printed...)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Soya Bean Cultivation (Maha & Yala)** (`main`): 3 varieties. Derived Yield: none
    - Variety *PB -1*: duration = `83d`, yield = `1120-1120 kg/ac`
    - Variety *PM -13*: duration = `93d`, yield = `1120-1120 kg/ac`
    - Variety *MISB1*: duration = `93d`, yield = `1120-1120 kg/ac`
- **Timing Details:** 6 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `sun, rain-thunder, sun-cloud, rain`
- **Pests & Diseases Count:** 14 items cataloged

### Soya Bean (Soybean) — `soya-bean/intermediate.json`
- **Zones:** intermediate | **Irrigation:** rainfed, irrigated | **Source Year:** 2013 (data-source/rgb/Soya Bean/soya_INTER.png)
- **Regions Count:** 4 administrative/agro-ecological regions
- **Raw Economic Keys Found:** 9 (cost_of_cultivation_acre_rs, total_expenditure_including_family, total_expenditure_excluding_family, selling_price_rs_per_kg, income_printed...)
- **Sanitized Surviving Keys:** **0** (Zero allowed)
- **Scenarios:**
  - **Main Seasons Soya Bean Cultivation (Maha & Yala)** (`main`): 3 varieties. Derived Yield: none
    - Variety *PB -1*: duration = `83d`, yield = `1120-1120 kg/ac`
    - Variety *PM -13*: duration = `93d`, yield = `1120-1120 kg/ac`
    - Variety *MISB1*: duration = `93d`, yield = `1120-1120 kg/ac`
- **Timing Details:** 6 parsed cleanly. 0 non-week agronomic advice strings safely flagged `parseFailed: true`.
- **Weather Icons:** `sun, rain-thunder, sun-cloud, rain`
- **Pests & Diseases Count:** 14 items cataloged

