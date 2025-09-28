import React, { useEffect, useMemo, useState } from "react";

/**
 * Assolombarda – Lesson Showcase (React + Tailwind)
 * Minimal, elegant single-file component ready for GitHub Pages.
 * - Clean tabs (short labels) + Dark Mode toggle
 * - Poppins typography
 * - Each tab: intro, key advice/best practices, and the full prompt
 * - Buttons: Copy + Download .md + Download ALL (.zip)
 */

// ---- Content ---------------------------------------------------------------
const BEST_PRACTICES_MD = `# Best Practices per lo Scraping con Infinite Scroll e Paginazione

## 1. Principi generali
- Rispetta i ToS e robots.txt; non aggirare protezioni.
- Preferisci dati strutturati (JSON, API REST/GraphQL, CSV/XLSX) all'HTML.
- Salva i payload raw per audit e rielaborazioni.
- Schema dinamico: estrai tutto e normalizza solo a valle.

## 2. Infinite Scroll
- Cattura le richieste di rete mentre scorri: spesso sono XHR/JSON paginati.
- Se non esiste endpoint: esegui scroll incrementali, attendi i caricamenti (network idle) e confronta il conteggio elementi.
- Usa una "sentinella di fine": interrompi quando il conteggio non cresce per N cicli.

## 3. Paginazione classica
- Pattern comuni: ` + "`?page=N`" + `, ` + "`offset`" + `, link "Next", pulsanti "Load more".
- Itera finché non ottieni 0 risultati; cattura e unisci pagina per pagina.
- Fallback: verifica l'esistenza di sitemap XML.

## 4. Performance e stabilità
- Sharding dei task (es. blocchi da 100) e checkpoint frequenti.
- Rate‑limit adattivo (1–2 req/s), backoff esponenziale su 429/5xx.
- Concorrenza prudente (2–6 worker). Processi idempotenti.

## 5. Normalizzazione e dedup
- Deduplica su chiavi (es. nome+regione). Unisci i tag quando ci sono duplicati.
- Conserva sia il testo originale (es. "1–5 addetti") sia il campo numerico derivato.

## 6. Qualità e validazione
- Campionamento manuale (es. 30–50 righe) vs fonte.
- Controlli numerici: continuità rank, range plausibili, conteggi attesi.
- Genera report QA con copertura, nulli, errori e mismatch.

## 7. Audit e trasparenza
- Ogni record: source_url, extracted_at, record_id.
- Conserva raw/ e logs/ per ispezioni future.

## 8. Checklist rapida
- [ ] Endpoint strutturato?  
- [ ] Strategia: API/XHR >> scroll >> paginazione.  
- [ ] Rate‑limit & retry impostati.  
- [ ] Payload raw salvati.  
- [ ] Dedup e normalizzazione.  
- [ ] QA e export finale.
`;

