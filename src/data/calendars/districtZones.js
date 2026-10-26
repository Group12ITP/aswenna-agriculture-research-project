/**
 * District to Agro-Ecological Zone Mapping for Sri Lanka's 25 Administrative Districts
 * 
 * IMPORTANT: Many districts span more than one agro-ecological zone (e.g. Badulla spans Intermediate and Dry,
 * Kurunegala spans Intermediate and Dry, Nuwara Eliya spans Wet and Intermediate).
 * 
 * NOTE FOR VERIFICATION:
 * User must verify this mapping against the Department of Agriculture (DOA) Natural Resources
 * Management Centre (NRMC) Agro-Ecological Zone Map (2003/2010). Where a crop's specific calendar sheet
 * lists exact district/agro-ecological region tables (such as the Red Onion, Green Gram, Cowpea, or Potato sheets),
 * that crop-specific data takes precedence.
 * 
 * STRICT RULE:
 * getCalendar must NEVER fall back across zones. If a crop has no calendar file for the farmer's zone,
 * it returns 'no_calendar_for_zone'.
 */

export const DISTRICT_TO_ZONES = {
  'Ampara': ['dry'],
  'Anuradhapura': ['dry'],
  'Badulla': ['intermediate', 'dry'],
  'Batticaloa': ['dry'],
  'Colombo': ['wet'],
  'Galle': ['wet'],
  'Gampaha': ['wet', 'intermediate'],
  'Hambantota': ['dry', 'intermediate'],
  'Jaffna': ['dry'],
  'Kalutara': ['wet'],
  'Kandy': ['intermediate', 'wet'],
  'Kegalle': ['wet', 'intermediate'],
  'Kilinochchi': ['dry'],
  'Kurunegala': ['intermediate', 'dry'],
  'Mannar': ['dry'],
  'Matale': ['intermediate', 'dry'],
  'Matara': ['wet', 'intermediate'],
  'Monaragala': ['intermediate', 'dry'],
  'Mullaitivu': ['dry'],
  'Nuwara Eliya': ['wet', 'intermediate'],
  'Polonnaruwa': ['dry'],
  'Puttalam': ['dry', 'intermediate'],
  'Ratnapura': ['wet', 'intermediate'],
  'Trincomalee': ['dry'],
  'Vavuniya': ['dry']
};

/**
 * Returns the matched zone for a given district and available crop zones.
 * Never falls back across unmapped zones.
 * 
 * @param {string} district - Administrative district name
 * @param {string[]} availableCropZones - Array of zones available for the crop (e.g. ['dry', 'intermediate'])
 * @returns {string|'no_calendar_for_zone'} - Matched zone or 'no_calendar_for_zone'
 */
export function getCalendarZone(district, availableCropZones = []) {
  const districtZones = DISTRICT_TO_ZONES[district];
  if (!districtZones || districtZones.length === 0) {
    return 'no_calendar_for_zone';
  }
  
  // Find first direct intersection between district's zones and crop's available zones
  const match = districtZones.find(z => availableCropZones.includes(z));
  if (match) {
    return match;
  }
  
  // STRICT POLICY: Never fall back across zones
  return 'no_calendar_for_zone';
}
