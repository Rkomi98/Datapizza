// Global variables
let startupData = [];
let filteredData = [];
let map = null;
let markersGroup = null;
let charts = {};
let currentPage = 1;
const itemsPerPage = 20;
let currentSort = { field: null, direction: 'asc' };

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    showLoading(true);
    
    try {
        // await loadData(); // Rimuovo il caricamento dati precedente
        startupData = startup_data.startup_data; // Uso i dati dallo script
        filteredData = [...startupData];

        initializeFilters();
        
        // Initialize map with better loading feedback
        await initializeMapWithProgress();
        
        initializeCharts();
        initializeTable();
        initializeEventListeners();
        applyFilters();
        
        // Hide loading after everything is initialized
        setTimeout(() => showLoading(false), 300);
    } catch (error) {
        console.error('Error initializing app:', error);
        showLoading(false);
    }
}

// Data loading
/* Rimuovo la vecchia funzione loadData
async function loadData() {
    const sources = [
        './startup_lombardia_data.json',
        'startup_lombardia_data.json',
        'https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/901e467b5dbb0552e479b311b228bd46/830cd162-dd44-4cf6-b323-e19b8577a4e9/fea0a35a.json'
    ];

    for (const url of sources) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const payload = await response.json();
            const records = Array.isArray(payload) ? payload : payload.startup_data || payload.data;

            if (Array.isArray(records) && records.length) {
                startupData = records.length > 50 ? records : generateSampleData(records);
                filteredData = [...startupData];
                console.log('Data loaded:', startupData.length, 'startups from', url);
                return;
            }
        } catch (error) {
            console.warn('Data source failed:', url, error);
        }
    }

    console.error('All data sources failed, using fallback dataset');
    startupData = generateFallbackData();
    filteredData = [...startupData];
}
*/
function generateSampleData(baseData) {
    const provinces = ["Milano", "Bergamo", "Brescia", "Como", "Cremona", "Mantova", "Pavia", "Sondrio", "Varese", "Lecco", "Lodi", "Monza e della Brianza"];
    const sectors = ["Fintech", "Blockchain", "Aerospace", "Automazione Industriale", "Automotive Tech", "Biotecnologie", "Cleantech", "Computer e Prodotti Elettronici", "Cybersecurity", "E-commerce", "Energia Rinnovabile", "Fabbricazione Macchinari", "Intelligenza Artificiale", "IoT", "Marketing Digitale", "Ricerca e Sviluppo", "Robotica", "Salute Digitale", "Servizi di Informazione", "Software & Consulenza Informatica"];
    const years = [2019, 2020, 2021, 2022, 2023, 2024, 2025];
    
    const provinceCoords = {
        "Milano": [45.4642, 9.1900],
        "Bergamo": [45.6983, 9.6773],
        "Brescia": [45.5416, 10.2118],
        "Como": [45.8081, 9.0852],
        "Cremona": [45.1335, 10.0227],
        "Mantova": [45.1564, 10.7914],
        "Pavia": [45.1847, 9.1582],
        "Sondrio": [46.1712, 9.8734],
        "Varese": [45.8205, 8.8250],
        "Lecco": [45.8564, 9.3933],
        "Lodi": [45.3142, 9.5034],
        "Monza e della Brianza": [45.5845, 9.2744]
    };
    
    const companyNames = [
        "TechNova", "InnovateLab", "DataFlow", "SmartSystems", "FutureLogic", "DigitalCore", "NextGen Solutions", "CyberTech",
        "BioInnovate", "CleanEnergy Pro", "RoboticsMilan", "FinanceAI", "HealthTech", "GreenTech Solutions", "AutoInnovate",
        "Spacetech", "IoT Solutions", "BlockchainItalia", "CyberSecure", "EcommercePro", "RenewableEnergy", "MachineTech",
        "AILombardia", "SmartIoT", "DigitalMarketing Pro", "R&D Labs", "RoboticsPlus", "DigitalHealth", "InfoServices", "SoftwareConsult"
    ];
    
    const data = [];
    
    // Generate 3500 startups
    for (let i = 0; i < 3500; i++) {
        const province = provinces[Math.floor(Math.random() * provinces.length)];
        const coords = provinceCoords[province];
        const year = years[Math.floor(Math.random() * years.length)];
        const sectorCount = Math.floor(Math.random() * 3) + 1; // 1-3 sectors
        const selectedSectors = [];
        
        for (let j = 0; j < sectorCount; j++) {
            const sector = sectors[Math.floor(Math.random() * sectors.length)];
            if (!selectedSectors.includes(sector)) {
                selectedSectors.push(sector);
            }
        }
        
        const startup = {
            id: `SU${String(i + 1).padStart(5, '0')}`,
            nome: `${companyNames[Math.floor(Math.random() * companyNames.length)]} ${Math.random() > 0.7 ? 'S.R.L.' : 'S.P.A.'}`,
            indirizzo: `Via ${Math.random() > 0.5 ? 'Roma' : 'Milano'}, ${Math.floor(Math.random() * 200) + 1}`,
            provincia: province,
            coordinate_lat: coords[0] + (Math.random() - 0.5) * 0.2,
            coordinate_lon: coords[1] + (Math.random() - 0.5) * 0.2,
            anno_costituzione: year,
            settori_tag: selectedSectors,
            capitale_sociale: Math.floor(Math.random() * 180000) + 10000,
            valore_produzione: Math.floor(Math.random() * 900000) + 50000,
            dipendenti: Math.floor(Math.random() * 45) + 1,
            status_attivo: Math.random() > 0.08 // 92% active
        };
        
        data.push(startup);
    }
    
    return data;
}

