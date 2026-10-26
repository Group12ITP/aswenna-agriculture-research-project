import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const irrPath = path.join(rootDir, 'src/data/calendars/paddy/dry-intermediate-irrigated.json');
const rfPath = path.join(rootDir, 'src/data/calendars/paddy/dry-intermediate-rainfed.json');
const wetPath = path.join(rootDir, 'src/data/calendars/paddy/wet.json');

const weatherDry = [
  { month: 9, month_name: 'September', h1: 'sun-cloud', h2: 'thunder' },
  { month: 10, month_name: 'October', h1: 'rain', h2: 'rain' },
  { month: 11, month_name: 'November', h1: 'rain', h2: 'rain' },
  { month: 12, month_name: 'December', h1: 'rain', h2: 'rain' },
  { month: 1, month_name: 'January', h1: 'moderate-rain', h2: 'sun' },
  { month: 2, month_name: 'February', h1: 'sun', h2: 'sun' },
  { month: 3, month_name: 'March', h1: 'sun', h2: 'sun' },
  { month: 4, month_name: 'April', h1: 'thunder', h2: 'thunder' },
  { month: 5, month_name: 'May', h1: 'thunder', h2: 'sun-cloud' },
  { month: 6, month_name: 'June', h1: 'sun', h2: 'sun' },
  { month: 7, month_name: 'July', h1: 'sun', h2: 'sun' },
  { month: 8, month_name: 'August', h1: 'sun', h2: 'sun' }
];

const weatherWet = [
  { month: 9, month_name: 'September', h1: 'sun-cloud', h2: null },
  { month: 10, month_name: 'October', h1: 'rain', h2: 'rain' },
  { month: 11, month_name: 'November', h1: 'rain', h2: 'rain' },
  { month: 12, month_name: 'December', h1: 'moderate-rain', h2: 'moderate-rain' },
  { month: 1, month_name: 'January', h1: 'sun', h2: 'sun' },
  { month: 2, month_name: 'February', h1: 'sun', h2: 'sun' },
  { month: 3, month_name: 'March', h1: 'sun', h2: 'moderate-rain' },
  { month: 4, month_name: 'April', h1: 'thunder', h2: 'thunder' },
  { month: 5, month_name: 'May', h1: 'rain', h2: 'rain' },
  { month: 6, month_name: 'June', h1: 'rain', h2: 'rain' },
  { month: 7, month_name: 'July', h1: 'rain', h2: 'rain' },
  { month: 8, month_name: 'August', h1: 'sun-cloud', h2: 'sun' }
];

function pestItem(verbatim) {
  const norm = verbatim.toLowerCase().replace(/[,\.]/g, '').trim();
  let canonical = norm;
  if (norm === 'thrips' || norm === 'thips') canonical = 'thrips';
  else if (norm === 'gall midge') canonical = 'gall_midge';
  else if (norm === 'leaf rolling caterpiller') canonical = 'leaf_rolling_caterpillar';
  else if (norm === 'stem borer') canonical = 'stem_borer';
  else if (norm === 'white back hopper') canonical = 'white_backed_planthopper';
  else if (norm === 'brown plant hopper' || norm === 'brown plant hoper') canonical = 'brown_planthopper';
  else if (norm === 'sheath & leaf mites') canonical = 'sheath_and_leaf_mites';
  else if (norm === 'blast') canonical = 'rice_blast';
  else if (norm === 'bacterial sheath blight' || norm === 'bacteria sheath blights') canonical = 'bacterial_sheath_blight';
  else if (norm === 'brown spot') canonical = 'brown_spot';
  else if (norm === 'paddy bug' || norm === 'pady bug') canonical = 'paddy_bug';

  return {
    canonical_name: canonical,
    verbatim_text: verbatim
  };
}

function buildPests(list) {
  return list.map(m => ({
    month: m.month,
    month_name: m.month_name,
    items: m.raw.map(pestItem)
  }));
}

