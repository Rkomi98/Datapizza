#!/usr/bin/env python3
"""
Script per generare la pagina HTML dinamica di un evento.
La pagina carica i dati da analysis.json e li renderizza.
"""

import json
from pathlib import Path
from datetime import datetime


def generate_event_page(event_folder: str):
    """Genera la pagina HTML dinamica per un evento."""
    
    event_path = Path(event_folder)
    analysis_file = event_path / 'analysis.json'
    
    if not analysis_file.exists():
        print(f"❌ File {analysis_file} non trovato!")
        print("Esegui prima: python analyze_event.py " + event_folder)
        return False
    
    # Carica i dati dell'analisi
    with open(analysis_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Template HTML dinamico
    html_template = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EVENT_NAME - Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.4;
            color: #2c3e50;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #a855f7 0%, #8b5cf6 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
        }
        
        .header h1 {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .header .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .back-link {
            position: absolute;
            top: 20px;
            left: 20px;
            color: white;
            text-decoration: none;
            font-size: 1.5rem;
        }
        
        .content {
            padding: 40px 30px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px 20px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(168, 85, 247, 0.15);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #a855f7;
            display: block;
            margin-bottom: 8px;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #64748b;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .section {
            margin-bottom: 35px;
        }
        
        .section-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-title::before {
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(135deg, #a855f7, #8b5cf6);
            border-radius: 2px;
        }
        
        .info-card {
            background: linear-gradient(135deg, #fefbff 0%, #f8f4ff 100%);
            border: 1px solid #e9d5ff;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .info-item {
            margin-bottom: 15px;
        }
        
        .info-label {
            font-weight: 600;
            color: #7c3aed;
            margin-bottom: 5px;
        }
        
        .info-value {
            color: #4b5563;
            line-height: 1.6;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .tags-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        
        .tag {
            background: white;
            border: 1px solid #e9d5ff;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            color: #7c3aed;
        }
        
        .footer {
            background: #f8fafc;
            padding: 25px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
            font-size: 0.9rem;
        }
        
        @media (max-width: 640px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }
            .content {
                padding: 30px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="../index.html" class="back-link">←</a>
            <h1 id="event-title">Caricamento...</h1>
            <p class="subtitle">Report e Analytics</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2 class="section-title">KPI principali</h2>
                <div id="kpis-container" class="metrics-grid"></div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Profilazione partecipanti</h2>
                <div id="profiling-container"></div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Feedback e valutazioni</h2>
                <div id="feedback-container"></div>
            </div>
            
            <div class="section" id="gpt-section" style="display: none;">
                <h2 class="section-title">Analisi qualitativa GPT</h2>
                <div id="gpt-container"></div>
            </div>
            
            <div class="section" id="job-titles-section" style="display: none;">
                <h2 class="section-title">Job titles partecipanti</h2>
                <div id="job-titles-container"></div>
            </div>
            
            <div class="section" id="companies-section" style="display: none;">
                <h2 class="section-title">Aziende partecipanti</h2>
                <div id="companies-container"></div>
            </div>
        </div>
        
        <div class="footer">
            <p id="footer-text">Report generato automaticamente</p>
        </div>
    </div>

    <script>
        // Dati embedded
        const eventData = EVENT_DATA_PLACEHOLDER;
        
        function renderKPIs(kpis) {
            const container = document.getElementById('kpis-container');
            
            // Lista completa di metriche possibili
            const allMetrics = [
                { key: 'iscritti_iniziali', label: 'Iscritti', format: (v) => v || 'N/A' },
                { key: 'disiscritti', label: 'Disiscritti', format: (v) => v || 'N/A' },
                { key: 'iscritti_finali', label: 'Iscritti Finali', format: (v) => v || 'N/A' },
                { key: 'partecipanti', label: 'Partecipanti', format: (v) => v || 'N/A' },
                { key: 'tasso_presenza', label: 'Tasso Presenza', format: (v) => v != null ? v.toFixed(1) + '%' : 'N/A' },
                { key: 'tasso_no_show', label: 'Tasso No Show', format: (v) => v != null ? v.toFixed(1) + '%' : 'N/A' },
                { key: 'profiling_responses', label: 'Profilation Response', format: (v) => v || 0 },
                { key: 'feedback_responses', label: 'Feedback', format: (v) => v || 0 },
                { key: 'feedback_rate', label: 'Feedback Rate', format: (v) => v != null ? v.toFixed(1) + '%' : 'N/A' },
                { key: 'overall_satisfaction', label: 'Soddisfazione Media', format: (v) => v != null ? v.toFixed(1) + '/5' : 'N/A' },
                { key: 'satisfaction_5_stars_percentage', label: 'Soddisfazione 5★', format: (v) => v != null ? v.toFixed(1) + '%' : 'N/A' },
                { key: 'unique_companies', label: 'Aziende Uniche', format: (v) => v || 0 }
            ];
            
            // Mostra solo le metriche disponibili
            const metrics = allMetrics
                .filter(m => kpis[m.key] !== undefined && kpis[m.key] !== null)
                .map(m => ({
                    label: m.label,
                    value: m.format(kpis[m.key])
                }));
            
            if (metrics.length === 0) {
                container.innerHTML = '<p class="info-value">Nessun KPI disponibile</p>';
                return;
            }
            
            container.innerHTML = metrics.map(m => `
                <div class="metric-card">
                    <span class="metric-value">${m.value}</span>
                    <span class="metric-label">${m.label}</span>
                </div>
            `).join('');
        }
        
        function renderProfiling(data) {
            const container = document.getElementById('profiling-container');
            if (!data || !data.total_responses) {
                container.innerHTML = '<p class="info-value">Dati non disponibili</p>';
                return;
            }
            
            let html = '<div class="grid-2">';
            
            // Studenti vs Professionisti
            if (data.students_vs_professionals) {
                const svp = data.students_vs_professionals;
                html += `
                    <div class="info-card">
                        <div class="info-label">Studenti vs Professionisti</div>
                        <div class="info-value">
                            Professionisti: ${svp.professionals} (${svp.professionals_percentage}%)<br>
                            Studenti: ${svp.students} (${svp.students_percentage}%)
                        </div>
                    </div>
                `;
            }
            
            // Distribuzione età
            if (data.age_distribution) {
                html += `
                    <div class="info-card">
                        <div class="info-label">Distribuzione età</div>
                        <div class="info-value">
                            ${Object.entries(data.age_distribution).map(([range, count]) => 
                                `${range}: ${count} persone`
                            ).join('<br>')}
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            
            // Esperienza
            if (data.experience_levels && Object.keys(data.experience_levels).length > 0) {
                html += `
                    <div class="info-card">
                        <div class="info-label">Livelli di esperienza</div>
                        <div class="info-value">
                            ${Object.entries(data.experience_levels).map(([level, count]) => 
                                `${level} anni: ${count} persone`
                            ).join(' • ')}
                        </div>
                    </div>
                `;
            }
            
            // Categorie professionali
            if (data.job_categories) {
                html += `<div class="info-card"><div class="info-label">Categorie professionali</div><div class="info-value">`;
                for (const [category, info] of Object.entries(data.job_categories)) {
                    if (info.count > 0) {
                        html += `<strong>${category}:</strong> ${info.count} (${info.percentage}%)<br>`;
                    }
                }
                html += `</div></div>`;
            }
            
            // Motivazioni
            if (data.motivations && Object.keys(data.motivations).length > 0) {
                html += `
                    <div class="info-card">
                        <div class="info-label">Motivazioni partecipazione</div>
                        <div class="info-value">
                            ${Object.entries(data.motivations)
                                .sort((a, b) => b[1] - a[1])
                                .slice(0, 5)
                                .map(([mot, count]) => `${mot}: ${count}`)
                                .join(' • ')}
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        
        function renderFeedback(data) {
            const container = document.getElementById('feedback-container');
            if (!data || !data.total_responses) {
                container.innerHTML = '<p class="info-value">Dati non disponibili</p>';
                return;
            }
            
            let html = '<div class="grid-2">';
            
            // Overall rating
            if (data.overall_rating) {
                const rating = data.overall_rating;
                html += `
                    <div class="info-card">
                        <div class="info-label">Valutazione complessiva</div>
                        <div class="info-value">
                            <strong style="font-size: 1.5rem; color: #a855f7;">${rating.average}/5</strong><br>
                            ${Object.entries(rating.distribution || {})
                                .sort((a, b) => b[0] - a[0])
                                .map(([stars, count]) => `${'⭐'.repeat(parseInt(stars))}: ${count}`)
                                .join('<br>')}
                        </div>
                    </div>
                `;
            }
            
            // Networking rating
            if (data.networking_rating) {
                const rating = data.networking_rating;
                html += `
                    <div class="info-card">
                        <div class="info-label">Valutazione networking</div>
                        <div class="info-value">
                            <strong style="font-size: 1.5rem; color: #a855f7;">${rating.average}/5</strong><br>
                            ${Object.entries(rating.distribution || {})
                                .sort((a, b) => b[0] - a[0])
                                .map(([stars, count]) => `${'⭐'.repeat(parseInt(stars))}: ${count}`)
                                .join('<br>')}
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            
            // Future interest
            if (data.future_interest && Object.keys(data.future_interest).length > 0) {
                html += `
                    <div class="info-card">
                        <div class="info-label">Interesse eventi futuri</div>
                        <div class="info-value">
                            ${Object.entries(data.future_interest)
                                .map(([answer, count]) => `${answer}: ${count}`)
                                .join(' • ')}
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        
        function renderGPTAnalysis(gptData) {
            if (!gptData || !gptData.summary) return;
            
            document.getElementById('gpt-section').style.display = 'block';
            const container = document.getElementById('gpt-container');
            
            let html = `
                <div class="info-card">
                    <div class="info-label">Sommario</div>
                    <div class="info-value">${gptData.summary}</div>
                </div>
            `;
            
            if (gptData.key_improvements && gptData.key_improvements.length > 0) {
                html += `
                    <div class="info-card">
                        <div class="info-label">Punti di miglioramento principali</div>
                        <div class="info-value">
                            <ul style="margin-left: 20px;">
                                ${gptData.key_improvements.map(imp => `<li>${imp}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                `;
            }
            
            if (gptData.categories && Object.keys(gptData.categories).length > 0) {
                html += `<div class="info-card"><div class="info-label">Categorie feedback</div><div class="info-value">`;
                for (const [category, items] of Object.entries(gptData.categories)) {
                    html += `<strong>${category}:</strong><br><ul style="margin-left: 20px; margin-bottom: 10px;">`;
                    items.forEach(item => {
                        html += `<li>${item}</li>`;
                    });
                    html += `</ul>`;
                }
                html += `</div></div>`;
            }
            
            container.innerHTML = html;
        }
        
        function renderJobTitles(jobTitles) {
            if (!jobTitles || !jobTitles.list || jobTitles.list.length === 0) return;
            
            document.getElementById('job-titles-section').style.display = 'block';
            const container = document.getElementById('job-titles-container');
            
            container.innerHTML = `
                <div class="info-card">
                    <div class="info-label">${jobTitles.unique} job titles unici (${jobTitles.total} totali)</div>
                    <div class="tags-container">
                        ${jobTitles.list.map(j => `<span class="tag">${j}</span>`).join('')}
                    </div>
                </div>
            `;
        }
        
        function renderCompanies(companies) {
            if (!companies || !companies.list || companies.list.length === 0) return;
            
            document.getElementById('companies-section').style.display = 'block';
            const container = document.getElementById('companies-container');
            
            container.innerHTML = `
                <div class="info-card">
                    <div class="info-label">${companies.total_unique} aziende rappresentate</div>
                    <div class="tags-container">
                        ${companies.list.sort().map(c => `<span class="tag">${c}</span>`).join('')}
                    </div>
                </div>
            `;
        }
        
        function init() {
            // Titolo
            document.getElementById('event-title').textContent = eventData.event_name || 'Evento';
            
            // Render sezioni
            renderKPIs(eventData.kpis || {});
            renderProfiling(eventData.profiling_data || {});
            renderFeedback(eventData.feedback_data || {});
            
            if (eventData.feedback_data && eventData.feedback_data.gpt_analysis) {
                renderGPTAnalysis(eventData.feedback_data.gpt_analysis);
            }
            
            if (eventData.profiling_data && eventData.profiling_data.job_titles) {
                renderJobTitles(eventData.profiling_data.job_titles);
            }
            
            if (eventData.profiling_data && eventData.profiling_data.companies) {
                renderCompanies(eventData.profiling_data.companies);
            }
            
            // Footer
            const date = new Date(eventData.analysis_date);
            document.getElementById('footer-text').textContent = 
                `Report generato il ${date.toLocaleDateString('it-IT')} • ${eventData.profiling_data?.total_responses || 0} risposte`;
        }
        
        init();
    </script>
</body>
</html>
"""
    
    # Sostituisci placeholder
    html_content = html_template.replace('EVENT_NAME', data['event_name'])
    html_content = html_content.replace('EVENT_DATA_PLACEHOLDER', json.dumps(data, ensure_ascii=False, indent=2))
    
    # Salva
    output_file = event_path / 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Pagina evento generata: {output_file}")
    return True


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python generate_event_page.py <event_folder>")
        sys.exit(1)
    
    generate_event_page(sys.argv[1])

