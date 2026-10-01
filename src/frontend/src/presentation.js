export const factLabels = {
  location: 'Location',
  incident_time: 'Incident time',
  device_type: 'Device type',
  theft_confirmed: 'Theft confirmed',
  banking_apps_present: 'Banking apps present',
  device_locked: 'Device locked',
  sim_blocked: 'SIM blocked',
};

export function displayValue(value) {
  if (value === null || value === undefined) return 'Unknown';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return String(value);
}

export function displayLabel(value) {
  if (value === null || value === undefined) return 'Unknown';
  const label = String(value).replaceAll('_', ' ');
  return label.charAt(0).toUpperCase() + label.slice(1);
}