const pestsIrrRaw = [
  { month: 10, month_name: 'October', raw: ['Thrips'] },
  { month: 11, month_name: 'November', raw: ['Thrips', 'Gall midge'] },
  { month: 12, month_name: 'December', raw: ['Thrips', 'Gall midge', 'Leaf rolling caterpiller', 'Stem borer', 'White back hopper', 'Sheath & leaf mites', 'Blast', 'Bacterial sheath blight'] },
  { month: 1, month_name: 'January', raw: ['Leaf rolling caterpiller', 'Brown plant hopper', 'Paddy bug', 'White back hopper', 'Sheath & leaf mites', 'Blast', 'Bacterial sheath blight', 'Brown spot'] },
  { month: 2, month_name: 'February', raw: ['Brown plant hopper', 'Paddy bug'] },
  { month: 4, month_name: 'April', raw: ['Thrips'] },
  { month: 5, month_name: 'May', raw: ['Thrips', 'Gall midge'] },
  { month: 6, month_name: 'June', raw: ['Thrips', 'Paddy bug', 'Gall midge', 'Leaf rolling caterpiller', 'Stem borer', 'Brown plant hopper', 'Sheath & leaf mites', 'Bacterial sheath blight'] },
  { month: 7, month_name: 'July', raw: ['Leaf rolling caterpiller', 'Gall midge', 'Brown plant hopper', 'Sheath & leaf mites', 'Brown spot'] },
  { month: 8, month_name: 'August', raw: ['Brown plant hopper', 'Paddy bug'] }
];

const pestsRfRaw = [
  { month: 10, month_name: 'October', raw: ['Thrips'] },
  { month: 11, month_name: 'November', raw: ['Thrips', 'Gall midge'] },
  { month: 12, month_name: 'December', raw: ['Thrips', 'Gall midge', 'Leaf rolling caterpiller', 'Stem borer', 'Brown plant hopper', 'Sheath & leaf mites', 'Blast', 'Bacterial sheath blight'] },
  { month: 1, month_name: 'January', raw: ['Leaf rolling caterpiller', 'Paddy bug', 'Brown plant hoper', 'Sheath & leaf mites', 'Blast,', 'Brown spot', 'Bacteria sheath blights'] },
  { month: 2, month_name: 'February', raw: ['Brown plant hopper', 'Paddy bug'] },
  { month: 4, month_name: 'April', raw: ['Thrips'] },
  { month: 5, month_name: 'May', raw: ['Thrips', 'Gall midge'] },
  { month: 6, month_name: 'June', raw: ['Thrips', 'Gall midge', 'Leaf rolling caterpiller', 'Stem borer', 'Brown plant hopper', 'Sheath & leaf mites', 'Bacterial sheath blight'] },
  { month: 7, month_name: 'July', raw: ['Brown plant hopper', 'Paddy bug', 'Leaf rolling caterpiller', 'Sheath & leaf mites', 'Brown spot', 'Bacterial sheath blight'] },
  { month: 8, month_name: 'August', raw: ['Pady bug', 'Brown plant hopper'] }
];

// Strictly bounded wet pests without neighboring column leak
const pestsWetRaw = [
  { month: 9, month_name: 'September', raw: ['Thrips'] },
  { month: 10, month_name: 'October', raw: ['Thrips', 'Gall midge'] },
  { month: 11, month_name: 'November', raw: ['Thrips', 'Gall midge', 'Leaf rolling caterpiller', 'Stem borer', 'White back hopper'] },
  { month: 12, month_name: 'December', raw: ['Leaf rolling caterpiller', 'Stem borer', 'Brown plant hopper', 'White back hopper', 'Sheath & leaf mites', 'Blast', 'Bacterial sheath blight'] },
  { month: 1, month_name: 'January', raw: ['Brown plant hopper', 'Paddy bug', 'Sheath & leaf mites', 'Brown spot', 'Bacterial sheath blights', 'Blast'] },
  { month: 2, month_name: 'February', raw: ['Brown plant hopper', 'Paddy bug'] },
  { month: 4, month_name: 'April', raw: ['Thrips'] },
  { month: 5, month_name: 'May', raw: ['Thips', 'Gall midge'] }, // Verbatim: 'Thips'
  { month: 6, month_name: 'June', raw: ['Thrips', 'Gall midge', 'Leaf rolling caterpiller', 'Stem borer', 'Brown plant hopper', 'Sheath & leaf mites', 'White back hopper', 'Bacterial sheath blight'] },
  { month: 7, month_name: 'July', raw: ['Brown plant hopper', 'Gall midge', 'Sheath & leaf mites', 'Brown spot', 'Bacterial sheath blight'] },
  { month: 8, month_name: 'August', raw: ['Brown plant hopper', 'Paddy bug', 'Bacterial sheath blight'] }
];

