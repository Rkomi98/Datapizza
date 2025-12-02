# Ducati: Datapizza AI Tutorial

Questo progetto contiene un Jupyter Notebook introduttivo per l'utilizzo della libreria `datapizza-ai`, inclusi esempi di chiamate API, creazione di chatbot con gestione della memoria e integrazione di tool personalizzati.

## 1. Prerequisiti

*   Python 3.12 o 3.13
*   `uv` (Package manager per Python)

## 2. Installazione

Il progetto utilizza `uv` per la gestione delle dipendenze e dell'ambiente virtuale per garantire la massima riproducibilità. Diamo di seguito le istruzioni per ambienti Linux/macOS e Windows:

1.  **Installare uv** (se non presente):
    *   **Linux/macOS**:
        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```
    *   **Windows (PowerShell)**:
        ```powershell
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        ```

2.  **Clonare il repository** (se necessario):
    ```bash
    git clone <url-repository>
    cd Ducati
    ```

3.  **Sincronizzare l'ambiente**:
    Questo comando creerà l'ambiente virtuale `.venv` e installerà tutte le dipendenze necessarie, configurando automaticamente il repository privato Datapizza.
    ```bash
    uv sync
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



