# Datapizza Salaries

Sistema per la valutazione degli stipendi con visualizzazione personalizzata dei risultati.

## Componenti

### Frontend
- `viewer.html` - Pagina di caricamento che recupera i risultati da Zapier Storage
- `heyyou[1-5].html` - Pagine risultato per ogni score (1-5)
- `images/` - Immagini associate a ogni score

### Backend (Zapier)
- Workflow Zapier che analizza i dati del form
- Storage by Zapier per salvare i risultati
- Email automation per inviare il link personalizzato

## Setup rapido

1. **Configura Zapier workflow** (vedi `zapier-config-example.json`)
   - Crea workflow con trigger form
   - Aggiungi analisi stipendio (AI/custom logic)
   - Salva risultato in Storage by Zapier con chiave `dp_result_{{unique_id}}`
   - Invia email con link: `viewer.html?tracking={{unique_id}}`

2. **Configura viewer.html**
   ```javascript
   // Sostituisci questa riga con il tuo secret
   const ZAPIER_STORE_SECRET = 'il-tuo-secret-qui';
   ```

3. **Deploy su hosting statico**
   - Carica tutti i file HTML
   - Carica cartella `images/`
   - Assicurati che i file siano accessibili via HTTPS

4. **Testa**
   - Compila il form
   - Ricevi email con link
   - Clicca link e verifica che il risultato venga mostrato

## Documentazione completa

Vedi `SETUP.md` per istruzioni dettagliate.

## Struttura flusso

```
Form → Zapier → Storage → Email → Viewer → Risultato
```

1. Utente compila form
2. Zapier analizza e calcola score (1-5)
3. Salva in Storage by Zapier
4. Invia email con link univoco
5. Viewer carica e mostra pagina corrispondente

## Score mapping

- **1** = Molto sotto la media
- **2** = Sotto la media
- **3** = Nella media (default)
- **4** = Sopra la media
- **5** = Molto sopra la media

## Note tecniche

- **Polling:** Il viewer controlla Storage ogni 1.5s (max 20 tentativi)
- **Fallback:** Se non trova risultato dopo 30s, mostra messaggio di errore
- **Cache:** Usa `cache: 'no-cache'` per evitare dati obsoleti
- **Security:** Il secret Zapier è esposto lato client (considera proxy server per produzione)

## Requisiti

- Account Zapier (con accesso a Storage by Zapier)
- Hosting statico per i file HTML
- Form per raccolta dati (Typeform, Google Forms, custom, etc.)

## Supporto

Per domande o problemi, consulta la sezione Troubleshooting in `SETUP.md`.
