/**
 * Crop Aliases: Maps Crop Calendar directory names to Aswenna App Crop Names
 * 
 * Note on Chilli:
 * The calendar source is titled "CHILI - Capsicum annum" and specifies both
 * "Harvesting for Green Chilli" and "Harvesting for Dry Chilli" on the same timeline.
 * Cultivars listed (MI 2, KA 2, MI Green, Arunalu 01, MICH-3) are the national standard
 * pungent cultivars for Sri Lanka. The Aswenna app tracks fresh green pods as "Green Chilli"
 * (Capsicum annuum), which directly maps to this calendar.
 */

export const CALENDAR_TO_APP_CROP = {
  'Big Onion': 'Big Onion',
  'Black Gram': 'Black Gram',
  'Chilli': 'Green Chilli',
  'Cowpea': 'Cowpea',
  'Finger Millet': 'Kurakkan',
  'Green Gram': 'Green Gram',
  'Ground Nut': 'Groundnut',
  'Maize': 'Maize',
  'Paddy': 'Paddy',
  'Potato': 'Potato',
  'Red Onion': 'Red Onion',
  'Sesame': 'Gingelly',
  'Soya Bean': 'Soybean'
};

export const APP_TO_CALENDAR_CROP = Object.entries(CALENDAR_TO_APP_CROP).reduce((acc, [k, v]) => {
  acc[v] = k;
  return acc;
}, {});
