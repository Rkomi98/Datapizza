#!/bin/bash

echo "🚀 Avvio Zipkin per il tracciamento..."

# Ferma e rimuovi container esistente se presente
docker stop zipkin > /dev/null 2>&1
docker rm zipkin > /dev/null 2>&1

# Avvia Zipkin
docker run -d -p 9411:9411 --name zipkin openzipkin/zipkin

if [ $? -eq 0 ]; then
    echo "✅ Zipkin avviato su http://localhost:9411"
    echo "💡 Ora puoi rieseguire il tuo chatbot per abilitare il tracciamento Zipkin"
else
    echo "❌ Errore nell'avvio di Zipkin"
fi
