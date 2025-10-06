#!/usr/bin/env python3
"""
Script per generare la dashboard HTML con i dati embedded.
Questo evita problemi CORS quando si apre il file direttamente.
"""

import json
from pathlib import Path


def generate_dashboard():
    """Genera la dashboard con i dati embedded."""
    
    # Carica i dati degli eventi
    index_file = Path('events_index.json')
    
    if not index_file.exists():
        print("❌ File events_index.json non trovato!")
        print("Esegui prima: python analyze_all_events.py")
        return
    
    with open(index_file, 'r', encoding='utf-8') as f:
        events_data = json.load(f)
    
    # Template HTML
    html_template = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Datapizza Eventi - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #a855f7 0%, #8b5cf6 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 50%);
            animation: rotate 20s linear infinite;
        }
        
        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .header-content {
            position: relative;
            z-index: 2;
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .stats-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(168, 85, 247, 0.15);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #a855f7;
            display: block;
            margin-bottom: 8px;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #64748b;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .section-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-title::before {
            content: '';
            width: 4px;
            height: 28px;
            background: linear-gradient(135deg, #a855f7, #8b5cf6);
            border-radius: 2px;
        }
        
        .events-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 25px;
        }
        
        .event-card {
            background: linear-gradient(135deg, #fefbff 0%, #f8f4ff 100%);
            border: 2px solid #e9d5ff;
            border-radius: 12px;
            padding: 25px;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .event-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(168, 85, 247, 0.2);
            border-color: #a855f7;
        }
        
        .event-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #a855f7, #8b5cf6);
        }
        
        .event-name {
            font-size: 1.4rem;
            font-weight: 700;
            color: #7c3aed;
            margin-bottom: 15px;
        }
        
        .event-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 15px;
        }
        
        .event-stat {
            background: white;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #e9d5ff;
        }
        
        .event-stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #a855f7;
        }
        
        .event-stat-label {
            font-size: 0.75rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .event-link {
            display: inline-block;
            background: linear-gradient(135deg, #a855f7, #8b5cf6);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            margin-top: 10px;
        }
        
        .event-link:hover {
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(168, 85, 247, 0.3);
        }
        
        .no-events {
            text-align: center;
            padding: 60px 20px;
            color: #64748b;
        }
        
        .no-events-icon {
            font-size: 4rem;
            margin-bottom: 20px;
        }
        
        .footer {
            background: #f8fafc;
            padding: 25px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .content {
                padding: 20px;
            }
            
            .events-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <div style="display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 15px;">
                    <svg width="60" height="40" viewBox="0 0 800 400" style="filter: brightness(0) invert(1);">
                        <polygon points="50,50 200,50 250,150 150,250 50,200" fill="#E53E3E" stroke="none"/>
                        <text x="320" y="180" font-family="Arial, sans-serif" font-size="120" font-weight="400" fill="#333">Datapizza</text>
                        <circle cx="750" cy="100" r="20" fill="#333"/>
                    </svg>
                </div>
                <h1>Eventi Datapizza</h1>
                <p class="subtitle">Dashboard Analytics e Report</p>
            </div>
        </div>
        
        <div class="content">
            <div id="stats-overview" class="stats-overview"></div>
            
            <h2 class="section-title">Eventi</h2>
            <div id="events-container" class="events-grid"></div>
        </div>
        
        <div class="footer">
            <p>Datapizza Eventi Dashboard • Ultimo aggiornamento: <span id="last-update"></span></p>
        </div>
    </div>

    <script>
        // Dati embedded direttamente nell'HTML
        const eventsData = EVENTS_DATA_PLACEHOLDER;
        
        /**
         * Renderizza le statistiche generali
         */
        function renderOverviewStats(events) {
            const statsContainer = document.getElementById('stats-overview');
            
            if (events.length === 0) {
                statsContainer.style.display = 'none';
                return;
            }
            
            // Calcola statistiche aggregate
            let totalParticipants = 0;
            let totalFeedbacks = 0;
            let totalCompanies = new Set();
            let avgSatisfaction = 0;
            let satisfactionCount = 0;
            
            events.forEach(event => {
                const kpis = event.kpis || {};
                totalParticipants += kpis.profiling_responses || 0;
                totalFeedbacks += kpis.feedback_responses || 0;
                totalCompanies = new Set([...totalCompanies, ...(event.profiling_data?.companies?.list || [])]);
                
                if (kpis.overall_satisfaction) {
                    avgSatisfaction += kpis.overall_satisfaction;
                    satisfactionCount++;
                }
            });
            
            const stats = [
                { value: events.length, label: 'Eventi Totali' },
                { value: totalParticipants, label: 'Partecipanti' },
                { value: totalFeedbacks, label: 'Feedback Ricevuti' },
                { value: totalCompanies.size, label: 'Aziende Uniche' },
                { 
                    value: satisfactionCount > 0 ? (avgSatisfaction / satisfactionCount).toFixed(1) : 'N/A', 
                    label: 'Soddisfazione Media' 
                }
            ];
            
            statsContainer.innerHTML = stats.map(stat => `
                <div class="stat-card">
                    <span class="stat-value">${stat.value}</span>
                    <span class="stat-label">${stat.label}</span>
                </div>
            `).join('');
        }
        
        /**
         * Renderizza la lista degli eventi
         */
        function renderEvents(events) {
            const container = document.getElementById('events-container');
            
            if (events.length === 0) {
                container.innerHTML = `
                    <div class="no-events">
                        <div class="no-events-icon">📭</div>
                        <h3>Nessun evento trovato</h3>
                        <p>Esegui <code>python analyze_all_events.py</code> per analizzare gli eventi disponibili.</p>
                    </div>
                `;
                return;
            }
            
            // Ordina per data (più recenti prima)
            const sortedEvents = [...events].sort((a, b) => {
                return new Date(b.analysis_date) - new Date(a.analysis_date);
            });
            
            container.innerHTML = sortedEvents.map(event => {
                const kpis = event.kpis || {};
                const profiling = event.profiling_data || {};
                const feedback = event.feedback_data || {};
                
                return `
                    <div class="event-card" onclick="window.location.href='${event.event_folder}/index.html'">
                        <div class="event-name">${event.event_name}</div>
                        <div class="event-stats">
                            <div class="event-stat">
                                <div class="event-stat-value">${kpis.profiling_responses || 0}</div>
                                <div class="event-stat-label">Partecipanti</div>
                            </div>
                            <div class="event-stat">
                                <div class="event-stat-value">${kpis.feedback_responses || 0}</div>
                                <div class="event-stat-label">Feedback</div>
                            </div>
                            <div class="event-stat">
                                <div class="event-stat-value">${kpis.overall_satisfaction ? kpis.overall_satisfaction.toFixed(1) + '/5' : 'N/A'}</div>
                                <div class="event-stat-label">Soddisfazione</div>
                            </div>
                            <div class="event-stat">
                                <div class="event-stat-value">${profiling.companies?.total_unique || 0}</div>
                                <div class="event-stat-label">Aziende</div>
                            </div>
                        </div>
                        <a href="${event.event_folder}/index.html" class="event-link" onclick="event.stopPropagation()">
                            Vedi Report →
                        </a>
                    </div>
                `;
            }).join('');
        }
        
        /**
         * Inizializzazione
         */
        function init() {
            console.log('🚀 Caricamento dashboard...');
            
            const events = eventsData.events || [];
            
            if (events.length > 0) {
                renderOverviewStats(events);
                renderEvents(events);
                
                // Aggiorna data ultimo update
                const lastUpdate = new Date().toLocaleDateString('it-IT', {
                    day: '2-digit',
                    month: 'long',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                document.getElementById('last-update').textContent = lastUpdate;
            } else {
                document.getElementById('events-container').innerHTML = `
                    <div class="no-events">
                        <div class="no-events-icon">📭</div>
                        <h3>Nessun evento trovato</h3>
                        <p>Esegui <code>python analyze_all_events.py</code> per generare i dati.</p>
                    </div>
                `;
            }
        }
        
        // Avvia l'applicazione
        init();
    </script>
</body>
</html>
"""
    
    # Sostituisci il placeholder con i dati reali
    events_json = json.dumps(events_data, ensure_ascii=False, indent=2)
    html_content = html_template.replace('EVENTS_DATA_PLACEHOLDER', events_json)
    
    # Salva il file
    output_file = Path('index.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard generata: {output_file}")
    print(f"📊 {len(events_data['events'])} eventi inclusi")
    print(f"\n🌐 Apri {output_file} nel browser per visualizzare la dashboard")


if __name__ == '__main__':
    generate_dashboard()