const TABS = [
  {
    id: "rank",
    short: "Ranking",
    title: "Scraping di ranking non‑tabellari",
    blurb:
      "Estrai dataset completi da fonti come IMD Smart City Index e INRIX Scorecard senza fissare colonne e con QA ≥ 99%.",
    advice: [
      "Preferisci payload ufficiali (ZIP/XLSX/JSON) al DOM.",
      "Intercetta XHR/JSON: spesso liste e grafici sono alimentati da endpoint paginati.",
      "Schema dinamico: cattura tutti i campi, normalizza solo a fine pipeline.",
      "Qualità: continuità dei rank, campione casuale di 20 righe, salvataggio dei raw per audit.",
      "Rate‑limit 1–2 req/s + retry/backoff; processi idempotenti e rilanciabili.",
    ],
    filename: "01_ranking.md",
    prompt: `# Agent: Scraping di ranking non-tabellari (IMD & INRIX)

**Obiettivo**  
1) Raccogli tutte le informazioni tabellari/semi‑strutturate da:  
   • https://www.imd.org/smart-city-observatory/home/rankings/  
   • https://inrix.com/scorecard/  
2) Esporta un Excel con 1 foglio per sorgente **senza fissare colonne** (schema dinamico).  
3) Garantisci **accuratezza ≥99%** con controlli e log.

**Principi**  
- Preferisci file/endpoint ufficiali (ZIP/XLSX/CSV/JSON).  
- Se la pagina usa XHR/JSON, usa i payload originali.  
- Idempotenza: aggiungi colonne servizio (source_name, source_url, extracted_at, record_id).

**IMD – Playbook**  
1. Cerca e scarica media pack/risorse strutturate.  
2. Estrai tabelle → unione outer → qualità (conteggio città atteso, continuità rank, 20 righe a campione).  
3. Esporta foglio IMD.

**INRIX – Playbook**  
1. Apri pagina, accetta cookie, vai a “City Ranking List”.  
2. Cattura XHR/JSON; se assente, scroll + parse DOM; come fallback, report PDF.  
3. Merge dinamico → qualità (copertura ≈ paesi/città attesi, range plausibile metriche) → export foglio INRIX.

**Done**  
Excel con 2 fogli; raw salvati; QA report e log.`,
  },
  {
    id: "brief",
    short: "Rassegna",
    title: "Rassegna stampa automatizzata (quotidiana)",
    blurb:
      "Briefing alle 09:00 nel chatbot, in italiano, con citazione della fonte per ogni notizia e sezione 'Fonti consultate'.",
    advice: [
      "Copri fonti must‑have + affini; ordina per rilevanza per l'industria italiana.",
      "Formato: bullet concise (1–2 righe) + link; opzionale Top 3 del giorno.",
      "Trasparenza: chiudi con elenco completo delle fonti consultate.",
    ],
    filename: "02_rassegna.md",
    prompt:
      `Search for the latest economic, industrial, and business news and official data releases from Italian and international authoritative sources (e.g., Istat, Ocse/OECD, IMF, European Commission, Banca d'Italia, Il Sole 24 Ore, Ambrosetti, Financial Times, The Economist, La Voce, and other relevant sources). Write the briefing in Italian. Cite every individual story with its source and link. Add a final section "Fonti consultate" listing all sources you checked (even those not used). Prioritize items relevant to Italian industry and policy, and include global developments with impact on Italy. Present concise bullets with 1–2 lines of context/insight for each item.`,
  },
  {
    id: "batch",
    short: "Aziende",
    title: "Batch aziende camerali (~2000)",
    blurb:
      "Senza API: Controller + Worker, shard, stato persistente, resume; estrazione 'numero addetti' con tracciabilità.",
    advice: [
      "Shard di 100 (parametrico) e checkpoint ogni 20 record.",
      "Worker 3–6 con rate‑limit adattivo (1–2 req/s) e backoff su 429/5xx.",
      "Matching: normalizza ragione sociale + fuzzy score; salva confidence_score e source_url.",
      "Errori: transient/permanent/gated → needs_manual; mai aggirare CAPTCHA.",
    ],
    filename: "03_aziende_camerali.md",
    prompt: `# Agent: Batch "numero dipendenti" da elenco aziende (senza API)

**Input**  
Excel/CSV a **una colonna** (nomi). Normalizza forme giuridiche, genera varianti di query.

**Architettura**  
- Controller: sharding, coda, scheduler, resume da state.jsonl.  
- Worker: ricerca → match → scheda → estrazione (addetti, anno, metadati) → salvataggio.

**Regole**  
- Rate‑limit 1–2 req/s; backoff; concorrenza 3–6.  
- Idempotenza + checkpoint frequenti; chiave record su P.IVA o hash(nome, comune).  
- Per record: source_url, extracted_at, confidence_score; salva raw/minisnapshot.

**Output**  
results.parquet, artifacts/output.xlsx, needs_manual.csv, run_metrics.json, logs/, raw/.

**Done**  
≥95% copertura, 0 duplicati, audit pronto.`,
  },
  {
    id: "startup",
    short: "Startup",
    title: "Startup → tag → regione (scroll/paginazione)",
    blurb:
      "Procedura generale con discovery endpoint, gestione infinite scroll/paginazione, dedup e QA.",
    advice: [
      "Discovery: intercetta XHR/GraphQL; se possibile usa sitemap o URL paginati.",
      "Infinite scroll: loop di scroll + attesa rete; stop quando il conteggio non cresce per N cicli.",
      "Paginazione: Next o ?page=N fino a 0 risultati; salva tutti i payload raw.",
      "Dedup per (name_normalized, region) e union dei tag; QA con 30 righe a campione.",
    ],
    filename: "04_startup_scroll_paginazione.md",
    prompt: `# Agent: Dataset "startup → tag → regione" (UI paginata o infinite scroll)

**Obiettivo**  
Costruisci dataset con almeno: name, tags[], region, source_url. **Schema dinamico**.

**Workflow**  
1) Discovery rete (XHR/REST/GraphQL) + sitemap/URL paginati.  
2) Estrazione:  
   • API: itera pagine finché vuote.  
   • Scroll: loop con network idle + sentinella.  
   • Paginazione: Next/?page=N finché 0 risultati.  
3) Parsing dinamico + normalizzazione tags/region; conserva raw.  
4) Dedup e QA (campione 30).  
5) Export output.xlsx + qa_report.json.

**Done**  
Output.xlsx pulito e tracciabile.`,
  },
  {
    id: "best",
    short: "Best",
    title: "Best Practices (riassunto)",
    blurb:
      "Linee guida trasversali per scroll, paginazione, qualità, dedup, audit e rispetto dei ToS.",
    advice: [
      "Endpoint prima del DOM: JSON/API batte HTML.",
      "Sharding + checkpoint per resilienza e resume.",
      "Rate‑limit adattivo, backoff e concorrenza prudente.",
      "Ogni record deve avere source_url, extracted_at, record_id.",
    ],
    filename: "00_best_practices.md",
    prompt: BEST_PRACTICES_MD,
  },
];

