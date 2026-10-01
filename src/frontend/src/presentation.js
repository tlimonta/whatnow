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

// Display metadata for the existing Spain workflow, copied from the source registry.
// API tasks still supply only reference IDs; unknown references are never guessed.
export const officialSources = {
  stolen_phone_es: {
    policia_nacional_denuncia: { name: 'Policía Nacional — Denuncias', url: 'https://www.policia.es/_es/denuncias/htdocs/politicaCookies.php' },
    policia_nacional_ovd: { name: 'Policía Nacional — Oficina Virtual de Denuncias', url: 'https://denuncias.policia.es/OVD/Principal.dgp' },
    movistar_bloqueo_linea_robo: { name: 'Movistar — Bloquear línea móvil por robo', url: 'https://www.movistar.es/atencion-cliente/bloqueo-linea-robo' },
    vodafone_robo_perdida_dispositivo: { name: 'Vodafone — Qué hacer si pierdes o te roban tu dispositivo', url: 'https://ayudacliente.vodafone.es/particulares/servicio-tecnico/robo-y-perdida/que-hacer-si-pierdes-o-te-roban-tu-dispositivo/' },
    orange_robo_perdida_movil: { name: 'Orange — Qué hacer si te roban el móvil o lo pierdes', url: 'https://ayuda.orange.es/particulares/movil/robo-perdida-rotura/me-han-robado-el-movil/1153-que-hacer-si-te-roban-el-movil-o-lo-pierdes' },
    yoigo_robo_perdida_movil: { name: 'Yoigo — Me han robado el móvil o lo he perdido', url: 'https://www.yoigo.com/ayuda/me-han-robado-el-movil-o-lo-he-perdido' },
    apple_robo_iphone_ipad: { name: 'Apple Support — Si te roban el iPhone o el iPad', url: 'https://support.apple.com/es-es/120837' },
    google_android_perdido: { name: 'Ayuda de Android — Cómo borrar, encontrar o proteger un dispositivo Android perdido', url: 'https://support.google.com/android/answer/6160491?hl=es' },
    bde_uso_fraudulento_tarjeta: { name: 'Banco de España — Uso fraudulento', url: 'https://clientebancario.bde.es/pcb/es/menu-horizontal/productosservici/serviciospago/tarjetas/guia-textual/uso-fraudulento/' },
  },
};
