import os
from PIL import Image

src_png = r'c:\Users\MSI\Desktop\Research\Profit Folder\data-source\rgb\Paddy\paddy-DRYINTER_Irrigated_English-scaled.png'
im = Image.open(src_png)
w, h = im.size
print(f'Paddy Irrigated dimensions: {w}x{h}')

scratch = r'C:\Users\MSI\.gemini\antigravity-ide\brain\b4679f88-f9de-4c34-9b76-4d9bc2de8b58\scratch\paddy_tiles'
os.makedirs(scratch, exist_ok=True)

# 1. Header & Legend: y: 0 to 250
im.crop((0, 0, w, 250)).save(os.path.join(scratch, '01_header_legend.png'))

# 2. Month, Week & Weather: y: 240 to 450
im.crop((0, 240, w, 450)).save(os.path.join(scratch, '02_month_week_weather.png'))

# 3. Operations - 2.5 month: y: 440 to 600
im.crop((0, 440, w, 600)).save(os.path.join(scratch, '03_ops_2_5_month.png'))

# 4. Operations - 3 month: y: 590 to 780
im.crop((0, 590, w, 780)).save(os.path.join(scratch, '04_ops_3_month.png'))

# 5. Operations - 3.5 month: y: 770 to 950
im.crop((0, 770, w, 950)).save(os.path.join(scratch, '05_ops_3_5_month.png'))

# 6. Pests & Diseases: y: 940 to 1180
im.crop((0, 940, w, 1180)).save(os.path.join(scratch, '06_pests_diseases.png'))

# 7. Bottom Left: Varieties & Seed Requirements: x: 0 to 500, y: 1180 to 1800
im.crop((0, 1180, 500, 1800)).save(os.path.join(scratch, '07_varieties_seed.png'))

# 8. Bottom Center-Left: Fertilizer table: x: 450 to 1000, y: 1180 to 1800
im.crop((450, 1180, 1000, 1800)).save(os.path.join(scratch, '08_fertilizer.png'))

# 9. Bottom Center: Organic advice & Salinity advice: x: 980 to 1500, y: 1180 to 1800
im.crop((980, 1180, 1500, 1800)).save(os.path.join(scratch, '09_organic_salinity.png'))

# 10. Bottom Right: Risk advice & Footer: x: 2200 to 2560, y: 1180 to 1800
im.crop((2200, 1180, 2560, 1800)).save(os.path.join(scratch, '10_risk_advice.png'))

# 11. Footer credits: y: 1800 to 1893
im.crop((0, 1800, w, 1893)).save(os.path.join(scratch, '11_footer_credits.png'))

print('All 11 tiles sliced successfully.')