const ageGroups3 = [
  {
    age_group: '2 1/2 Month',
    header_text: '2 1/2 Month (days 80 ± 5) variety',
    duration_days: 80,
    tolerance_days: 5
  },
  {
    age_group: '3 Month',
    header_text: '3 Month (days 90 ± 5) variety',
    duration_days: 90,
    tolerance_days: 5
  },
  {
    age_group: '3 1/2 Month',
    header_text: '3 1/2 Month (days 105 ± 5) variety',
    duration_days: 105,
    tolerance_days: 5
  }
];

const ageGroups4 = [
  ...ageGroups3,
  {
    age_group: '4 - 4 1/2 Month',
    header_text: '4- 4 1/2 Month (days 120 -135 ± 5) variety',
    duration_days: { min: 120, max: 135 },
    tolerance_days: 5
  }
];

function updateFile(filePath, weather, pestsRaw, ageGroups, isRainfed = false, isWet = false) {
  const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

  data.weather_by_month = weather;
  delete data.weather_by_week;

  data.pests_diseases = buildPests(pestsRaw);

  for (const sc of data.scenarios) {
    sc.age_groups = ageGroups;

    // Season windows: mark planting positions with hint: true, verified: false
    if (Array.isArray(sc.season_windows)) {
      sc.season_windows.forEach(sw => {
        sw.hint = true;
        sw.verified = false;
      });
    }

    // Varieties
    for (const v of sc.varieties) {
      v.tolerance_days = 5;
      if (isRainfed && v.id === 'bg304') {
        v.yield_range_kg_ac = [1200, 1400]; // Revert to printed value
        v.notes = null; // Override removed from calendar JSON
      }
      if (isWet && (v.age_group === '4- 4 1/2 Month' || v.age_group === '4 - 4 1/2 Month')) {
        v.duration_days = { min: 120, max: 135 };
        delete v.duration_days_min;
        delete v.duration_days_max;
      } else {
        if (typeof v.duration_days === 'object') {
          // keep or handle
        }
      }
    }

    // Operations:
    // 1. Planting positions marked as hint: true, verified: false
    // 2. Harvest positions: store month only (Maha Feb, Yala Aug), remove W1/W2/W3 staggering
    // 3. All other operations: original_grid_position = null
    for (const op of sc.operations) {
      const k = op.key.toLowerCase();
      if (k.includes('plant') || k.includes('sow') || k.includes('broadcasting')) {
        op.hint = true;
        op.verified = false;
        // keep original_grid_position
      } else if (k.includes('harvest')) {
        op.hint = false;
        op.verified = true;
        op.original_grid_position = {
          maha_month: 2,
          yala_month: 8
        };
        op.details = 'Harvest icon month only read from tile (Maha Feb, Yala Aug)';
      } else {
        op.original_grid_position = null;
        delete op.hint;
        delete op.verified;
      }
      delete op.start_day_offset;
      delete op.end_day_offset;
    }

    // Fertilizer timing: use only printed days or weeks after broadcasting and planting
    for (const fert of sc.fertilizer_schedule) {
      delete fert.days_after_planting;
    }

    // Derived block
    if (sc.derived) {
      delete sc.derived.operations_day_offsets;
      delete sc.derived.day_offsets_computation_status;
    }
  }

  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
  console.log(`Updated ${filePath}`);

  // Mirror to frontend
  const rel = path.relative(path.join(rootDir, 'src'), filePath);
  const feDest = path.join(rootDir, 'profit_engine', 'frontend', 'src', rel);
  fs.mkdirSync(path.dirname(feDest), { recursive: true });
  fs.writeFileSync(feDest, JSON.stringify(data, null, 2), 'utf8');
  console.log(`Mirrored to ${feDest}`);
}

updateFile(irrPath, weatherDry, pestsIrrRaw, ageGroups3, false, false);
updateFile(rfPath, weatherDry, pestsRfRaw, ageGroups3, true, false);
updateFile(wetPath, weatherWet, pestsWetRaw, ageGroups4, false, true);
console.log('All files successfully updated and mirrored.');
