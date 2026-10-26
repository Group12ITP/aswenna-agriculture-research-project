# Aswenna Platform — Asset Inventory & Requirements

This document tracks all multimedia assets used on the Aswenna Agricultural Decision-Support System home and landing page, their current state, and the exact specifications for incoming production video files.

---

## 1. Video Files Inventory (`public/videos/`)

| Filename | Target Section | Current Status | Poster Fallback | Recommended Specs |
| :--- | :--- | :--- | :--- | :--- |
| `hero.mp4` | Section 2: Hero Background | **Present** (30 MB) | `hero.jpg` (Active) | 1080p, 24fps, H.264/WebM, $\le$ 6 MB |
| `hero-mobile.mp4` | Section 2: Hero Mobile Viewport ($<768$px) | **Pending User Upload** | `hero-mobile.jpg` (Active) | 1080x1920 (9:16), $\le$ 4 MB |
| `highlands.mp4` | Section 4: Scroll Story (Plan Scene) | **Present** (31 MB) | `highlands.jpg` (Active) | 1080p, 24fps, H.264/WebM, $\le$ 4 MB |
| `harvest-hands.mp4` | Section 4: Scroll Story (Harvest Scene) | **Pending User Upload** | `harvest-hands.jpg` (Active) | 1080p, 24fps, H.264/WebM, $\le$ 4 MB |
| `transport.mp4` | Section 4: Scroll Story / Logistics | **Present** (15 MB) | `transport.jpg` (Active) | 1080p, 24fps, H.264/WebM, $\le$ 4 MB |
| `market.mp4` | Section 4: Scroll Story (Sell Scene) / Bento | **Pending User Upload** | `market.jpg` (Active) | 1080p, 24fps, H.264/WebM, $\le$ 4 MB |
| `ai-data.mp4` | Section 2 Modal & Section 7 Trust & Intelligence | **Pending User Upload** | `ai-data.jpg` (Active) | 1080p, 24fps, H.264/WebM, $\le$ 4 MB |
| `monsoon.mp4` | Section 6: How It Works Backdrop | **Pending User Upload** | `monsoon.jpg` (Active) | 1080p, 24fps, H.264/WebM, $\le$ 4 MB |
| `sunset.mp4` | Section 9: Final Emotional CTA | **Pending User Upload** | `sunset.jpg` (Active) | 1080p, 24fps, H.264/WebM, $\le$ 4 MB |

> **Note on Fallback Architecture**:  
> All video components are wrapped with `lazy` IntersectionObserver detection, an auto-fading high-resolution `.jpg` poster frame, and a CSS gradient backdrop. If any `.mp4` file is not found or fails to load, the page seamlessly presents the cinematic poster frame without UI breakage.

---

## 2. Configuration & Media Registry

All video sources, poster paths, and scene metadata are centrally managed in:
[`src/data/homeMedia.js`](file:///c:/Users/MSI/Desktop/Research/Profit%20Folder/profit_engine/frontend/src/data/homeMedia.js)

To replace or update a video file, simply drop the `.mp4` into `public/videos/` and ensure the filename matches, or update the path in `src/data/homeMedia.js`.

---

## 3. Brand Assets

| Asset | Path | Status |
| :--- | :--- | :--- |
| Aswenna White Logo (Transparent PNG) | `src/images/aswenna-logo-white.png` | **Present** |
| Aswenna Original Brand Crest | `src/images/ChatGPT Image Jun 26, 2026, 11_27_49 AM-Photoroom.png` | **Present** |

---

## 4. Farm Journey 3D & Illustrated Asset Requirements

Per the Farm Journey specification:
- **No primitives posing as objects**: Real GLBs with instanced models or illustrated 2D fallbacks.
- **Illustrated fallbacks**: Every 3D stage and pest card has an SVG/illustrated fallback for WebGL-disabled or low-end devices.

### 4.1 3D Journey Models Needed

| Asset / Prop | Search Term | Target Path | Fallback Strategy | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Walking Farmer** | "stylized farmer character walking animation GLB" | `public/models/journey/farmer_walker.glb` | Illustrated 2D walking farmer SVG badge | ⚠️ Cataloged |
| **Field Ridges / Soil** | "furrows plowed farm field texture soil GLB" | `public/models/journey/field_ridges.glb` | Procedural PBR soil shader + 2D illustrated cross-section | ⚠️ Cataloged |
| **Polythene Tunnel Frame** | "greenhouse hoop polythene rain shelter frame GLB" | `public/models/journey/polythene_tunnel.glb` | Procedural Three.js arched tube geometry with translucent film material | ⚠️ Cataloged |
| **Harvest Crates & Produce Baskets** | "wooden vegetable harvest crate low poly GLB" | `public/models/journey/harvest_crates.glb` | 2D illustrated wooden crate stack SVG with filled produce counter | ⚠️ Cataloged |
| **Sprinkler / Irrigation Hose** | "farm drip irrigation hose sprinkler head GLB" | `public/models/journey/irrigation_sprinkler.glb` | Animated SVG water arc with Three.js particle mist emitter | ⚠️ Cataloged |

### 4.2 Pest & Disease Illustrated Assets (66 Canonical Names)
Illustrated pest identification cards. Target path: `public/images/pests/<canonical_name>.webp` (format: 400x300 WebP with transparent/dark vignette background).

| # | Canonical Name | Target Filename | Search Term | Fallback Component |
|---|---|---|---|---|
| 1 | `purple_blotch` | `purple_blotch.webp` | "Alternaria porri purple blotch onion leaf disease illustration" | Illustrated SVG disease card with amber badge |
| 2 | `anthracnose` | `anthracnose.webp` | "Colletotrichum anthracnose twister disease onion chilli" | Illustrated SVG disease card with red badge |
| 3 | `thrips` | `thrips.webp` | "Thrips tabaci onion thrips vector insect illustration" | Illustrated SVG pest card with warning badge |
| 4 | `pod_borer` | `pod_borer.webp` | "Helicoverpa armigera legume pod borer caterpillar illustration" | Illustrated SVG pest card with warning badge |
| 5 | `chilli_leaf_curl_complex` | `chilli_leaf_curl_complex.webp` | "chilli leaf curl virus mite thrips upward curling leaf" | Illustrated SVG disease card with warning badge |
| 6 | `damping_off` | `damping_off.webp` | "Pythium damping off nursery seedling collar rot" | Illustrated SVG disease card with amber badge |
| 7 | `bacterial_wilt` | `bacterial_wilt.webp` | "Ralstonia solanacearum bacterial wilt solanaceous" | Illustrated SVG disease card with red badge |
| 8 | `late_blight` | `late_blight.webp` | "Phytophthora infestans late blight potato leaf lesions" | Illustrated SVG disease card with red badge |
| 9 | `brown_planthopper` | `brown_planthopper.webp` | "Nilaparvata lugens brown planthopper rice pest" | Illustrated SVG pest card with red badge |
| 10 | `paddy_blast` | `paddy_blast.webp` | "Magnaporthe oryzae rice blast spindle lesion" | Illustrated SVG disease card with red badge |
| ... | *Remaining 56 canonical pests* | `<canonical_name>.webp` | DOA Sri Lanka crop pest catalog lookup | `PestCard.jsx` visual fallback with category icon & DOA advice |

