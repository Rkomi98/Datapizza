# Esercizi DataPizza (GSK)

Applicazione React/Vite che mette a disposizione tutti i materiali degli esercizi GSK, con icone e call to action per effettuare il download dei singoli file o dell’intero pacchetto di ciascun esercizio.

## Requisiti

- Node.js 20+
- npm 10+

## Avvio locale

```bash
npm install
npm run dev
```

Il server di sviluppo è disponibile su `http://localhost:5173/`. I file Word/Excel sono serviti dalla cartella `public/Esercizi`.

## Build di produzione

```bash
npm run build
npm run preview
```

Il build produce gli asset statici nella cartella `dist/`.

## GitHub Pages

Il workflow `Deploy to GitHub Pages` (`.github/workflows/deploy.yml`) compila automaticamente il progetto e pubblica la cartella `dist` su GitHub Pages ad ogni push su `main`. Una volta effettuato il primo deploy, assicurati che nelle impostazioni della repository la sorgente di GitHub Pages punti all’ambiente creato dal workflow (`GitHub Actions`).

## Struttura cartelle principale

- `public/Esercizi` – materiali originali e archivi `.zip` per ogni esercizio.
- `src/EserciziDataPizza.jsx` – componente principale dell’interfaccia.
- `src/App.jsx` – monta il componente principale.