// ---- Helpers: ZIP (store only) --------------------------------------------
// Minimal ZIP creator (no compression). Creates a Blob with multiple files.
function crc32Buf(buf) {
  let c = ~0;
  for (let i = 0; i < buf.length; i++) {
    c ^= buf[i];
    for (let k = 0; k < 8; k++) c = (c >>> 1) ^ (0xEDB88320 & -(c & 1));
  }
  return ~c >>> 0;
}
function strToUint8(s) {
  return new TextEncoder().encode(s);
}
function fileTimeDate(d = new Date()) {
  // DOS time/date
  const time = (d.getHours() << 11) | (d.getMinutes() << 5) | (Math.floor(d.getSeconds() / 2));
  const date = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
  return { time, date };
}
function makeZip(files) {
  // files: [{name, data: Uint8Array}]
  const localParts = [];
  const centralParts = [];
  let offset = 0;
  const { time, date } = fileTimeDate();
  files.forEach(({ name, data }) => {
    const crc = crc32Buf(data);
    const size = data.length;
    const nameBytes = strToUint8(name);
    // Local file header
    const local = new Uint8Array(30 + nameBytes.length + size);
    const dv = new DataView(local.buffer);
    dv.setUint32(0, 0x04034b50, true); // signature
    dv.setUint16(4, 20, true); // version
    dv.setUint16(6, 0, true); // flags
    dv.setUint16(8, 0, true); // method = store
    dv.setUint16(10, time, true);
    dv.setUint16(12, date, true);
    dv.setUint32(14, crc, true);
    dv.setUint32(18, size, true);
    dv.setUint32(22, size, true);
    dv.setUint16(26, nameBytes.length, true);
    dv.setUint16(28, 0, true); // extra len
    local.set(nameBytes, 30);
    local.set(data, 30 + nameBytes.length);
    localParts.push(local);

    // Central directory header
    const central = new Uint8Array(46 + nameBytes.length);
    const cv = new DataView(central.buffer);
    cv.setUint32(0, 0x02014b50, true);
    cv.setUint16(4, 20, true); // version made by
    cv.setUint16(6, 20, true); // version needed
    cv.setUint16(8, 0, true); // flags
    cv.setUint16(10, 0, true); // method
    cv.setUint16(12, time, true);
    cv.setUint16(14, date, true);
    cv.setUint32(16, crc, true);
    cv.setUint32(20, size, true);
    cv.setUint32(24, size, true);
    cv.setUint16(28, nameBytes.length, true);
    cv.setUint16(30, 0, true); // extra len
    cv.setUint16(32, 0, true); // comment len
    cv.setUint16(34, 0, true); // disk start
    cv.setUint16(36, 0, true); // int attrs
    cv.setUint32(38, 0, true); // ext attrs
    cv.setUint32(42, offset, true); // local header offset
    central.set(nameBytes, 46);
    centralParts.push(central);

    offset += local.length;
  });

  const centralSize = centralParts.reduce((n, p) => n + p.length, 0);
  const centralOffset = offset;
  const end = new Uint8Array(22);
  const ev = new DataView(end.buffer);
  ev.setUint32(0, 0x06054b50, true); // end of central dir
  ev.setUint16(4, 0, true); // disk
  ev.setUint16(6, 0, true); // start disk
  ev.setUint16(8, files.length, true);
  ev.setUint16(10, files.length, true);
  ev.setUint32(12, centralSize, true);
  ev.setUint32(16, centralOffset, true);
  ev.setUint16(20, 0, true); // comment len

  const blob = new Blob([...localParts, ...centralParts, end], { type: "application/zip" });
  return blob;
}

