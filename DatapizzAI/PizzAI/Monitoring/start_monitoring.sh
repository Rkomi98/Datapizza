#!/bin/bash

echo "🚀 Avvio stack di monitoring per chatbot..."

# Verifica Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker non trovato! Installa Docker prima di continuare."
    exit 1
fi

# Crea directory per i dati
echo "📁 Creazione directory..."
mkdir -p grafana-data prometheus-data

# Ferma container esistenti (se presenti)
echo "🔄 Pulizia container esistenti..."
docker stop prometheus grafana zipkin 2>/dev/null || true
docker rm prometheus grafana zipkin 2>/dev/null || true

# Avvia Zipkin
echo "🔧 Avvio Zipkin..."
docker run -d \
    --name zipkin \
    -p 9411:9411 \
    openzipkin/zipkin

# Avvia Prometheus
echo "🔧 Avvio Prometheus..."
docker run -d \
    --name prometheus \
    -p 9090:9090 \
    -v "$(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml" \
    -v "$(pwd)/prometheus-data:/prometheus" \
    prom/prometheus

# Avvia Grafana
echo "🔧 Avvio Grafana..."
docker run -d \
    --name grafana \
    -p 3000:3000 \
    -v "$(pwd)/grafana-data:/var/lib/grafana" \
    grafana/grafana

echo ""
echo "✅ Stack di monitoring avviato con successo!"
echo ""
echo "📊 Servizi disponibili:"
echo "  - Zipkin (traces):     http://localhost:9411"
echo "  - Prometheus (metrics): http://localhost:9090"  
echo "  - Grafana (dashboard):  http://localhost:3000 (admin/admin)"
echo ""
echo "🤖 Per avviare il chatbot con monitoring:"
echo "  export OPENAI_API_KEY='your-key-here'"
echo "  python simple_chatbot_monitor.py"
echo ""
echo "⏹️  Per fermare tutto: ./stop_monitoring.sh"
