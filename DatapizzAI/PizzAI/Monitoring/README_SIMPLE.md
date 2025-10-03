# Monitoring semplice per chatbot

Configurazione ultra-semplice per monitorare un chatbot Datapizza-AI con Grafana, Prometheus e Zipkin.

## Avvio rapido (3 minuti)

### 1. Avvia i servizi di monitoring

```bash
cd Monitoring/
./start_monitoring.sh
```

### 2. Configura la tua API key

```bash
export OPENAI_API_KEY='your-openai-key-here'
```

### 3. Avvia il chatbot con monitoring

```bash
# Modalità interattiva
python simple_chatbot_monitor.py

# Modalità demo automatica
python simple_chatbot_monitor.py --auto
```

## Accesso ai servizi

Una volta avviato tutto:

- **🤖 Metriche chatbot**: http://localhost:8000
- **📊 Prometheus**: http://localhost:9090
- **📈 Grafana**: http://localhost:3000 (admin/admin)
- **🔍 Zipkin**: http://localhost:9411

## Configurazione Grafana

1. Vai su http://localhost:3000 (admin/admin)
2. Aggiungi Data Source: Prometheus → `http://prometheus:9090`
3. Crea dashboard con queste query:

```promql
# Richieste totali
chatbot_requests_total

# Tempo di risposta medio
rate(chatbot_response_time_seconds_sum[5m]) / rate(chatbot_response_time_seconds_count[5m])

# Token al minuto
rate(chatbot_tokens_total[5m]) * 60

# Tasso di errore
rate(chatbot_errors_total[5m]) / rate(chatbot_requests_total[5m])
```

## Metriche disponibili

- `chatbot_requests_total{status="success|error"}` - Richieste totali
- `chatbot_response_time_seconds` - Tempo di risposta (histogram)
- `chatbot_tokens_total` - Token utilizzati
- `chatbot_errors_total{error_type="..."}` - Errori per tipo

## Arresto

```bash
./stop_monitoring.sh
```

I dati rimangono salvati in `grafana-data/` e `prometheus-data/`.

## File inclusi

- `simple_chatbot_monitor.py` - Monitor principale
- `prometheus.yml` - Configurazione Prometheus
- `start_monitoring.sh` - Avvia tutto
- `stop_monitoring.sh` - Ferma tutto

## Troubleshooting

### Docker non disponibile
```bash
# Installa Docker prima
sudo dnf install docker  # Fedora
sudo systemctl start docker
```

### Porte occupate
I servizi usano le porte: 3000, 8000, 9090, 9411. Assicurati siano libere.

### API key mancante
```bash
export OPENAI_API_KEY='sk-...'
```

### Importazioni corrette
Se hai errori di importazione, usa:
```python
```

### Test rapido
```bash
cd Monitoring/
python test_monitor.py  # Test senza API key
```
