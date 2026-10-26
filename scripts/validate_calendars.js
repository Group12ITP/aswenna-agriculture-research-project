import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const schemaPath = path.join(rootDir, 'calendar.schema.json');
const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));

// Search paths for calendars
const calendarDirs = [
  path.join(rootDir, 'src', 'data', 'calendars'),
  path.join(rootDir, 'profit_engine', 'frontend', 'src', 'data', 'calendars')
];

function getJsonFiles(dir) {
  let results = [];
  if (!fs.existsSync(dir)) return results;
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const full = path.join(dir, file);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      results = results.concat(getJsonFiles(full));
    } else if (file.endsWith('.json') && !file.endsWith('.geo.json')) {
      results.push(full);
    }
  }
  return results;
}

const seenFiles = new Set();
let files = [];
for (const dir of calendarDirs) {
  for (const f of getJsonFiles(dir)) {
    const baseName = path.basename(f);
    const relFromCalendars = path.relative(dir, f);
    if (!seenFiles.has(relFromCalendars)) {
      seenFiles.add(relFromCalendars);
      files.push({ full: f, rel: relFromCalendars });
    }
  }
}

console.log(`\n==================================================`);
console.log(`  Aswenna Crop Calendar Validation Suite`);
console.log(`==================================================`);
console.log(`Found ${files.length} calendar JSON file(s) to validate.\n`);

let hasErrors = false;
let totalWarnings = 0;

