<p align="center">
  <img src="https://raw.githubusercontent.com/Data-Pizza/Data-Pizza/main/datapizza-logo.png" alt="Datapizza Logo" width="200"/>
</p>

<h1 align="center">PizzAI Template</h1>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white"/>
  <img alt="uv" src="https://img.shields.io/badge/installer-uv-blueviolet"/>
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green"/>
</p>

Questo progetto è un template per iniziare a sviluppare con i pacchetti privati di Datapizza.

---

## Configurazione

Segui questi passaggi per configurare il tuo ambiente di sviluppo.

### 1. Prerequisiti

Assicurati di avere installato `uv`, un gestore di pacchetti Python veloce. Se non ce l'hai, puoi installarlo seguendo la [guida ufficiale](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Creazione dell'ambiente virtuale

Per isolare le dipendenze del progetto, crea un ambiente virtuale con una versione di Python 3.12 o superiore.

Dalla cartella principale del progetto (`PizzAI`), esegui:
```bash
uv venv --python 3.12
```

Questo comando creerà una cartella `.venv` contenente l'ambiente virtuale.

### 3. Configurazione del progetto

Prima di poter installare pacchetti dal repository privato di Datapizza, devi configurare il file `pyproject.toml` per indicare a `uv` dove trovarli.

Aggiungi le seguenti righe al tuo file `PizzAI/pyproject.toml`:
```toml
[[tool.uv.index]]
name = "datapizza-pypi"
url = "https://repository.datapizza.tech/repository/datapizza-pypi/simple"
```

### 4. Autenticazione al repository privato

Per scaricare i pacchetti privati di Datapizza, devi autenticarti al nostro repository PyPI.

Crea un file `.netrc` nella tua home directory (`~/.netrc` su macOS/Linux o `C:\Users\<username>\_netrc` su Windows) con il seguente contenuto:

```
machine repository.datapizza.tech
login <il-tuo-username>
password <la-tua-password>
```

Sostituisci `<il-tuo-username>` e `<la-tua-password>` con le credenziali che trovi su Bitwarden cercando "pypy-registry".

**Nota:** Il file `.gitignore` del progetto è già configurato per ignorare questo file, quindi le tue credenziali non verranno accidentalmente caricate su Git.

### 5. Installazione delle dipendenze

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
