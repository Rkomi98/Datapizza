```javascript
// Step: generate_cards (viewer)
// Props: dataStore (type: data_store) - collega in UI
export default defineComponent({
  props: { dataStore: { type: "data_store" } },
  async run({ steps, $ }) {
    // 1) prendi rid dalla query: /?rid=...
    const rid = steps.trigger?.event?.query?.rid ?? $.params?.rid ?? null;
    if (!rid) {
      $.respond({ status: 400, headers: { "Content-Type":"text/html; charset=utf-8" }, body: "<h1>Missing rid</h1>" });
      return;
    }

    // 2) leggi il record
    let record;
    try { record = await this.dataStore.get(rid); }
    catch (err) {
      console.error("DataStore.get error", err);
      $.respond({ status: 500, headers: { "Content-Type":"text/html; charset=utf-8" }, body: "<h1>Server error</h1>" });
      return;
    }
    if (!record) {
      $.respond({ status: 404, headers: { "Content-Type":"text/html; charset=utf-8" }, body: `<h1>Not found rid=${rid}</h1>` });
      return;
    }

    // 3) prepara dati e HTML
    const score = Number(record.score ?? 2);
    const rationale = String(record.rationale ?? "");
    const { ruolo="—", localita="—", stipendio=0 } = record.inputs || {};

    const labels = {1:"Sopra la media", 2:"In media", 3:"Sotto la media", 4:"Sotto la media (Milano)"};
    const card = n => `<div class="card ${n===score ? 'hit' : ''}">${labels[n]||''}</div>`;

    const html = `<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Valutazione</title>
<style>
  body{font-family:system-ui,Arial;padding:24px;line-height:1.3}
  h1{font-size:20px;margin:0 0 6px}
  .meta{color:#444;margin:0 0 18px}
  .grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
  .card{border:2px solid #ddd;border-radius:12px;padding:28px;text-align:center;font-weight:700;background:#fff}
  .hit{border-color:#000;box-shadow:0 6px 18px rgba(0,0,0,.06)}
  @media(max-width:600px){.grid{grid-template-columns:1fr}}
</style></head><body>
  <h1>${esc(ruolo)} · ${esc(localita)} · €${Number(stipendio).toLocaleString("it-IT")}</h1>
  <div class="meta">Risultato: <strong>${labels[score] ?? score}</strong></div>
  <div class="grid">${[1,2,3,4].map(card).join('')}</div>
  <p class="meta">${esc(rationale)}</p>
</body></html>`;

    // 4) rispondi al browser (qui è un HTTP trigger, quindi è compatibile)
    $.respond({ status: 200, headers: { "Content-Type":"text/html; charset=utf-8" }, body: html });
    return { ok: true, rid };
  }
});

function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,"&#039;"); }
```