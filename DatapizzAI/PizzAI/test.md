# Guida Ambiente Virtuale "test" - Datapizza AI

Questa guida spiega come creare e utilizzare l'ambiente virtuale "test" per il progetto Datapizza AI.

## Prerequisiti

- Python 3.10 o superiore
- [uv](https://github.com/astral-sh/uv) installato

## Creazione Ambiente Virtuale

Naviga nella cartella del progetto principale:

```bash
cd /home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/datapizza-ai-main
```

Crea l'ambiente virtuale chiamato "test":

```bash
uv venv test
```

Questo comando creerà una cartella `test/` contenente l'ambiente virtuale isolato.

## Installazione Dipendenze

Attiva l'ambiente virtuale e sincronizza tutte le dipendenze del workspace:

```bash
source test/bin/activate
uv sync
```

Il comando `uv sync` installerà automaticamente:
- Tutti i pacchetti del workspace Datapizza AI
- Le dipendenze di sviluppo (pytest, ruff, deptry)
- Le dipendenze esterne necessarie

## Attivazione Ambiente

Per attivare l'ambiente virtuale in una nuova sessione terminale:

```bash
cd /home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/datapizza-ai-main
source test/bin/activate
```

Dopo l'attivazione, il prompt dovrebbe mostrare `(test)` all'inizio della riga.

## Verifica Installazione

Per verificare che tutto sia installato correttamente:

```bash
python -c "import datapizza; print('Datapizza AI installato correttamente')"
```

Oppure esegui i test:

```bash
pytest
```

## Utilizzo con uv run

Alternativamente, puoi eseguire script Python direttamente senza attivare l'ambiente:

```bash
uv run --python test/bin/python tuo_script.py
```

## Struttura del Workspace

Questo progetto utilizza un workspace UV con i seguenti moduli principali:
- `datapizza-ai-core`: Nucleo del framework
- `datapizza-ai-clients-*`: Client per diversi provider AI
- `datapizza-ai-embedders-*`: Sistemi di embedding
- `datapizza-ai-vectorstores-*`: Database vettoriali
- `datapizza-ai-modules-*`: Moduli aggiuntivi (parser, reranker, etc.)

## Comandi Utili

### Aggiornare dipendenze
```bash
source test/bin/activate
uv sync --upgrade
```

### Aggiungere nuove dipendenze
```bash
source test/bin/activate
uv add nome_pacchetto
```

### Rimuovere ambiente virtuale
```bash
rm -rf test/
```

## Troubleshooting

### Ambiente non attivato
Se ricevi errori di importazione, assicurati che l'ambiente sia attivato:
```bash
source test/bin/activate
```

### Dipendenze mancanti
Se mancano alcune dipendenze, riesegui la sincronizzazione:
```bash
source test/bin/activate
uv sync
```

### Versione Python incompatibile
Assicurati di avere Python 3.10+:
```bash
python --version
```