function generateFallbackData() {
    // Fallback minimal data if API fails
    return [
        {
            id: "SU00001",
            nome: "FutureLogic S.R.L.",
            indirizzo: "Via Brera, 83",
            provincia: "Milano",
            coordinate_lat: 45.47792326829273,
            coordinate_lon: 9.195073292914222,
            anno_costituzione: 2022,
            settori_tag: ["Fintech"],
            capitale_sociale: 19552,
            valore_produzione: 39053,
            dipendenti: 2,
            status_attivo: true
        },
        {
            id: "SU00002",
            nome: "SmartEngine S.R.L.",
            indirizzo: "Via Dante, 59",
            provincia: "Milano",
            coordinate_lat: 45.485806209417244,
            coordinate_lon: 9.186961783426806,
            anno_costituzione: 2021,
            settori_tag: ["Blockchain"],
            capitale_sociale: 16759,
            valore_produzione: 181463,
            dipendenti: 1,
            status_attivo: true
        }
    ];
}

// Initialize filters
function initializeFilters() {
    initializeSectorFilter();
    initializeProvinceFilter();
    initializeRangeSliders();
}

function initializeSectorFilter() {
    const sectors = [...new Set(startupData.flatMap(s => s.settori_tag))].sort();
    const container = document.getElementById('sector-options');
    
    container.innerHTML = '';
    sectors.forEach(sector => {
        const count = startupData.filter(s => s.settori_tag.includes(sector)).length;
        const div = document.createElement('div');
        div.className = 'sector-option';
        div.innerHTML = `
            <label>
                <input type="checkbox" value="${sector}">
                ${sector}
            </label>
            <span class="sector-count">${count}</span>
        `;
        container.appendChild(div);
    });
    
    // Sector search functionality
    const searchInput = document.querySelector('.sector-search');
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const options = container.querySelectorAll('.sector-option');
        
        options.forEach(option => {
            const text = option.textContent.toLowerCase();
            option.style.display = text.includes(searchTerm) ? 'flex' : 'none';
        });
    });
}

function initializeProvinceFilter() {
    const provinces = [...new Set(startupData.map(s => s.provincia))].sort();
    const container = document.getElementById('province-options');
    
    container.innerHTML = '';
    provinces.forEach(province => {
        const count = startupData.filter(s => s.provincia === province).length;
        const div = document.createElement('div');
        div.className = 'province-option';
        div.innerHTML = `
            <label>
                <input type="checkbox" value="${province}" checked>
                ${province}
            </label>
            <span class="province-count">${count}</span>
        `;
        container.appendChild(div);
    });
}

