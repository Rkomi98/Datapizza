(function () {
    const tabs = [];
    let scripts = [];
    let activeTab = null;

    const isFileProtocol = window.location.protocol === 'file:';
    const isHttp = window.location.protocol === 'http:' || window.location.protocol === 'https:';
    const isGitHubPages = isHttp && /(^|\.)github\.io$/.test(window.location.hostname);

    function setLoadingState(message) {
        document.getElementById('contentArea').innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⏳</div>
                <h2>${message}</h2>
            </div>
        `;
    }

    function showError(message) {
        if (isFileProtocol) {
            showLocalFolderPrompt(message);
            return;
        }

        document.getElementById('contentArea').innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h2>Errore nel caricamento</h2>
                <p>${message}</p>
                <p>Se preferisci, seleziona manualmente la cartella Scripts.</p>
                <button class="upload-button" onclick="requestLocalScripts()">Seleziona cartella Scripts</button>
            </div>
        `;
    }

    function formatTabTitle(filename) {
        const name = filename.replace(/\.[^/.]+$/, '').replace(/[-_]+/g, ' ');
        return name.replace(/\b\w/g, (char) => char.toUpperCase());
    }

    function joinPath() {
        return Array.from(arguments)
            .filter(Boolean)
            .map((part) => String(part).replace(/^\/+|\/+$/g, ''))
            .join('/');
    }

    function updateTimestamp() {
        const timestamp = document.getElementById('timestamp');
        timestamp.textContent = `Ultimo aggiornamento: ${new Date().toLocaleTimeString('it-IT')}`;
    }

    function initializeTabs() {
        const tabsContainer = document.getElementById('tabsContainer');
        tabsContainer.innerHTML = '';
        tabs.length = 0;

        scripts.forEach((script, index) => {
            const tab = document.createElement('div');
            const tabNumber = String(index + 1).padStart(2, '0');
            const truncatedTitle = script.title.length > 24 ? `${script.title.slice(0, 21)}…` : script.title;

            tab.className = 'tab';
            tab.id = `tab-${index + 1}`;
            tab.title = script.title;
            tab.innerHTML = `
                <span class="tab-number">${tabNumber}</span>
                <span class="tab-title">${truncatedTitle}</span>
            `;
            tab.onclick = () => selectTab(index);

            tabsContainer.appendChild(tab);
            tabs.push(tab);
        });
    }

    function selectTab(index) {
        if (index < 0 || index >= scripts.length) {
            return;
        }

        activeTab = index;

        tabs.forEach((tab, currentIndex) => {
            tab.classList.toggle('active', currentIndex === index);
        });

        showContent(index);
    }

    function showContent(index) {
        const script = scripts[index];
        if (!script) {
            setLoadingState('Seleziona uno script disponibile');
            return;
        }

        const htmlContent = marked.parse(script.content);

        document.getElementById('contentArea').innerHTML = `
            <div class="script-content">
                <div class="upload-text">${script.filename}</div>
                ${htmlContent}
            </div>
        `;
    }

    async function loadMarkdownFilesRelative(filenames) {
        filenames.sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }));
        const loadedScripts = [];

        for (const name of filenames) {
            const response = await fetch(joinPath('Scripts', name));
            if (!response.ok) {
                throw new Error(`Impossibile caricare ${name}`);
            }

            loadedScripts.push({
                filename: name,
                title: formatTabTitle(name),
                content: await response.text(),
            });
        }

        scripts = loadedScripts;
        initializeTabs();

        if (scripts.length > 0) {
            selectTab(0);
            updateTimestamp();
        }
    }

    async function loadFromManifestOrIndex() {
        try {
            const manifestResponse = await fetch('Scripts/index.json', { cache: 'no-cache' });
            if (manifestResponse.ok) {
                const manifest = await manifestResponse.json();
                const names = Array.isArray(manifest)
                    ? manifest
                    : Array.isArray(manifest.files)
                    ? manifest.files
                    : [];
                const files = names
                    .map((entry) => (typeof entry === 'string' ? entry : entry.file || entry.path))
                    .filter(Boolean);

                if (files.length > 0) {
                    await loadMarkdownFilesRelative(files);
                    return;
                }
            }
        } catch (error) {
            console.warn('Manifest non disponibile:', error);
        }

        const response = await fetch('Scripts/');
        if (!response.ok) {
            throw new Error('Nessun indice della cartella Scripts disponibile');
        }

        const directoryHtml = await response.text();
        const parser = new DOMParser();
        const directoryDocument = parser.parseFromString(directoryHtml, 'text/html');
        const links = Array.from(directoryDocument.querySelectorAll('a'))
            .map((link) => link.getAttribute('href'))
            .filter(Boolean)
            .map((href) => href.split('?')[0])
            .filter((href) => href.match(/\.md$/i))
            .map((href) => href.replace(/^.*\//, ''));

        const uniqueFiles = [...new Set(links)];
        if (uniqueFiles.length === 0) {
            throw new Error('Nessun file .md trovato nell\'indice');
        }

        await loadMarkdownFilesRelative(uniqueFiles);
    }

    async function loadFromGitHubAPI() {
        const host = window.location.hostname;
        const segments = window.location.pathname.split('/').filter(Boolean);
        const directorySegments = segments.slice(0, -1);

        let owner = null;
        let repo = null;
        let repoRelativeDir = '';

        if (/github\.io$/.test(host)) {
            owner = host.split('.')[0];
            if (directorySegments.length > 0 && directorySegments[0] !== `${owner}.github.io`) {
                repo = directorySegments[0];
                repoRelativeDir = directorySegments.slice(1).join('/');
            } else {
                repo = `${owner}.github.io`;
                repoRelativeDir = directorySegments.join('/');
            }
        } else {
            throw new Error('Host non GitHub Pages: impossibile usare la GitHub API automaticamente');
        }

        const basePath = repoRelativeDir ? joinPath(repoRelativeDir, 'Scripts') : 'Scripts';
        const candidates = [basePath, joinPath('docs', basePath)];
        const branches = ['gh-pages', 'main', 'master'];

        let listing = null;
        let context = null;

        for (const branch of branches) {
            for (const path of candidates) {
                const url = `https://api.github.com/repos/${owner}/${repo}/contents/${path}?ref=${encodeURIComponent(branch)}`;
                const response = await fetch(url, {
                    headers: { 'Accept': 'application/vnd.github.v3+json' },
                });

                if (!response.ok) {
                    continue;
                }

                const json = await response.json();
                if (Array.isArray(json) && json.length) {
                    const markdownFiles = json.filter(
                        (item) => item.type === 'file' && item.name.match(/\.md$/i)
                    );

                    if (markdownFiles.length) {
                        listing = markdownFiles;
                        context = { branch, path };
                        break;
                    }
                }
            }

            if (listing) {
                break;
            }
        }

        if (!listing) {
            throw new Error('Impossibile elencare i file via GitHub API');
        }

        const loadedScripts = [];
        for (const item of listing) {
            const response = await fetch(item.download_url, { cache: 'no-cache' });
            if (!response.ok) {
                throw new Error(`Impossibile scaricare ${item.name}`);
            }

            loadedScripts.push({
                filename: joinPath(context.path, item.name),
                title: formatTabTitle(item.name),
                content: await response.text(),
            });
        }

        loadedScripts.sort((a, b) =>
            a.filename.localeCompare(b.filename, undefined, { numeric: true, sensitivity: 'base' })
        );

        scripts = loadedScripts;
        initializeTabs();

        if (scripts.length > 0) {
            selectTab(0);
            updateTimestamp();
        }
    }

    let directoryInput = null;

    function ensureDirectoryInput() {
        if (directoryInput) {
            return directoryInput;
        }

        directoryInput = document.createElement('input');
        directoryInput.type = 'file';
        directoryInput.accept = '.md,.markdown';
        directoryInput.multiple = true;
        directoryInput.style.display = 'none';
        directoryInput.setAttribute('webkitdirectory', '');
        directoryInput.setAttribute('directory', '');
        directoryInput.addEventListener('change', handleDirectorySelection);
        document.body.appendChild(directoryInput);

        return directoryInput;
    }

    function requestLocalScripts() {
        const input = ensureDirectoryInput();
        input.value = '';
        input.click();
    }

    async function handleDirectorySelection(event) {
        const files = Array.from(event.target.files || []).filter((file) =>
            file.name.match(/\.(md|markdown)$/i)
        );

        if (!files.length) {
            setLoadingState('Nessun file selezionato');
            return;
        }

        setLoadingState('Caricamento degli script locali...');

        try {
            const loadedScripts = await Promise.all(
                files.map(async (file) => ({
                    filename: file.webkitRelativePath || file.name,
                    title: formatTabTitle(file.name),
                    content: await file.text(),
                }))
            );

            loadedScripts.sort((a, b) =>
                a.filename.localeCompare(b.filename, undefined, { numeric: true, sensitivity: 'base' })
            );

            scripts = loadedScripts;
            initializeTabs();

            if (scripts.length > 0) {
                selectTab(0);
                updateTimestamp();
            }
        } catch (error) {
            console.error(error);
            showLocalFolderPrompt('Impossibile leggere i file selezionati. Riprova.');
        }
    }

    function showLocalFolderPrompt(message) {
        document.getElementById('tabsContainer').innerHTML = '';
        document.getElementById('contentArea').innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📂</div>
                <h2>Carica gli script locali</h2>
                <p>${message || ''}</p>
                <p style="margin-top: 15px;">Seleziona la cartella <strong>Scripts</strong> sul tuo disco.</p>
                <button class="upload-button" onclick="requestLocalScripts()">Seleziona cartella Scripts</button>
            </div>
        `;
    }

    document.addEventListener('DOMContentLoaded', async () => {
        if (typeof marked !== 'undefined') {
            marked.setOptions({ breaks: true });
        }

        try {
            setLoadingState('Cerco script in Scripts/...');

            if (isFileProtocol) {
                showLocalFolderPrompt('Pagina aperta via file://, seleziona la cartella Scripts per continuare.');
                return;
            }

            await loadFromManifestOrIndex();
        } catch (primaryError) {
            try {
                if (isGitHubPages) {
                    setLoadingState('Caricamento da GitHub Pages...');
                    await loadFromGitHubAPI();
                } else {
                    throw primaryError;
                }
            } catch (secondaryError) {
                console.error(primaryError, secondaryError);
                showError(secondaryError.message || 'Caricamento fallito');
            }
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key >= '1' && event.key <= '9' && (event.ctrlKey || event.metaKey)) {
            event.preventDefault();
            selectTab(parseInt(event.key, 10) - 1);
        }
    });

    window.requestLocalScripts = requestLocalScripts;
})();
