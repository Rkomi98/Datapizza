#!/bin/bash

echo "⏹️  Arresto stack di monitoring..."

# Ferma e rimuove i container
echo "🔄 Arresto container..."
docker stop prometheus grafana zipkin 2>/dev/null || true
docker rm prometheus grafana zipkin 2>/dev/null || true

echo "✅ Stack di monitoring arrestato."
echo ""
echo "💾 I dati sono conservati in:"
echo "  - grafana-data/"
echo "  - prometheus-data/"
echo ""
echo "🚀 Per riavviare: ./start_monitoring.sh"