function initializeRangeSliders() {
    // Year range
    setupRangeSlider('year', 2019, 2025);
    
    // Capital range
    setupRangeSlider('capital', 0, 200000, 1000);
    
    // Production range
    setupRangeSlider('production', 0, 1000000, 10000);
    
    // Employees range
    setupRangeSlider('employees', 0, 50);
}

function setupRangeSlider(prefix, min, max, step = 1) {
    const minSlider = document.getElementById(`${prefix}-min`);
    const maxSlider = document.getElementById(`${prefix}-max`);
    const minValue = document.getElementById(`${prefix}-min-val`);
    const maxValue = document.getElementById(`${prefix}-max-val`);
    
    minSlider.min = min;
    minSlider.max = max;
    minSlider.step = step;
    minSlider.value = min;
    
    maxSlider.min = min;
    maxSlider.max = max;
    maxSlider.step = step;
    maxSlider.value = max;
    
    function updateValues() {
        let minVal = parseInt(minSlider.value);
        let maxVal = parseInt(maxSlider.value);
        
        if (minVal >= maxVal) {
            if (minSlider === document.activeElement) {
                maxSlider.value = minVal + step;
                maxVal = minVal + step;
            } else {
                minSlider.value = maxVal - step;
                minVal = maxVal - step;
            }
        }
        
        // Format display values
        if (prefix === 'capital') {
            minValue.textContent = formatCurrency(minVal);
            maxValue.textContent = formatCurrency(maxVal);
        } else if (prefix === 'production') {
            minValue.textContent = formatCurrency(minVal);
            maxValue.textContent = formatCurrency(maxVal);
        } else {
            minValue.textContent = minVal;
            maxValue.textContent = maxVal;
        }
        
        applyFilters();
    }
    
    minSlider.addEventListener('input', updateValues);
    maxSlider.addEventListener('input', updateValues);
    
    // Initialize display
    updateValues();
}

// Improved map initialization with progress feedback
async function initializeMapWithProgress() {
    return new Promise((resolve) => {
        // Add loading text to map container
        const mapContainer = document.getElementById('map');
        mapContainer.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--color-text-secondary); font-size: 14px;">Caricamento mappa...</div>';
        
        setTimeout(() => {
            try {
                map = L.map('map').setView([45.6, 9.5], 8);
                
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);
                
                markersGroup = L.markerClusterGroup({
                    chunkedLoading: true,
                    maxClusterRadius: 50,
                    spiderfyOnMaxZoom: true,
                    showCoverageOnHover: false,
                    zoomToBoundsOnClick: true
                });
                
                map.addLayer(markersGroup);
                
                // Force map resize after initialization
                setTimeout(() => {
                    map.invalidateSize();
                    resolve();
                }, 100);
                
            } catch (error) {
                console.error('Error initializing map:', error);
                mapContainer.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--color-error); font-size: 14px;">Errore nel caricamento della mappa</div>';
                resolve();
            }
        }, 100);
    });
}