function validateCalendar(data, fileRel) {
  const errors = [];
  const warnings = [];

  // Required top-level fields
  const requiredFields = ['crop', 'app_crop', 'zones', 'regions', 'irrigation', 'source_file', 'scenarios', 'risk_advice'];
  for (const field of requiredFields) {
    if (data[field] === undefined) {
      errors.push(`Missing required top-level property: "${field}"`);
    }
  }
  if (!data.weather_by_month && !data.weather_by_week) {
    errors.push('Missing required top-level property: "weather_by_month" or "weather_by_week"');
  }

  // Check zones
  if (Array.isArray(data.zones)) {
    const validZones = ['dry', 'intermediate', 'wet'];
    for (const z of data.zones) {
      if (!validZones.includes(z)) {
        errors.push(`Invalid zone "${z}". Must be one of: ${validZones.join(', ')}`);
      }
    }
  }

  // Check scenarios
  if (Array.isArray(data.scenarios)) {
    if (data.scenarios.length === 0) {
      errors.push(`"scenarios" array must contain at least 1 scenario block.`);
    }

    data.scenarios.forEach((sc, idx) => {
      const prefix = `Scenario[${idx}] (${sc.scenario || 'unknown'})`;
      if (!sc.scenario) errors.push(`${prefix}: missing "scenario"`);
      if (sc.cultivation_system === undefined) errors.push(`${prefix}: missing "cultivation_system"`);
      if (sc.harvest_type === undefined) errors.push(`${prefix}: missing "harvest_type"`);

      // Cross-check varieties
      if (Array.isArray(sc.varieties)) {
        sc.varieties.forEach((v) => {
          if (v.yield_range_kg_ac && Array.isArray(v.yield_range_kg_ac)) {
            if (v.yield_range_kg_ac[0] > v.yield_range_kg_ac[1]) {
              warnings.push(`${prefix} variety "${v.name}": Min yield (${v.yield_range_kg_ac[0]}) is greater than max yield (${v.yield_range_kg_ac[1]})!`);
            }
          }
          if (v.age_group && v.duration_days) {
            const days = typeof v.duration_days === 'object' ? v.duration_days.min : v.duration_days;
            if (v.age_group.toLowerCase().includes('3 month') && (days < 75 || days > 105)) {
              warnings.push(`${prefix} variety "${v.name}": Duration (${days} days) seems mismatched for age-group "${v.age_group}"`);
            }
          }
        });
      }

      // Variety checks: no unauthorized fields like pericarp_color
      if (Array.isArray(sc.varieties)) {
        sc.varieties.forEach((v) => {
          if (v.pericarp_color !== undefined) {
            errors.push(`${prefix} variety "${v.name}": contains unauthorized field "pericarp_color" (must not be added from external knowledge)`);
          }
        });

        if (sc.derived && sc.derived.total_varieties_count !== undefined) {
          if (sc.varieties.length !== sc.derived.total_varieties_count) {
            errors.push(`${prefix}: Variety count (${sc.varieties.length}) does not match expected tile count (${sc.derived.total_varieties_count})`);
          }
        }
      }

      // Cross-check operations (offsets may be in operation or derived block)
      if (Array.isArray(sc.operations)) {
        sc.operations.forEach((op) => {
          if (op.start_day_offset !== undefined && op.end_day_offset !== undefined) {
            if (op.start_day_offset > op.end_day_offset) {
              errors.push(`${prefix} operation "${op.label}": start_day_offset (${op.start_day_offset}) > end_day_offset (${op.end_day_offset})`);
            }
          }
        });
      }
      if (sc.derived && Array.isArray(sc.derived.operations_day_offsets)) {
        sc.derived.operations_day_offsets.forEach((op) => {
          if (op.start_day_offset !== undefined && op.end_day_offset !== undefined) {
            if (op.start_day_offset > op.end_day_offset) {
              errors.push(`${prefix} derived operation "${op.label}": start_day_offset (${op.start_day_offset}) > end_day_offset (${op.end_day_offset})`);
            }
          }
        });
      }

      // Cross-check fertilizer totals against printed_totals (ground truth)
      if (Array.isArray(sc.printed_totals) && Array.isArray(sc.fertilizer_schedule)) {
        sc.printed_totals.forEach((pt) => {
          const appRows = sc.fertilizer_schedule.filter(i => (i.age_group || 'all') === (pt.age_group || 'all'));
          const sumUrea = appRows.reduce((acc, i) => acc + (i.urea_kg_ac || 0), 0);
          const sumTsp = appRows.reduce((acc, i) => acc + (i.tsp_kg_ac || 0), 0);
          const sumMop = appRows.reduce((acc, i) => acc + (i.mop_kg_ac || 0), 0);

          if (pt.poster_discrepancy) {
            // Acknowledged poster discrepancy: application rows remain operational values
            if (pt.computed_sum) {
              if (pt.computed_sum.urea !== undefined && pt.computed_sum.urea !== sumUrea) {
                errors.push(`${prefix} [${pt.age_group}]: computed_sum.urea (${pt.computed_sum.urea}) differs from application sum (${sumUrea})`);
              }
              if (pt.computed_sum.tsp !== undefined && pt.computed_sum.tsp !== sumTsp) {
                errors.push(`${prefix} [${pt.age_group}]: computed_sum.tsp (${pt.computed_sum.tsp}) differs from application sum (${sumTsp})`);
              }
              if (pt.computed_sum.mop !== undefined && pt.computed_sum.mop !== sumMop) {
                errors.push(`${prefix} [${pt.age_group}]: computed_sum.mop (${pt.computed_sum.mop}) differs from application sum (${sumMop})`);
              }
            }
            if (pt.printed_total) {
              if (pt.printed_total.urea !== undefined && pt.printed_total.urea !== pt.urea_kg_ac) {
                errors.push(`${prefix} [${pt.age_group}]: printed_total.urea (${pt.printed_total.urea}) differs from printed total (${pt.urea_kg_ac})`);
              }
              if (pt.printed_total.tsp !== undefined && pt.printed_total.tsp !== pt.tsp_kg_ac) {
                errors.push(`${prefix} [${pt.age_group}]: printed_total.tsp (${pt.printed_total.tsp}) differs from printed total (${pt.tsp_kg_ac})`);
              }
              if (pt.printed_total.mop !== undefined && pt.printed_total.mop !== pt.mop_kg_ac) {
                errors.push(`${prefix} [${pt.age_group}]: printed_total.mop (${pt.printed_total.mop}) differs from printed total (${pt.mop_kg_ac})`);
              }
            }
            warnings.push(`${prefix} [${pt.age_group}]: Poster discrepancy acknowledged: printed total MOP is ${pt.mop_kg_ac} kg/ac, but application rows sum to ${sumMop} kg/ac. Application rows kept as operational values.`);
          } else {
            if (pt.urea_kg_ac !== null && sumUrea !== pt.urea_kg_ac) {
              errors.push(`${prefix} [${pt.age_group}]: Summed Urea applications (${sumUrea} kg/ac) differ from ground truth printed_total (${pt.urea_kg_ac} kg/ac)`);
            }
            if (pt.tsp_kg_ac !== null && sumTsp !== pt.tsp_kg_ac) {
              errors.push(`${prefix} [${pt.age_group}]: Summed TSP applications (${sumTsp} kg/ac) differ from ground truth printed_total (${pt.tsp_kg_ac} kg/ac)`);
            }
            if (pt.mop_kg_ac !== null && sumMop !== pt.mop_kg_ac) {
              errors.push(`${prefix} [${pt.age_group}]: Summed MOP applications (${sumMop} kg/ac) differ from ground truth printed_total (${pt.mop_kg_ac} kg/ac) [MISMATCH DETECTED]`);
            }
          }
        });
      }
    });
  }

  return { errors, warnings };
}

