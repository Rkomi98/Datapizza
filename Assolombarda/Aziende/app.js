// Global variables
let map;
let markers = [];
let markerClusterGroup;
let organizationsData = [];
let geocodedData = [];
let filteredData = [];
let colorMap = {};
let filteredMarkers = [];
let currentView = 'map';

// Table state
let currentSort = { column: null, direction: 'asc' };
let currentPage = 1;
let rowsPerPage = 25;
let searchTerm = '';

// Color palette for different tipologie
const colors = ['#1FB8CD', '#FFC185', '#B4413C', '#ECEBD5', '#5D878F', '#DB4545', '#D2BA4C', '#964325', '#944454', '#13343B'];

// Rate limiting for geocoding
let geocodingQueue = [];
let geocodingInProgress = false;
const GEOCODING_DELAY = 1100; // 1.1 seconds to respect Nominatim rate limit

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Load organization data
        organizationsData = soggetti_data.soggetti;
        
        // Setup filters
        setupFilters();
        
        // Initialize map
        initializeMap();
        
        // Start geocoding process
        await geocodeAddresses();
        
        // Create markers and populate map
        createMarkers();
        
        // Initialize filtered data
        filteredData = [...geocodedData];
        
        // Hide loading overlay
        hideLoadingOverlay();
        
        // Setup event listeners
        setupEventListeners();
        
        // Update displays
        updateStatistics();
        updateTableView();
        
    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Errore durante l\'inizializzazione dell\'applicazione: ' + error.message);
    }
}

function setupFilters() {
    const tipologieSet = new Set();
    const comuniSet = new Set();
    
    organizationsData.forEach((org, index) => {
        tipologieSet.add(org.tipologia);
        
        // Extract comune from address
        const comune = extractComune(org.indirizzo_pulito);
        if (comune) {
            comuniSet.add(comune);
        }
        
        // Assign color to tipologia
        if (!colorMap[org.tipologia]) {
            const colorIndex = Object.keys(colorMap).length % colors.length;
            colorMap[org.tipologia] = colors[colorIndex];
        }
    });
    
    // Populate tipologia filter
    const tipologiaSelect = document.getElementById('tipologia-filter');
    Array.from(tipologieSet).sort().forEach(tipologia => {
        const option = document.createElement('option');
        option.value = tipologia;
        option.textContent = tipologia.charAt(0).toUpperCase() + tipologia.slice(1);
        tipologiaSelect.appendChild(option);
    });
    
    // Populate comune filter
    const comuneSelect = document.getElementById('comune-filter');
    Array.from(comuniSet).sort().forEach(comune => {
        const option = document.createElement('option');
        option.value = comune;
        option.textContent = comune;
        comuneSelect.appendChild(option);
    });
    
    // Create legend
    createLegend();
}

function extractComune(address) {
    // Extract city name from Italian address
    const patterns = [
        /(\w+)\s*\([A-Z]{2}\)/, // City (Province)
        /\d+\s+([A-Za-z\s]+)\s*(?:\([A-Z]{2}\)|$)/, // After postal code
        /,\s*(\w+)$/ // Last word after comma
    ];
    
    for (const pattern of patterns) {
        const match = address.match(pattern);
        if (match) {
            return match[1].trim();
        }
    }
    
    // Fallback: try to extract from known cities
    const knownCities = ['Milano', 'Roma', 'Pavia', 'Bergamo', 'Brescia', 'Varese', 'Como', 'Lecco', 'Lodi', 'Padova'];
    for (const city of knownCities) {
        if (address.includes(city)) {
            return city;
        }
    }
    
    return null;
}

function createLegend() {
    const legendContainer = document.getElementById('legend-container');
    
    Object.entries(colorMap).forEach(([tipologia, color]) => {
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        
        const colorDiv = document.createElement('div');
        colorDiv.className = 'legend-color';
        colorDiv.style.backgroundColor = color;
        
        const textSpan = document.createElement('span');
        textSpan.className = 'legend-text';
        textSpan.textContent = tipologia.charAt(0).toUpperCase() + tipologia.slice(1);
        
        legendItem.appendChild(colorDiv);
        legendItem.appendChild(textSpan);
        legendContainer.appendChild(legendItem);
    });
}

