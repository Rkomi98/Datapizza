# Guida all'installazione della libreria Datapizza-AI

Questa guida fornisce le istruzioni complete per installare e configurare la libreria Datapizza-AI nel ambiente di test.

## Prerequisiti

Prima di iniziare, assicurati di avere i seguenti requisiti:

- **Python 3.10+** installato
- **uv** (gestore pacchetti Python veloce) - installalo con: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Accesso alla directory `datapizza-ai-main`

## Ambiente di test

La libreria è già configurata e installata nell'ambiente di test situato in:
```
PizzAI/datapizza-ai-main/test/
```

Questo ambiente virtuale Python contiene tutti i pacchetti necessari per utilizzare Datapizza-AI.

## Installazione della libreria

### Passo 1: Attivazione dell'ambiente di test

```bash
cd /home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/datapizza-ai-main
source test/bin/activate
```

Verifica che l'ambiente sia attivo:
```bash
which python
# Dovrebbe mostrare: /home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/datapizza-ai-main/test/bin/python

python --version
# Dovrebbe mostrare: Python 3.11.13
```

### Passo 2: Installazione/aggiornamento della libreria

La libreria è già installata, ma se vuoi reinstallarla o aggiornarla:

```bash
# Assicurati di essere nell'ambiente attivato
source test/bin/activate

# Installa la libreria in modalità editable (sviluppo)
uv pip install -e . --python test/bin/python
```

### Passo 3: Verifica dell'installazione

Testa che tutto funzioni correttamente:

```bash
# Verifica import base
python -c "import datapizza; print('✓ Datapizza importato con successo')"

# Verifica moduli principali
python -c "
import datapizza
from datapizza.agents import Agent
from datapizza.memory import Memory
from datapizza.tools import tool
from datapizza.clients import ClientFactory
from datapizza.type import TextBlock, ROLE
print('✓ Tutti i moduli principali importati correttamente')
"

# Verifica pacchetti installati
uv pip list | grep datapizza
```

### Passo 4: Pacchetti installati

L'installazione include i seguenti pacchetti Datapizza:

```
datapizza-ai: 0.0.1 (editable install)
datapizza-ai-core: 0.0.1
datapizza-ai-clients-openai: 0.0.1
datapizza-ai-embedders-openai: 0.0.1
datapizza-ai-vectorstores-qdrant: 0.0.1
```

E le seguenti dipendenze esterne:
- OpenAI SDK (1.109.1)
- Qdrant client (1.15.1)
- Pydantic (2.11.9)
- OpenTelemetry (1.37.0)
- E altre dipendenze necessarie

## Utilizzo della libreria

### Importazione dei moduli

```python
# Importazione diretta (raccomandata)
from datapizza.agents import Agent
from datapizza.memory import Memory
from datapizza.tools import tool
from datapizza.clients import ClientFactory

# Oppure importazione completa
import datapizza as dp
```

### Esempio di utilizzo base

```python
import os
from dotenv import load_dotenv
import datapizza as dp

load_dotenv()

# Crea un client OpenAI
client = dp.clients.OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="Sei un assistente utile."
)

# Crea un agente
agent = dp.agents.Agent(
    name="TestAgent",
    client=client,
    system_prompt="Sei un assistente AI utile."
)

# Usa l'agente
response = agent.run("Ciao! Come posso aiutarti?")
print(response)
```

### Esempio con memoria

```python
import datapizza as dp

# Crea memoria e client
memory = dp.memory.Memory()
client = dp.clients.OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

# Usa la memoria nelle conversazioni
memory.add_turn([dp.type.TextBlock(content="Ciao!")], dp.type.ROLE.USER)
response = client.invoke("Rispondi al messaggio", memory=memory)
```

## Struttura della libreria

La libreria Datapizza-AI è organizzata in moduli:

- **`agents`**: Agenti AI autonomi con strumenti
- **`memory`**: Gestione della memoria conversazionale
- **`tools`**: Decoratori e strumenti per gli agenti
- **`clients`**: Client per vari provider LLM
- **`type`**: Tipi di dati (TextBlock, ROLE, etc.)
- **`embedders`**: Generazione di embedding
- **`vectorstores`**: Archiviazione vettoriale (Qdrant)
- **`pipeline`**: Pipeline di processamento

## Troubleshooting

### Problemi comuni

1. **Ambiente non attivato**
   ```bash
   # Verifica ambiente attivo
   which python  # deve puntare a test/bin/python
   ```

2. **Dipendenze mancanti**
   ```bash
   # Reinstalla tutto
   uv pip install -e . --python test/bin/python
   ```

3. **Python sbagliato**
   ```bash
   # Usa sempre l'ambiente test
   source test/bin/activate
   python your_script.py
   ```

4. **Import errors**
   ```bash
   # Verifica versioni installate
   uv pip list | grep datapizza
   ```

### Logs e debugging

Per debug più dettagliato:
```bash
export PYTHONPATH="/home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/datapizza-ai-main:$PYTHONPATH"
python -c "import datapizza; print(datapizza.__file__)"
```

## Configurazione avanzata

### Chiavi API

Crea un file `.env` nella directory principale:
```bash
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-google-key-here
```

### Configurazione personalizzata

```python
from datapizza.clients import ClientFactory
from datapizza.clients.factory import Provider

# Crea client personalizzato
client = ClientFactory.create(
    provider=Provider.OPENAI,
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7,
    system_prompt="Sei un assistente specializzato."
)
```

## Supporto

Per supporto o problemi:
1. Controlla la documentazione nella cartella `docs/`
2. Consulta gli esempi nella cartella `PizzAI/`
3. Verifica l'installazione con gli script di test

---

**Nota**: Questo ambiente di test è configurato specificatamente per lo sviluppo e il testing della libreria Datapizza-AI. Per l'uso in produzione, considera l'installazione tramite pip dal repository privato Datapizza.