function updateMap() {
    if (!map || !markersGroup) return;
    
    markersGroup.clearLayers();
    
    const provinceColors = {
        'Milano': '#1FB8CD',
        'Bergamo': '#FFC185',
        'Brescia': '#B4413C',
        'Como': '#ECEBD5',
        'Cremona': '#5D878F',
        'Mantova': '#DB4545',
        'Pavia': '#D2BA4C',
        'Sondrio': '#964325',
        'Varese': '#944454',
        'Lecco': '#13343B',
        'Lodi': '#1FB8CD',
        'Monza e della Brianza': '#FFC185'
    };
    
    // Process markers in smaller batches to improve performance
    const batchSize = 100;
    let processed = 0;
    
    function processBatch() {
        const batch = filteredData.slice(processed, processed + batchSize);
        
        batch.forEach(startup => {
            if (startup.coordinate_lat && startup.coordinate_lon) {
                const color = provinceColors[startup.provincia] || '#1FB8CD';
                
                const marker = L.circleMarker([startup.coordinate_lat, startup.coordinate_lon], {
                    radius: 6,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                });
                
                const popupContent = `
                    <div style="min-width: 200px;">
                        <h4 style="margin: 0 0 8px 0; color: var(--color-primary);">${startup.nome}</h4>
                        <p style="margin: 4px 0; font-size: 12px;"><strong>Provincia:</strong> ${startup.provincia}</p>
                        <p style="margin: 4px 0; font-size: 12px;"><strong>Anno:</strong> ${startup.anno_costituzione}</p>
                        <p style="margin: 4px 0; font-size: 12px;"><strong>Settori:</strong> ${startup.settori_tag.join(', ')}</p>
                        <p style="margin: 4px 0; font-size: 12px;"><strong>Dipendenti:</strong> ${startup.dipendenti}</p>
                        <button onclick="showStartupDetails('${startup.id}')" style="margin-top: 8px; padding: 4px 8px; background: var(--color-primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                            Dettagli
                        </button>
                    </div>
                `;
                
                marker.bindPopup(popupContent);
                markersGroup.addLayer(marker);
            }
        });
        
        processed += batchSize;
        
        if (processed < filteredData.length) {
            setTimeout(processBatch, 10); // Small delay between batches
        }
    }
    
    processBatch();
}

// Charts initialization
function initializeCharts() {
    initializeProvinceChart();
    initializeYearChart();
    initializeSectorChart();
    initializeScatterChart();
}

function initializeProvinceChart() {
    const ctx = document.getElementById('province-chart').getContext('2d');
    charts.province = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Numero Startup',
                data: [],
                backgroundColor: '#1FB8CD',
                borderColor: '#1FB8CD',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const province = charts.province.data.labels[index];
                    filterByProvince(province);
                }
            }
        }
    });
}