function initializeMap() {
    // Initialize map centered on Lombardy
    map = L.map('map').setView([45.4642, 9.1900], 8);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Initialize marker cluster group
    markerClusterGroup = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 50
    });
    
    map.addLayer(markerClusterGroup);
}

async function geocodeAddresses() {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const total = organizationsData.length;
    let completed = 0;
    
    for (const org of organizationsData) {
        try {
            const coordinates = await geocodeAddress(org.indirizzo_pulito);
            geocodedData.push({
                ...org,
                lat: coordinates.lat,
                lng: coordinates.lng,
                geocoded: true,
                comune: extractComune(org.indirizzo_pulito)
            });
        } catch (error) {
            console.warn(`Failed to geocode ${org.soggetto}:`, error);
            // Add with default coordinates (Milan center)
            geocodedData.push({
                ...org,
                lat: 45.4642,
                lng: 9.1900,
                geocoded: false,
                comune: extractComune(org.indirizzo_pulito)
            });
        }
        
        completed++;
        const progress = (completed / total) * 100;
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `${Math.round(progress)}%`;
        
        // Rate limiting delay
        await new Promise(resolve => setTimeout(resolve, GEOCODING_DELAY));
    }
}

async function geocodeAddress(address) {
    const encodedAddress = encodeURIComponent(`${address}, Italy`);
    const url = `https://nominatim.openstreetmap.org/search?q=${encodedAddress}&format=json&limit=1`;
    
    const response = await fetch(url, {
        headers: {
            'User-Agent': 'Dashboard Organizzazioni Lombardia'
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data && data.length > 0) {
        return {
            lat: parseFloat(data[0].lat),
            lng: parseFloat(data[0].lon)
        };
    } else {
        throw new Error('No results found');
    }
}

function createMarkers() {
    markers = [];
    
    geocodedData.forEach(org => {
        const color = colorMap[org.tipologia];
        
        // Create custom icon
        const icon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
        
        // Create marker
        const marker = L.marker([org.lat, org.lng], { icon: icon });
        
        // Create popup content
        const popupContent = document.createElement('div');
        popupContent.innerHTML = `
            <div class="popup-title">${org.soggetto}</div>
            <div class="popup-type">${org.tipologia}</div>
            ${!org.geocoded ? '<div style="color: orange; font-size: 12px; margin-top: 8px;">⚠️ Posizione approssimativa</div>' : ''}
        `;
        
        // Add website link if available
        if (org['Sito web']) {
            const linkDiv = document.createElement('div');
            linkDiv.style.marginTop = '8px';
            
            const link = document.createElement('a');
            link.href = org['Sito web'];
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.className = 'popup-link';
            link.textContent = 'Visita sito web';
            
            link.addEventListener('click', function(e) {
                e.preventDefault();
                window.open(org['Sito web'], '_blank', 'noopener,noreferrer');
            });
            
            linkDiv.appendChild(link);
            popupContent.appendChild(linkDiv);
        }
        
        marker.bindPopup(popupContent);
        marker.orgData = org;
        markers.push(marker);
        markerClusterGroup.addLayer(marker);
    });
    
    filteredMarkers = [...markers];
}

function setupEventListeners() {
    // View toggle listeners
    document.getElementById('map-view-btn').addEventListener('click', () => switchView('map'));
    document.getElementById('table-view-btn').addEventListener('click', () => switchView('table'));
    
    // Filter change listeners
    document.getElementById('tipologia-filter').addEventListener('change', applyFilters);
    document.getElementById('comune-filter').addEventListener('change', applyFilters);
    
    // Search input with debouncing
    let searchTimeout;
    document.getElementById('table-search').addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchTerm = e.target.value.toLowerCase();
            currentPage = 1;
            applyFilters();
        }, 300);
    });
    
    // Clear search button
    document.getElementById('clear-search').addEventListener('click', function() {
        document.getElementById('table-search').value = '';
        searchTerm = '';
        currentPage = 1;
        applyFilters();
    });
    
    // Reset filters button
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    
    // Table sorting
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.column;
            sortTable(column);
        });
    });
    
    // Pagination
    document.getElementById('rows-per-page').addEventListener('change', function(e) {
        rowsPerPage = parseInt(e.target.value);
        currentPage = 1;
        updateTableView();
        updatePagination();
    });
    
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            updateTableView();
            updatePagination();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        const totalPages = Math.ceil(filteredData.length / rowsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            updateTableView();
            updatePagination();
        }
    });
    
    // Export CSV
    document.getElementById('export-csv').addEventListener('click', exportToCSV);
    
    // Fit bounds button
    document.getElementById('fit-bounds').addEventListener('click', fitMapToBounds);
    
    // Modal close listeners
    document.getElementById('close-error-modal').addEventListener('click', () => {
        document.getElementById('error-modal').classList.add('hidden');
    });
    
    document.getElementById('retry-button').addEventListener('click', () => {
        document.getElementById('error-modal').classList.add('hidden');
        location.reload();
    });
    
    // Modal backdrop click to close
    document.getElementById('error-modal').addEventListener('click', function(e) {
        if (e.target === this) {
            this.classList.add('hidden');
        }
    });
}

