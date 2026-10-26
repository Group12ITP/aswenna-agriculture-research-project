import os
from PIL import Image

src_png = r'c:\Users\MSI\Desktop\Research\Profit Folder\data-source\rgb\Paddy\paddy-WET_English_New-scaled.png'
im = Image.open(src_png)
w, h = im.size

scratch = r'C:\Users\MSI\.gemini\antigravity-ide\brain\b4679f88-f9de-4c34-9b76-4d9bc2de8b58\scratch\paddy_wet_tiles'
os.makedirs(scratch, exist_ok=True)

# 1. Header & Title: y: 0 to 250
im.crop((0, 0, w, 250)).save(os.path.join(scratch, '01_header.png'))

# 2. Operations timeline: y: 440 to 950
im.crop((0, 440, w, 950)).save(os.path.join(scratch, '02_ops.png'))

# 3. Varieties table: x: 0 to 500, y: 1180 to 1800
im.crop((0, 1180, 500, 1800)).save(os.path.join(scratch, '03_varieties.png'))

# 4. Fertilizer table: x: 450 to 1180, y: 1180 to 1800
im.crop((450, 1180, 1180, 1800)).save(os.path.join(scratch, '04_fertilizer.png'))

# 5. Organic & Toxicity advice: x: 1150 to 1800, y: 1180 to 1800
im.crop((1150, 1180, 1800, 1800)).save(os.path.join(scratch, '05_toxicity.png'))

# 6. Salinity & Risk advice: x: 1800 to 2560, y: 1180 to 1800
im.crop((1800, 1180, 2560, 1800)).save(os.path.join(scratch, '06_salinity_risk.png'))

print('Paddy Wet tiles sliced.')
