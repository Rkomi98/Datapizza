# Ducati: Datapizza AI Tutorial

Questo progetto contiene un Jupyter Notebook introduttivo per l'utilizzo della libreria `datapizza-ai`, inclusi esempi di chiamate API, creazione di chatbot con gestione della memoria e integrazione di tool personalizzati.

## 1. Versione di Python e prerequisiti

Questo progetto richiede **Python 3.12 o superiore** (vedi `pyproject.toml`, `requires-python = ">=3.12"`).

Per avere un ambiente **riproducibile** usiamo:

- `uv` come package manager
- il file di lock `uv.lock` per fissare versioni e dipendenze

> Suggerito: usare direttamente `uv` anche per installare la versione di Python, così non devi gestirla a mano.

### 1.1. Verificare la versione di Python

Da terminale:

```bash
python --version
```

Se leggi qualcosa come `Python 3.12.x` o `Python 3.13.x` sei a posto.

Se la versione è più vecchia (es. 3.10 o 3.11), installa una versione compatibile seguendo una di queste strade.

### 1.2. Installare Python con `uv` (consigliato)

`uv` può scaricare e gestire versioni di Python isolate, senza toccare quella di sistema.

Per installare una versione compatibile:

```bash
uv python install 3.12
```

Per vedere le versioni disponibili:

```bash
uv python list
```

Quando userai `uv sync` o `uv run`, `uv` userà automaticamente una versione compatibile con `>=3.12` (se disponibile).

### 1.3. Installare `uv`

Il progetto utilizza `uv` per la gestione delle dipendenze e dell'ambiente virtuale. Diamo di seguito le istruzioni per ambienti Linux/macOS e Windows:

- **Linux/macOS**:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

- **Windows (PowerShell)**:
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

> Dopo l’installazione, chiudi e riapri il terminale se il comando `uv` non viene riconosciuto.

## 2. Installazione del progetto (ambiente riproducibile)

Una volta installati Python (3.12+) e `uv`, puoi creare l’ambiente virtuale e installare le dipendenze in modo riproducibile.

1.  **Clonare il repository** (se necessario):
    ```bash
    git clone <url-repository>
    cd Ducati
    ```

2.  **Sincronizzare l'ambiente**:

    Questo comando:
    - crea l'ambiente virtuale `.venv`
    - installa tutte le dipendenze rispettando le versioni definite in `uv.lock`
    - configura automaticamente il repository privato Datapizza

    ```bash
    uv sync
    ```

    Se vuoi essere sicuro al 100% che vengano usate solo le versioni del `uv.lock` (senza aggiornamenti), puoi usare:

    ```bash
    uv sync --frozen
    ```

## 3. Configurazione

Prima di eseguire il notebook, è necessario configurare le credenziali API.

1.  Creare un file `.env` nella root del progetto.
2.  Aggiungere la chiave API di OpenAI:
    ```env
    OPENAI_API_KEY=sk- la_tua_chiave_qui
    ```

## 4. Utilizzo

Per avviare il notebook e seguire il tutorial:

1.  **Attivare l'ambiente e avviare Jupyter**:
    
    Il comando qui sotto:
    - usa l'ambiente virtuale creato da `uv sync`
    - garantisce che la versione di Python usata sia quella corretta (>=3.12)

    ```bash
    uv run jupyter notebook
    ```
    
2.  Aprire il file `Notebook/Ducati.ipynb`.

3.  Assicurarsi che il kernel selezionato sia quello dell'ambiente virtuale creato (solitamente indicato come `Python 3 (ipykernel)` o simile, ma eseguendo tramite `uv run` dovrebbe essere automatico).

## 5. Contenuti del Notebook

Il notebook `Ducati.ipynb` copre i seguenti argomenti:

*   **Chiamata API**: Esempio base di invio prompt.
*   **Chatbot**: Implementazione di una classe con memoria persistente della conversazione.
*   **Tools**: Esempio di integrazione di funzioni Python (calcolatrice, meteo) richiamabili dal modello.


