# Hackathon Voting Game

![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![Firebase](https://img.shields.io/badge/firebase-%23039BE5.svg?style=for-the-badge&logo=firebase)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)

Un'applicazione web per la gestione delle votazioni in tempo reale durante un hackathon. Consente a un "Host" di creare una stanza, definire le squadre partecipanti e gestire i round di votazione, mentre i "Giocatori" possono unirsi alla stanza, votare le squadre in base a criteri predefiniti e visualizzare i risultati live.

## 🚀 Funzionalità

- **Gestione Ruoli**: Distinzione tra Host (amministratore) e Giocatore (votante).
- **Creazione Stanza**: L'Host può creare una stanza protetta da password e aggiungere le squadre partecipanti.
- **Votazione in Tempo Reale**: I giocatori votano le squadre durante un timer. I risultati e le medie si aggiornano istantaneamente per tutti i partecipanti.
- **Criteri Ponderati**: I voti sono basati su diversi criteri (es. Creatività, Esecuzione) con pesi personalizzabili.
- **Leaderboard Dinamica**: Una classifica generale che mostra il punteggio medio di ogni squadra, aggiornata al termine di ogni round.
- **Interfaccia Semplice**: Un'interfaccia utente pulita e intuitiva per una facile navigazione.

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Backend & Database**: [Firebase Realtime Database](https://firebase.google.com/products/realtime-database) per la sincronizzazione dei dati in tempo reale.
- **Hosting**: Può essere deployato su qualsiasi servizio di hosting per siti statici (es. GitHub Pages, Netlify, Vercel).

## ⚙️ Configurazione e Installazione

Per eseguire il progetto in locale, segui questi passaggi:

### 1. Prerequisiti

- [Node.js](https://nodejs.org/) installato (versione 14 o successiva).
- Un progetto [Firebase](https://firebase.google.com/) attivo.

### 2. Clona il Repository

```bash
git clone https://github.com/tuo-username/tuo-repository.git
cd tuo-repository
```

### 3. Configura Firebase (locale)

Crea manualmente un file `firebase-config-local.js` nella root del progetto con il seguente contenuto e compila i campi con le credenziali del tuo progetto Firebase (console Firebase: Settings > General > Your apps > SDK snippet). Questo file viene caricato prima di `app.js` solo in locale e NON va committato.

```javascript
// firebase-config-local.js
window.firebaseConfigLocal = {
  apiKey: "<API_KEY>",
  authDomain: "<PROJECT_ID>.firebaseapp.com",
  // Realtime Database URL (esempi):
  //   https://<PROJECT_ID>-default-rtdb.firebaseio.com
  //   https://<PROJECT_ID>-default-rtdb.europe-west1.firebasedatabase.app
  databaseURL: "https://<PROJECT_ID>-default-rtdb.firebaseio.com",
  projectId: "<PROJECT_ID>",
  storageBucket: "<PROJECT_ID>.appspot.com",
  messagingSenderId: "<SENDER_ID>",
  appId: "<APP_ID>",
  measurementId: "<MEASUREMENT_ID>"
};
```

**Nota**: `firebase-config-local.js` non viene committato né usato in produzione.

### 4. Installa le Dipendenze

Esegui il seguente comando per installare le dipendenze necessarie (Firebase e il server di sviluppo):

```bash
npm install
```

### 5. Avvia l'Applicazione

Per avviare il server di sviluppo locale, esegui:

```bash
npm start
```

L'applicazione sarà disponibile all'indirizzo `http://127.0.0.1:8080` (o un'altra porta se la 8080 è occupata).

## 📖 Come si Usa

### Host

1.  Dalla pagina principale, scegli il ruolo **Host**.
2.  Inserisci la password (quella predefinita è `D4t4p1zz4`).
3.  Aggiungi i nomi di tutte le squadre partecipanti.
4.  Clicca su **Crea Stanza**. Verrà generato un codice univoco da condividere con i giocatori.
5.  Nella dashboard, seleziona una squadra da valutare e avvia il timer.
6.  Monitora i risultati live o la classifica generale tramite i tab.
7.  Al termine di una valutazione, passa alla manche successiva con il pulsante **Prossima manche**.

### Giocatore

1.  Dalla pagina principale, scegli il ruolo **Giocatore**.
2.  Inserisci il codice della stanza fornito dall'Host.
3.  Seleziona la squadra di cui fai parte (non potrai votare per la tua stessa squadra).
4.  Quando l'Host avvia il timer per una squadra, il modulo di votazione si attiverà.
5.  Assegna un punteggio da 1 a 5 stelle per ogni criterio e invia il tuo voto.
6.  Puoi vedere i risultati medi in tempo reale nella parte inferiore della schermata. 