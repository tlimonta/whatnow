// Local demonstration fixture. These values are not extracted from user input.
// The case and task keys mirror current shared model concepts.
export const mockCase = {
  id: 'case_123',
  case_type: 'stolen_phone',
  status: 'active',
  risk_level: 'high',
  initial_message: 'My phone was stolen in Spain.',
  facts: {
    location: 'Spain',
    incident_time: null,
    device_type: 'smartphone',
    theft_confirmed: true,
    banking_apps_present: null,
    device_locked: null,
    sim_blocked: null,
  },
  missing_fields: [
    'incident_time',
    'banking_apps_present',
    'device_locked',
    'sim_blocked',
  ],
  tasks: [
    { id: 'demo-review', title: 'Review this example case', status: 'pending' },
    { id: 'demo-unknowns', title: 'Note which details are unknown', status: 'pending' },
    { id: 'demo-sources', title: 'Check for verified guidance in a later phase', status: 'pending' },
  ],
};

// Frontend-only presentation data; these fields are not part of the shared Task model.
export const mockTaskPresentation = {
  'demo-review': {
    priority: 'High',
    explanation: 'This example shows how a case summary could help organize the situation. It is demonstration content, not an assessed case.',
  },
  'demo-unknowns': {
    priority: 'Medium',
    explanation: 'Unknown details stay unknown in this prototype. The list shows what a future workflow might need to clarify.',
  },
  'demo-sources': {
    priority: 'Medium',
    explanation: 'A real action plan needs checked procedural data. No Spain procedure or official link is supplied in this demo.',
  },
};

export const factLabels = {
  location: 'Location',
  incident_time: 'Incident time',
  device_type: 'Device type',
  theft_confirmed: 'Theft confirmed',
  banking_apps_present: 'Banking apps present',
  device_locked: 'Device locked',
  sim_blocked: 'SIM blocked',
};