function switchView(view) {
    const mapView = document.getElementById('map-view');
    const tableView = document.getElementById('table-view');
    const mapBtn = document.getElementById('map-view-btn');
    const tableBtn = document.getElementById('table-view-btn');
    const searchSection = document.getElementById('search-section');
    const exportSection = document.getElementById('export-section');
    
    currentView = view;
    
    if (view === 'map') {
        mapView.classList.remove('hidden');
        tableView.classList.add('hidden');
        mapBtn.classList.add('view-toggle-btn--active');
        tableBtn.classList.remove('view-toggle-btn--active');
        searchSection.classList.add('hidden');
        exportSection.classList.add('hidden');
        
        // Refresh map
        setTimeout(() => {
            if (map) {
                map.invalidateSize();
                fitMapToBounds();
            }
        }, 100);
    } else {
        mapView.classList.add('hidden');
        tableView.classList.remove('hidden');
        mapBtn.classList.remove('view-toggle-btn--active');
        tableBtn.classList.add('view-toggle-btn--active');
        searchSection.classList.remove('hidden');
        exportSection.classList.remove('hidden');
        
        // Refresh table
        updateTableView();
        updatePagination();
    }
}

function applyFilters() {
    const tipologiaFilter = document.getElementById('tipologia-filter').value;
    const comuneFilter = document.getElementById('comune-filter').value;
    
    // Filter data
    filteredData = geocodedData.filter(org => {
        let show = true;
        
        // Apply tipologia filter
        if (tipologiaFilter && org.tipologia !== tipologiaFilter) {
            show = false;
        }
        
        // Apply comune filter
        if (comuneFilter && org.comune !== comuneFilter) {
            show = false;
        }
        
        // Apply search filter
        if (searchTerm) {
            const searchString = `${org.soggetto} ${org.tipologia} ${org.indirizzo_pulito} ${org.comune || ''}`.toLowerCase();
            if (!searchString.includes(searchTerm)) {
                show = false;
            }
        }
        
        return show;
    });
    
    // Update map markers
    markerClusterGroup.clearLayers();
    filteredMarkers = [];
    
    markers.forEach(marker => {
        const org = marker.orgData;
        const isInFiltered = filteredData.some(filteredOrg => 
            filteredOrg.soggetto === org.soggetto && 
            filteredOrg.tipologia === org.tipologia
        );
        
        if (isInFiltered) {
            filteredMarkers.push(marker);
            markerClusterGroup.addLayer(marker);
        }
    });
    
    // Reset pagination
    currentPage = 1;
    
    // Update displays
    updateStatistics();
    if (currentView === 'table') {
        updateTableView();
        updatePagination();
    }
    
    // Fit map to filtered markers if there are any
    if (filteredMarkers.length > 0 && currentView === 'map') {
        setTimeout(() => fitMapToBounds(), 100);
    }
}

function sortTable(column) {
    // Toggle sort direction
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    
    // Sort filtered data
    filteredData.sort((a, b) => {
        let aVal = a[column] || '';
        let bVal = b[column] || '';
        
        // Special handling for comune
        if (column === 'comune') {
            aVal = a.comune || '';
            bVal = b.comune || '';
        }
        
        aVal = aVal.toString().toLowerCase();
        bVal = bVal.toString().toLowerCase();
        
        if (currentSort.direction === 'asc') {
            return aVal.localeCompare(bVal, 'it');
        } else {
            return bVal.localeCompare(aVal, 'it');
        }
    });
    
    // Reset to first page
    currentPage = 1;
    
    // Update sort indicators
    document.querySelectorAll('.sortable').forEach(header => {
        header.classList.remove('sort-asc', 'sort-desc');
    });
    
    const activeHeader = document.querySelector(`[data-column="${column}"]`);
    activeHeader.classList.add(`sort-${currentSort.direction}`);
    
    // Update table
    updateTableView();
    updatePagination();
}

