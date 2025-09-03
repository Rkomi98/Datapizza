#!/bin/bash

# Script rapido per avviare Qdrant Server
echo "�� Avvio Qdrant Server..."

# Crea directory per persistenza dati se non esiste
mkdir -p qdrant_storage

echo "📁 Directory storage: $(pwd)/qdrant_storage"

# Avvia Qdrant con Docker
echo "🐳 Avvio container Docker..."
docker run -d \\
    --name qdrant-server \\
    -p 6333:6333 \\
    -p 6334:6334 \\
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \\
    --restart unless-stopped \\
    qdrant/qdrant:latest

echo ""
echo "✅ Qdrant avviato!"
echo "📊 Dashboard: http://localhost:6333/dashboard"
echo "🔗 REST API: http://localhost:6333"
echo ""
echo "🔍 Per verificare status:"
echo "   docker ps | grep qdrant"
echo "   curl http://localhost:6333/health"
echo ""
echo "⏹️ Per fermare:"
echo "   docker stop qdrant-server"
echo "   docker rm qdrant-server"