function initializeYearChart() {
    const ctx = document.getElementById('year-chart').getContext('2d');
    charts.year = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Nuove Startup',
                data: [],
                borderColor: '#FFC185',
                backgroundColor: 'rgba(255, 193, 133, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

function initializeSectorChart() {
    const ctx = document.getElementById('sector-chart').getContext('2d');
    charts.sector = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: ['#1FB8CD', '#FFC185', '#B4413C', '#ECEBD5', '#5D878F', '#DB4545', '#D2BA4C', '#964325', '#944454', '#13343B']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 8,
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

function initializeScatterChart() {
    const ctx = document.getElementById('scatter-chart').getContext('2d');
    charts.scatter = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Startup',
                data: [],
                backgroundColor: 'rgba(31, 184, 205, 0.6)',
                borderColor: '#1FB8CD'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Capitale Sociale (€)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Valore Produzione (€)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}

// Update charts with filtered data
function updateCharts() {
    updateProvinceChart();
    updateYearChart();
    updateSectorChart();
    updateScatterChart();
}

function updateProvinceChart() {
    const provinceData = {};
    filteredData.forEach(startup => {
        provinceData[startup.provincia] = (provinceData[startup.provincia] || 0) + 1;
    });
    
    const sortedData = Object.entries(provinceData).sort((a, b) => b[1] - a[1]);
    
    charts.province.data.labels = sortedData.map(d => d[0]);
    charts.province.data.datasets[0].data = sortedData.map(d => d[1]);
    charts.province.update();
}

function updateYearChart() {
    const yearData = {};
    filteredData.forEach(startup => {
        yearData[startup.anno_costituzione] = (yearData[startup.anno_costituzione] || 0) + 1;
    });
    
    const years = [2019, 2020, 2021, 2022, 2023, 2024, 2025];
    
    charts.year.data.labels = years;
    charts.year.data.datasets[0].data = years.map(year => yearData[year] || 0);
    charts.year.update();
}

function updateSectorChart() {
    const sectorData = {};
    filteredData.forEach(startup => {
        startup.settori_tag.forEach(sector => {
            sectorData[sector] = (sectorData[sector] || 0) + 1;
        });
    });
    
    // Show top 10 sectors
    const sortedSectors = Object.entries(sectorData)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    charts.sector.data.labels = sortedSectors.map(d => d[0]);
    charts.sector.data.datasets[0].data = sortedSectors.map(d => d[1]);
    charts.sector.update();
}

function updateScatterChart() {
    const scatterData = filteredData.map(startup => ({
        x: startup.capitale_sociale,
        y: startup.valore_produzione,
        startup: startup
    }));
    
    charts.scatter.data.datasets[0].data = scatterData;
    charts.scatter.update();
}

// Table management
function initializeTable() {
    updateTable();
    initializeTableSorting();
}

function updateTable() {
    const tbody = document.getElementById('table-body');
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageData = filteredData.slice(start, end);
    
    tbody.innerHTML = '';
    
    pageData.forEach(startup => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${startup.nome}</td>
            <td>${startup.provincia}</td>
            <td>${startup.anno_costituzione}</td>
            <td>${startup.settori_tag.join(', ')}</td>
            <td>${formatCurrency(startup.capitale_sociale)}</td>
            <td>${formatCurrency(startup.valore_produzione)}</td>
            <td>${startup.dipendenti}</td>
        `;
        
        row.addEventListener('click', () => showStartupDetails(startup.id));
        tbody.appendChild(row);
    });
    
    updatePagination();
    updateResultsCount();
}

function initializeTableSorting() {
    const headers = document.querySelectorAll('.startup-table th[data-sort]');
    
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const field = header.dataset.sort;
            
            if (currentSort.field === field) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.field = field;
                currentSort.direction = 'asc';
            }
            
            sortData();
            updateSortIndicators();
            currentPage = 1;
            updateTable();
        });
    });
}

function sortData() {
    const field = currentSort.field;
    const direction = currentSort.direction;
    
    filteredData.sort((a, b) => {
        let valueA = a[field];
        let valueB = b[field];
        
        if (field === 'settori_tag') {
            valueA = valueA.join(', ');
            valueB = valueB.join(', ');
        }
        
        if (typeof valueA === 'string') {
            valueA = valueA.toLowerCase();
            valueB = valueB.toLowerCase();
        }
        
        if (direction === 'asc') {
            return valueA > valueB ? 1 : -1;
        } else {
            return valueA < valueB ? 1 : -1;
        }
    });
}

function updateSortIndicators() {
    const headers = document.querySelectorAll('.startup-table th[data-sort]');
    
    headers.forEach(header => {
        header.classList.remove('sorted');
        const arrow = header.querySelector('.sort-arrow');
        arrow.textContent = '↕️';
        
        if (header.dataset.sort === currentSort.field) {
            header.classList.add('sorted');
            arrow.textContent = currentSort.direction === 'asc' ? '↑' : '↓';
        }
    });
}

function updatePagination() {
    const totalPages = Math.ceil(filteredData.length / itemsPerPage);
    const pagination = document.getElementById('pagination');
    
    pagination.innerHTML = '';
    
    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '← Precedente';
    prevBtn.disabled = currentPage === 1;
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            updateTable();
        }
    });
    pagination.appendChild(prevBtn);
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.classList.toggle('active', i === currentPage);
        btn.addEventListener('click', () => {
            currentPage = i;
            updateTable();
        });
        pagination.appendChild(btn);
    }
    
    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Successiva →';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            updateTable();
        }
    });
    pagination.appendChild(nextBtn);
}

function updateResultsCount() {
    const count = document.getElementById('results-count');
    count.textContent = `${filteredData.length} risultati`;
}

// Filter application
function applyFilters() {
    // Remove any unwanted visual selections
    clearTemporarySelections();
    
    showLoading(true, 200);
    
    setTimeout(() => {
        filteredData = startupData.filter(startup => {
            // Search filter
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            if (searchTerm && !startup.nome.toLowerCase().includes(searchTerm)) {
                return false;
            }
            
            // Sector filter
            const selectedSectors = Array.from(document.querySelectorAll('#sector-options input:checked'))
                .map(cb => cb.value);
            if (selectedSectors.length > 0) {
                const hasMatchingSector = selectedSectors.some(sector => startup.settori_tag.includes(sector));
                if (!hasMatchingSector) return false;
            }
            
            // Year filter
            const minYear = parseInt(document.getElementById('year-min').value);
            const maxYear = parseInt(document.getElementById('year-max').value);
            if (startup.anno_costituzione < minYear || startup.anno_costituzione > maxYear) {
                return false;
            }
            
            // Province filter
            const selectedProvinces = Array.from(document.querySelectorAll('#province-options input:checked'))
                .map(cb => cb.value);
            if (selectedProvinces.length > 0 && !selectedProvinces.includes(startup.provincia)) {
                return false;
            }
            
            // Status filter
            const activeOnly = document.getElementById('active-only').checked;
            if (activeOnly && !startup.status_attivo) {
                return false;
            }
            
            // Capital filter
            const minCapital = parseInt(document.getElementById('capital-min').value);
            const maxCapital = parseInt(document.getElementById('capital-max').value);
            if (startup.capitale_sociale < minCapital || startup.capitale_sociale > maxCapital) {
                return false;
            }
            
            // Production filter
            const minProduction = parseInt(document.getElementById('production-min').value);
            const maxProduction = parseInt(document.getElementById('production-max').value);
            if (startup.valore_produzione < minProduction || startup.valore_produzione > maxProduction) {
                return false;
            }
            
            // Employees filter
            const minEmployees = parseInt(document.getElementById('employees-min').value);
            const maxEmployees = parseInt(document.getElementById('employees-max').value);
            if (startup.dipendenti < minEmployees || startup.dipendenti > maxEmployees) {
                return false;
            }
            
            return true;
        });
        
        currentPage = 1;
        updateKPIs();
        updateMap();
        updateCharts();
        updateTable();
        
        showLoading(false);
    }, 100);
}

// Fix for visual selection bug
function clearTemporarySelections() {
    // Clear any unintended text selections
    if (window.getSelection) {
        window.getSelection().removeAllRanges();
    }
    
    // Remove focus from any active elements that might cause highlighting
    const activeElement = document.activeElement;
    if (activeElement && activeElement !== document.body) {
        activeElement.blur();
    }
}

// KPI Updates
function updateKPIs() {
    const totalStartups = filteredData.length;
    const totalCapital = filteredData.reduce((sum, s) => sum + s.capitale_sociale, 0);
    const avgProduction = totalStartups > 0 ? filteredData.reduce((sum, s) => sum + s.valore_produzione, 0) / totalStartups : 0;
    const totalEmployees = filteredData.reduce((sum, s) => sum + s.dipendenti, 0);
    
    document.getElementById('filtered-total').textContent = totalStartups.toLocaleString();
    document.getElementById('total-capital').textContent = formatCurrency(totalCapital);
    document.getElementById('avg-production').textContent = formatCurrency(avgProduction);
    document.getElementById('total-jobs').textContent = totalEmployees.toLocaleString();
}

// Event listeners
function initializeEventListeners() {
    // Search input
    document.getElementById('search-input').addEventListener('input', debounce(applyFilters, 300));
    
    // Sector checkboxes
    document.getElementById('sector-options').addEventListener('change', applyFilters);
    
    // Province checkboxes
    document.getElementById('province-options').addEventListener('change', applyFilters);
    
    // Status toggle
    document.getElementById('active-only').addEventListener('change', applyFilters);
    
    // Reset filters
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
    
    // Export CSV
    document.getElementById('export-csv').addEventListener('click', exportCSV);
    
    // Modal close
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('startup-modal').addEventListener('click', (e) => {
        if (e.target.id === 'startup-modal') {
            closeModal();
        }
    });
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatCurrency(value) {
    if (value >= 1000000) {
        return '€' + (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
        return '€' + (value / 1000).toFixed(0) + 'k';
    } else {
        return '€' + value.toLocaleString();
    }
}

function showLoading(show, delay = 0) {
    const overlay = document.getElementById('loading-overlay');
    if (delay > 0) {
        setTimeout(() => {
            overlay.classList.toggle('hidden', !show);
        }, show ? 0 : delay);
    } else {
        overlay.classList.toggle('hidden', !show);
    }
}

function resetFilters() {
    // Reset search
    document.getElementById('search-input').value = '';
    
    // Reset sectors
    document.querySelectorAll('#sector-options input').forEach(cb => cb.checked = false);
    
    // Reset provinces
    document.querySelectorAll('#province-options input').forEach(cb => cb.checked = true);
    
    // Reset ranges
    document.getElementById('year-min').value = 2019;
    document.getElementById('year-max').value = 2025;
    document.getElementById('capital-min').value = 0;
    document.getElementById('capital-max').value = 200000;
    document.getElementById('production-min').value = 0;
    document.getElementById('production-max').value = 1000000;
    document.getElementById('employees-min').value = 0;
    document.getElementById('employees-max').value = 50;
    
    // Reset status
    document.getElementById('active-only').checked = true;
    
    // Update displays
    initializeRangeSliders();
    applyFilters();
}

function filterByProvince(province) {
    // Uncheck all provinces first
    document.querySelectorAll('#province-options input').forEach(cb => cb.checked = false);
    
    // Check only the selected province
    const provinceCheckbox = document.querySelector(`#province-options input[value="${province}"]`);
    if (provinceCheckbox) {
        provinceCheckbox.checked = true;
        applyFilters();
    }
}

function showStartupDetails(startupId) {
    const startup = startupData.find(s => s.id === startupId);
    if (!startup) return;
    
    const modal = document.getElementById('startup-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    
    title.textContent = startup.nome;
    
    body.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <div>
                <h4 style="color: var(--color-primary); margin: 0 0 8px 0;">Informazioni Generali</h4>
                <p><strong>ID:</strong> ${startup.id}</p>
                <p><strong>Indirizzo:</strong> ${startup.indirizzo}</p>
                <p><strong>Provincia:</strong> ${startup.provincia}</p>
                <p><strong>Anno di Costituzione:</strong> ${startup.anno_costituzione}</p>
                <p><strong>Status:</strong> <span class="status ${startup.status_attivo ? 'status--success' : 'status--error'}">${startup.status_attivo ? 'Attiva' : 'Inattiva'}</span></p>
            </div>
            <div>
                <h4 style="color: var(--color-primary); margin: 0 0 8px 0;">Dati Economici</h4>
                <p><strong>Capitale Sociale:</strong> ${formatCurrency(startup.capitale_sociale)}</p>
                <p><strong>Valore Produzione:</strong> ${formatCurrency(startup.valore_produzione)}</p>
                <p><strong>Dipendenti:</strong> ${startup.dipendenti}</p>
            </div>
        </div>
        <div style="margin-top: 16px;">
            <h4 style="color: var(--color-primary); margin: 0 0 8px 0;">Settori di Attività</h4>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                ${startup.settori_tag.map(tag => `<span class="status status--info">${tag}</span>`).join('')}
            </div>
        </div>
    `;
    
    modal.classList.remove('hidden');
}

function closeModal() {
    document.getElementById('startup-modal').classList.add('hidden');
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-color-scheme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-color-scheme', newTheme);
    
    const themeIcon = document.querySelector('.theme-icon');
    themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
    
    // Save preference
    localStorage.setItem('theme', newTheme);
}

function exportCSV() {
    const headers = ['Nome', 'Provincia', 'Anno', 'Settori', 'Capitale', 'Produzione', 'Dipendenti', 'Status'];
    
    const csvData = [
        headers.join(','),
        ...filteredData.map(startup => [
            `"${startup.nome}"`,
            startup.provincia,
            startup.anno_costituzione,
            `"${startup.settori_tag.join('; ')}"`,
            startup.capitale_sociale,
            startup.valore_produzione,
            startup.dipendenti,
            startup.status_attivo ? 'Attiva' : 'Inattiva'
        ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `startup_lombardia_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
}

// Initialize theme on load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-color-scheme', savedTheme);
    
    const themeIcon = document.querySelector('.theme-icon');
    if (themeIcon) {
        themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
    }
});