function updateTableView() {
    const tableBody = document.getElementById('table-body');
    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;
    const pageData = filteredData.slice(startIndex, endIndex);
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Add rows
    pageData.forEach(org => {
        const row = document.createElement('tr');
        
        // Nome Organizzazione
        const nameCell = document.createElement('td');
        nameCell.textContent = org.soggetto;
        row.appendChild(nameCell);
        
        // Tipologia
        const tipologiaCell = document.createElement('td');
        const tipologiaBadge = document.createElement('span');
        tipologiaBadge.className = 'tipologia-badge';
        tipologiaBadge.style.backgroundColor = colorMap[org.tipologia];
        tipologiaBadge.textContent = org.tipologia;
        tipologiaCell.appendChild(tipologiaBadge);
        row.appendChild(tipologiaCell);
        
        // Indirizzo
        const addressCell = document.createElement('td');
        addressCell.className = 'address-cell';
        addressCell.textContent = org.indirizzo_pulito;
        addressCell.title = org.indirizzo_pulito; // Tooltip for full address
        row.appendChild(addressCell);
        
        // Comune
        const comuneCell = document.createElement('td');
        comuneCell.textContent = org.comune || '-';
        row.appendChild(comuneCell);
        
        // Sito Web
        const websiteCell = document.createElement('td');
        if (org['Sito web']) {
            const link = document.createElement('a');
            link.href = org['Sito web'];
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.className = 'website-link';
            link.textContent = 'Visita';
            
            link.addEventListener('click', function(e) {
                e.preventDefault();
                window.open(org['Sito web'], '_blank', 'noopener,noreferrer');
            });
            
            websiteCell.appendChild(link);
        } else {
            websiteCell.textContent = '-';
        }
        row.appendChild(websiteCell);
        
        tableBody.appendChild(row);
    });
    
    // Update results count
    document.getElementById('table-results-count').textContent = 
        `${filteredData.length} risultat${filteredData.length === 1 ? 'o' : 'i'}`;
}

function updatePagination() {
    const totalPages = Math.ceil(filteredData.length / rowsPerPage);
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');
    
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages || totalPages === 0;
    
    if (totalPages === 0) {
        pageInfo.textContent = 'Nessun risultato';
    } else {
        pageInfo.textContent = `Pagina ${currentPage} di ${totalPages}`;
    }
}

function exportToCSV() {
    const headers = ['Nome Organizzazione', 'Tipologia', 'Indirizzo', 'Comune', 'Sito Web'];
    const csvContent = [
        headers.join(','),
        ...filteredData.map(org => [
            `"${org.soggetto}"`,
            `"${org.tipologia}"`,
            `"${org.indirizzo_pulito}"`,
            `"${org.comune || ''}"`,
            `"${org['Sito web'] || ''}"`
        ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'organizzazioni_lombardia.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function resetFilters() {
    // Clear filter selections
    document.getElementById('tipologia-filter').value = '';
    document.getElementById('comune-filter').value = '';
    document.getElementById('table-search').value = '';
    
    // Reset search term
    searchTerm = '';
    
    // Reset pagination
    currentPage = 1;
    
    // Reset sort
    currentSort = { column: null, direction: 'asc' };
    document.querySelectorAll('.sortable').forEach(header => {
        header.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Reapply filters (which will show all data)
    applyFilters();
    
    // Fit map bounds
    if (currentView === 'map') {
        fitMapToBounds();
    }
}

function updateStatistics() {
    document.getElementById('total-count').textContent = geocodedData.length;
    document.getElementById('visible-count').textContent = filteredData.length;
}

function fitMapToBounds() {
    if (filteredMarkers.length > 0) {
        const group = new L.featureGroup(filteredMarkers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

function hideLoadingOverlay() {
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.add('hidden');
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-modal').classList.remove('hidden');
}