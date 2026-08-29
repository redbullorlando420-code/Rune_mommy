import { loadCatalog } from '/shared/catalog.js';

export async function loadClientCatalog() {
  return loadCatalog(async (name) => {
    const r = await fetch('/data/' + name);
    if (!r.ok) throw new Error('missing ' + name);
    return r.json();
  });
}
