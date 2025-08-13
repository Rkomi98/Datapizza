# PizzAI

Questo progetto è un template per iniziare a sviluppare con i pacchetti privati di Datapizza.

## Configurazione

Segui questi passaggi per configurare il tuo ambiente di sviluppo.

### 1. Prerequisiti

Assicurati di avere installato `uv`, un gestore di pacchetti Python veloce. Se non ce l'hai, puoi installarlo seguendo la [guida ufficiale](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Creazione dell'Ambiente Virtuale

Per isolare le dipendenze del progetto, crea un ambiente virtuale con una versione di Python 3.12 o superiore.

Dalla cartella principale del progetto (`PizzAI`), esegui:
```bash
uv venv --python 3.12
```

Questo comando creerà una cartella `.venv` contenente l'ambiente virtuale.

### 3. Autenticazione al Repository Privato

Per scaricare i pacchetti privati di Datapizza, devi autenticarti al nostro repository PyPI.

Crea un file `.netrc` nella tua home directory (`~/.netrc` su macOS/Linux o `C:\Users\<username>\_netrc` su Windows) con il seguente contenuto:

```
machine repository.datapizza.tech
login <il-tuo-username>
password <la-tua-password>
```

Sostituisci `<il-tuo-username>` e `<la-tua-password>` con le credenziali che trovi su Bitwarden cercando "pypy-registry".

**Nota:** Il file `.gitignore` del progetto è già configurato per ignorare questo file, quindi le tue credenziali non verranno accidentalmente caricate su Git.

### 4. Installazione delle Dipendenze

Una volta configurata l'autenticazione, attiva l'ambiente virtuale e installa i pacchetti necessari.

**Attiva l'ambiente:**
```bash
source .venv/bin/activate
```

**Installa i pacchetti (esempio):**
```bash
uv pip install datapizzai
```

Questo comando leggerà il file `pyproject.toml` per trovare l'indirizzo del repository privato e scaricherà il pacchetto.

## Utilizzo

Dopo l'installazione, puoi eseguire il tuo script Python principale:
```bash
python main.py
```