// ---- UI -------------------------------------------------------------------
function CopyablePrompt({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {}
  };
  const download = () => {
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "prompt.md";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <button onClick={copy} className="px-3 py-2 rounded-xl bg-neutral-900 text-white hover:bg-black text-sm">
          {copied ? "Copiato ✓" : "Copia prompt"}
        </button>
        <button onClick={download} className="px-3 py-2 rounded-xl border border-neutral-300 hover:bg-neutral-50 text-sm">
          Scarica .md
        </button>
      </div>
      <textarea
        readOnly
        value={text}
        className="w-full h-80 p-4 rounded-xl border border-neutral-300 font-mono text-sm bg-white"
      />
    </div>
  );
}

export default function ShowcaseApp() {
  const [active, setActive] = useState(TABS[0].id);
  const current = useMemo(() => TABS.find(t => t.id === active)!, [active]);
  const [dark, setDark] = useState(false);

  // Inject Poppins for typography (works on GitHub Pages)
  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap";
    document.head.appendChild(link);
    return () => { document.head.removeChild(link); };
  }, []);

  const bg = dark ? "bg-neutral-950 text-neutral-100" : "bg-white text-neutral-900";
  const sub = dark ? "text-neutral-400" : "text-neutral-600";
  const border = dark ? "border-neutral-800" : "border-neutral-200";
  const cardBg = dark ? "bg-neutral-900" : "bg-neutral-50";

  const downloadAll = () => {
    const files = TABS.map(t => ({ name: t.filename || `${t.id}.md`, data: strToUint8(t.prompt) }));
    const blob = makeZip(files);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "prompts_bundle.zip";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`min-h-screen ${bg}`} style={{ fontFamily: 'Poppins, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial' }}>
      <div className="max-w-5xl mx-auto px-6 py-10">
        <header className="mb-8 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">Assolombarda · Lesson Showcase</h1>
            <p className={`${sub} mt-2`}>Quattro esercizi + Best Practices. Copia o scarica i prompt.</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setDark(v => !v)}
              className={`px-3 py-2 rounded-xl text-sm border ${border} ${dark ? 'bg-neutral-900' : 'bg-white'} hover:opacity-90`}
              aria-label="Toggle dark mode"
            >
              {dark ? 'Light' : 'Dark'} mode
            </button>
            <button
              onClick={downloadAll}
              className={`px-3 py-2 rounded-xl text-sm border ${border} ${dark ? 'bg-neutral-900' : 'bg-white'} hover:opacity-90`}
            >
              Scarica tutti (.zip)
            </button>
          </div>
        </header>

        {/* Tabs (short, minimal) */}
        <nav className={`flex flex-wrap gap-2 border-b ${border} mb  -6`}>
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActive(tab.id)}
              className={`px-3 py-2 text-sm rounded-t-lg transition focus:outline-none ${
                active === tab.id
                  ? `border-b-2 ${dark ? 'border-neutral-100 text-neutral-100' : 'border-neutral-900 text-neutral-900'} font-semibold`
                  : `${dark ? 'text-neutral-400 hover:text-neutral-200' : 'text-neutral-500 hover:text-neutral-800'}`
              }`}
            >
              {tab.short}
            </button>
          ))}
        </nav>

        <section className="space-y-5">
          <div>
            <h2 className="text-xl font-semibold">{current.title}</h2>
            <p className={`text-sm mt-1 ${sub}`}>{current.blurb}</p>
          </div>

          {/* Advice box */}
          <div className={`rounded-2xl border ${border} ${cardBg} p-4`}>
            <div className="text-sm font-semibold mb-2">Consigli rapidi</div>
            <ul className={`list-disc pl-5 text-sm space-y-1 ${dark ? 'text-neutral-300' : 'text-neutral-700'}`}>
              {current.advice.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>

          {/* Prompt */}
          <CopyablePrompt text={current.prompt} />
        </section>

        <footer className={`text-xs mt-10 ${sub}`}>
          Pubblica con Vite/React su GitHub Pages. Poppins è caricato via Google Fonts. Il bundle .zip è creato lato client (senza dipendenze).
        </footer>
      </div>
    </div>
  );
}
