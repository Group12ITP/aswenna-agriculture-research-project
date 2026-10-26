import os
from PIL import Image

src_png = r'c:\Users\MSI\Desktop\Research\Profit Folder\data-source\rgb\Paddy\IPMcalender.png'
im = Image.open(src_png)
w, h = im.size

scratch = r'C:\Users\MSI\.gemini\antigravity-ide\brain\b4679f88-f9de-4c34-9b76-4d9bc2de8b58\scratch\paddy_ipm_tiles'
os.makedirs(scratch, exist_ok=True)

# 1. Title and header: y: 0 to 250
im.crop((0, 0, w, 250)).save(os.path.join(scratch, '01_title_header.png'))

# 2. Months and weeks: y: 200 to 450
im.crop((0, 200, w, 450)).save(os.path.join(scratch, '02_month_week.png'))

# 3. Phenology stages and Pests: y: 400 to 750
im.crop((0, 400, w, 750)).save(os.path.join(scratch, '03_pest_phenology.png'))

# 4. Lower IPM control actions: y: 700 to 1275
im.crop((0, 700, w, 1275)).save(os.path.join(scratch, '04_ipm_controls.png'))

print('Paddy IPM tiles sliced.')