function validateIpmSupplement(data, fileRel) {
  const errors = [];
  const warnings = [];

  const requiredFields = ['crop', 'app_crop', 'type', 'source_file', 'ipm_core_principles', 'seasonal_phenology', 'target_pests', 'target_diseases', 'beneficial_organisms', 'weather_triggered_pest_risks'];
  for (const field of requiredFields) {
    if (data[field] === undefined) {
      errors.push(`Missing required IPM property: "${field}"`);
    }
  }

  if (data.type !== 'supplementary_pest_phenology') {
    errors.push(`IPM type must be "supplementary_pest_phenology", received "${data.type}"`);
  }

  // Validate target pests confidence
  if (Array.isArray(data.target_pests)) {
    data.target_pests.forEach((p, idx) => {
      if (!p.id || !p.name_en || !p.name_si) errors.push(`Pest[${idx}]: missing id, name_en, or name_si`);
      if (!p.confidence) errors.push(`Pest[${idx}] (${p.name_en || 'unknown'}): missing confidence flag`);
    });
  }

  // Validate target diseases confidence
  if (Array.isArray(data.target_diseases)) {
    data.target_diseases.forEach((d, idx) => {
      if (!d.id || !d.name_en || !d.name_si) errors.push(`Disease[${idx}]: missing id, name_en, or name_si`);
      if (!d.confidence) errors.push(`Disease[${idx}] (${d.name_en || 'unknown'}): missing confidence flag`);
    });
  }

  // Validate beneficials
  if (data.beneficial_organisms) {
    ['predators', 'parasitoids', 'entomopathogens'].forEach((cat) => {
      if (Array.isArray(data.beneficial_organisms[cat])) {
        data.beneficial_organisms[cat].forEach((b, idx) => {
          if (!b.id || !b.name_en) errors.push(`Beneficial ${cat}[${idx}]: missing id or name_en`);
          if (!b.confidence) errors.push(`Beneficial ${cat}[${idx}]: missing confidence flag`);
        });
      }
    });
  }

  return { errors, warnings };
}

for (const f of files) {
  try {
    const raw = fs.readFileSync(f.full, 'utf8');
    const data = JSON.parse(raw);
    const isIpm = f.rel.toLowerCase().endsWith('ipm.json') || data.type === 'supplementary_pest_phenology';
    const { errors, warnings } = isIpm ? validateIpmSupplement(data, f.rel) : validateCalendar(data, f.rel);

    if (errors.length > 0) {
      hasErrors = true;
      console.log(`❌ FAIL: ${f.rel}`);
      errors.forEach(e => console.log(`   - ERROR: ${e}`));
    } else {
      console.log(`✅ PASS: ${f.rel} ${isIpm ? '(IPM Supplement)' : ''}`);
    }

    if (warnings.length > 0) {
      totalWarnings += warnings.length;
      warnings.forEach(w => console.log(`   ⚠️ WARNING: ${w}`));
    }
  } catch (err) {
    hasErrors = true;
    console.log(`❌ ERROR reading/parsing ${f.rel}: ${err.message}`);
  }
}

console.log(`\n--------------------------------------------------`);
if (hasErrors) {
  console.log(`Validation FAILED with errors.`);
  process.exit(1);
} else {
  console.log(`All files PASSED validation! (${totalWarnings} warnings flagged)`);
  process.exit(0);
}
