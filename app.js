// app.js
// Core logic for the hackathon voting game.

// -- Firebase configuration is now in firebase-config.js --

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.database();

// Criteria definitions with weights (sum to 1.0)
const CRITERIA = [
    { key: 'problemFit', name: 'Problem Fit', weight: 0.30 },
    { key: 'aiLeverage', name: 'AI‑Leverage', weight: 0.25 },
    { key: 'creativity', name: 'Creatività', weight: 0.20 },
    { key: 'execution', name: 'Execution', weight: 0.15 },
    { key: 'pitch', name: 'Pitch', weight: 0.10 }
];

// Application state
const state = {
    role: null,
    roomCode: null,
    teams: [],
    myTeamIndex: null,
    currentTeamIndex: null,
    currentRound: 0,
    timerEnd: 0,
    voterId: null,
    subscriptions: []
};

// Utility to generate a 6‑character alphanumeric code
function generateRoomCode() {
    const chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
    let code = '';
    for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
}

// Utility: show and hide panels
function showPanel(panelId) {
    document.querySelectorAll('.panel').forEach(p => p.classList.add('hidden'));
    document.getElementById(panelId).classList.remove('hidden');
}

// Remove all subscriptions to Firebase listeners when leaving a room
function clearSubscriptions() {
    state.subscriptions.forEach(sub => sub.off());
    state.subscriptions = [];
}

// Host: Add a new team input row
function addTeamInput(name = '') {
    const list = document.getElementById('teamList');
    const wrapper = document.createElement('div');
    wrapper.className = 'team-item';
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Nome squadra';
    input.value = name;
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'remove-team';
    removeBtn.innerHTML = '✕';
    removeBtn.addEventListener('click', () => {
        list.removeChild(wrapper);
    });
    wrapper.appendChild(input);
    wrapper.appendChild(removeBtn);
    list.appendChild(wrapper);
}

// Host: Build team selector buttons
function buildHostTeamSelector() {
    const container = document.getElementById('hostTeamSelector');
    container.innerHTML = '';
    state.teams.forEach((teamName, index) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'secondary';
        btn.textContent = teamName;
        btn.dataset.index = index;
        if (state.currentTeamIndex === index) {
            btn.classList.add('active');
        }
        btn.addEventListener('click', () => {
            if (state.currentTeamIndex === index && state.timerEnd > Date.now()) {
                // Already selected and timer running, ignore changes
                return;
            }
            // Update currentTeam and roundTeam mapping in DB
            db.ref('rooms/' + state.roomCode).transaction(room => {
                if (!room) return room;
                room.currentTeam = index;
                // Record mapping of round -> team index
                if (!room.roundTeams) room.roundTeams = {};
                room.roundTeams[state.currentRound] = index;
                return room;
            });
        });
        container.appendChild(btn);
    });
}

// Host: Update timer display
function updateHostTimer() {
    const display = document.getElementById('timerDisplay');
    if (!state.timerEnd) {
        display.textContent = '03:00';
        return;
    }
    const diff = Math.max(0, state.timerEnd - Date.now());
    const mins = Math.floor(diff / 60000);
    const secs = Math.floor((diff % 60000) / 1000);
    display.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    if (diff <= 0) {
        // Timer expired
        state.timerEnd = 0;
        // Stop timer in DB to avoid others still seeing running
        db.ref('rooms/' + state.roomCode + '/timerEnd').set(0);
    }
}

// Player: Update timer display
function updatePlayerTimer() {
    const display = document.getElementById('playerTimer');
    if (!state.timerEnd) {
        display.textContent = '03:00';
        return;
    }
    const diff = Math.max(0, state.timerEnd - Date.now());
    const mins = Math.floor(diff / 60000);
    const secs = Math.floor((diff % 60000) / 1000);
    display.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    if (diff <= 0) {
        state.timerEnd = 0;
        display.textContent = '00:00';
    }
}

// Host: Load and display room history
function loadHostHistory() {
    const history = JSON.parse(localStorage.getItem('hostHistory')) || [];
    const listEl = document.getElementById('hostRoomList');
    listEl.innerHTML = '<p>Caricamento stanze...</p>';

    if (history.length === 0) {
        listEl.innerHTML = '<p>Nessuna stanza creata finora.</p>';
        return;
    }

    const promises = history.map(code => db.ref('rooms/' + code).once('value'));

    Promise.all(promises).then(snapshots => {
        listEl.innerHTML = '';
        const validHistory = [];
        const twentyFourHoursAgo = Date.now() - (24 * 60 * 60 * 1000);

        snapshots.forEach(snap => {
            const roomData = snap.val();
            if (snap.exists() && roomData.createdAt && roomData.createdAt > twentyFourHoursAgo) {
                const code = snap.key;
                validHistory.push(code);
                const item = document.createElement('div');
                item.className = 'room-list-item';
                item.textContent = `Stanza: ${code}`;
                item.addEventListener('click', () => {
                    state.roomCode = code;
                    showPanel('hostDashboard');
                    subscribeHost();
                });
                listEl.appendChild(item);
            }
        });

        if (listEl.children.length === 0) {
            listEl.innerHTML = '<p>Nessuna stanza attiva trovata.</p>';
        }

        // Clean up localStorage from non-existent rooms
        localStorage.setItem('hostHistory', JSON.stringify(validHistory));
    });
}

// Compute weighted average rating for a vote object
function computeWeightedAverage(ratings) {
    let sum = 0;
    CRITERIA.forEach(c => {
        const val = parseFloat(ratings[c.key]) || 0;
        sum += val * c.weight;
    });
    return sum;
}

// Host & Player: Render live results for a specific round
function renderLiveResults(room, roundToShow) {
    const liveContainer = document.getElementById('liveResults');
    const playerContainer = document.getElementById('playerResults');
    liveContainer.innerHTML = '';
    playerContainer.innerHTML = '';

    // If roundToShow is not provided, use the current round
    const round = roundToShow !== undefined ? roundToShow : room.currentRound;

    // Determine which team is being evaluated
    const teamIndex = room.roundTeams && room.roundTeams[round];
    if (teamIndex === undefined || teamIndex === null) {
        liveContainer.textContent = 'Nessuna valutazione per questo round.';
        playerContainer.textContent = '';
        return;
    }
    const teamName = room.teams[teamIndex];
    // Collect votes for current round
    const roundVotes = room.votes && room.votes[round] ? room.votes[round] : {};
    const voteCount = Object.keys(roundVotes).length;
    // Compute per‑criterion averages
    const averages = {};
    CRITERIA.forEach(c => {
        let total = 0;
        Object.values(roundVotes).forEach(v => {
            total += parseFloat(v[c.key] || 0);
        });
        averages[c.key] = voteCount ? total / voteCount : 0;
    });
    // Render live results: show criteria with animated bars and numeric values
    const title = document.createElement('h3');
    title.textContent = `Risultati Round ${round + 1} – ${teamName}`;
    liveContainer.appendChild(title);
    CRITERIA.forEach(c => {
        const item = document.createElement('div');
        item.className = 'result-row';
        const label = document.createElement('span');
        label.textContent = `${c.name}`;
        const value = document.createElement('span');
        const val = averages[c.key].toFixed(2);
        value.textContent = val;
        const barContainer = document.createElement('div');
        barContainer.className = 'bar-container';
        const bar = document.createElement('div');
        bar.className = 'bar';
        // width based on average (out of 5)
        bar.style.width = `${(averages[c.key] / 5) * 100}%`;
        barContainer.appendChild(bar);
        item.appendChild(label);
        item.appendChild(value);
        item.appendChild(barContainer);
        liveContainer.appendChild(item);
    });
    // Duplicate for player view (simpler)
    const pTitle = document.createElement('h3');
    pTitle.textContent = `Risultati Live`; // intentionally generic
    playerContainer.appendChild(pTitle);
    CRITERIA.forEach(c => {
        const item = document.createElement('div');
        item.className = 'result-row';
        const label = document.createElement('span');
        label.textContent = `${c.name}`;
        const value = document.createElement('span');
        const val = averages[c.key].toFixed(2);
        value.textContent = val;
        const barContainer = document.createElement('div');
        barContainer.className = 'bar-container';
        const bar = document.createElement('div');
        bar.className = 'bar';
        bar.style.width = `${(averages[c.key] / 5) * 100}%`;
        barContainer.appendChild(bar);
        item.appendChild(label);
        item.appendChild(value);
        item.appendChild(barContainer);
        playerContainer.appendChild(item);
    });
}

// Host & Player: Render leaderboard across all rounds
function renderLeaderboard(room) {
    const container = document.getElementById('leaderboard');
    container.innerHTML = '';
    const teamCount = room.teams.length;
    // Aggregate scores per team
    const scores = Array(teamCount).fill(0);
    const counts = Array(teamCount).fill(0);
    const roundTeams = room.roundTeams || {};
    const votes = room.votes || {};
    Object.keys(votes).forEach(roundKey => {
        const teamIndex = roundTeams[roundKey];
        if (teamIndex === undefined || teamIndex === null) return;
        const roundVotes = votes[roundKey];
        Object.values(roundVotes).forEach(vote => {
            scores[teamIndex] += computeWeightedAverage(vote);
            counts[teamIndex] += 1;
        });
    });
    // Compute averages and pair with names
    const leaderboard = room.teams.map((name, idx) => {
        const avg = counts[idx] ? scores[idx] / counts[idx] : 0;
        return { name, avg };
    });
    // Sort descending by avg
    leaderboard.sort((a, b) => b.avg - a.avg);
    // Render rows
    leaderboard.forEach((entry, index) => {
        const row = document.createElement('div');
        row.className = 'leader-row';
        const nameSpan = document.createElement('span');
        // Medal for top 3
        let medal = '';
        if (index === 0) medal = '🥇 ';
        else if (index === 1) medal = '🥈 ';
        else if (index === 2) medal = '🥉 ';
        nameSpan.textContent = `${medal}${entry.name}`;
        const scoreSpan = document.createElement('span');
        scoreSpan.textContent = entry.avg.toFixed(2);
        const barContainer = document.createElement('div');
        barContainer.className = 'bar-container';
        const bar = document.createElement('div');
        bar.className = 'bar';
        bar.style.background = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'peru' : 'var(--primary)';
        bar.style.width = `${(entry.avg / 5) * 100}%`;
        barContainer.appendChild(bar);
        row.appendChild(nameSpan);
        row.appendChild(scoreSpan);
        row.appendChild(barContainer);
        container.appendChild(row);
    });
}

// Build rating form for players
function buildRatingForm() {
    const form = document.getElementById('ratingForm');
    form.innerHTML = '';
    CRITERIA.forEach(c => {
        const item = document.createElement('div');
        item.className = 'rating-item';
        const label = document.createElement('h4');
        label.textContent = `${c.name}`;
        const stars = document.createElement('div');
        stars.className = 'stars';
        // 5 stars
        for (let i = 5; i >= 1; i--) {
            const input = document.createElement('input');
            input.type = 'radio';
            input.name = c.key;
            input.id = `${c.key}-${i}`;
            input.value = i;
            const starLabel = document.createElement('label');
            starLabel.htmlFor = `${c.key}-${i}`;
            starLabel.innerHTML = '&#9733;';
            stars.appendChild(input);
            stars.appendChild(starLabel);
        }
        item.appendChild(label);
        item.appendChild(stars);
        form.appendChild(item);
    });
}

// Read current ratings from form
function readRatings() {
    const ratings = {};
    CRITERIA.forEach(c => {
        const checked = document.querySelector(`input[name="${c.key}"]:checked`);
        if (checked) ratings[c.key] = parseInt(checked.value);
    });
    return ratings;
}

// Determine if player has already voted in current round
function playerHasVoted(room) {
    if (!room.votes) return false;
    const roundVotes = room.votes[state.currentRound];
    if (!roundVotes) return false;
    return !!roundVotes[state.voterId];
}

// Subscribe host to realtime database updates
function subscribeHost() {
    clearSubscriptions();
    const refRoom = db.ref('rooms/' + state.roomCode);
    const sub = refRoom.on('value', snapshot => {
        const data = snapshot.val();
        if (!data) return;
        state.teams = data.teams || [];
        state.currentRound = data.currentRound || 0;
        state.currentTeamIndex = data.currentTeam;
        state.timerEnd = data.timerEnd || 0;

        // Populate round selector
        const roundSelector = document.getElementById('roundSelector');
        const previouslySelected = roundSelector.value;
        roundSelector.innerHTML = '';
        const playedRounds = Object.keys(data.roundTeams || {}).map(Number);
        if (playedRounds.length === 0) {
            // Add current round if no rounds are recorded yet
            playedRounds.push(0);
        }

        playedRounds.sort((a,b) => a-b).forEach(r => {
            const option = document.createElement('option');
            option.value = r;
            option.textContent = `Round ${r + 1}`;
            roundSelector.appendChild(option);
        });
        
        // Restore selection or default to current round
        if (playedRounds.includes(Number(previouslySelected))) {
            roundSelector.value = previouslySelected;
        } else {
            roundSelector.value = state.currentRound;
        }
        
        buildHostTeamSelector();
        // Disable team selector buttons if timer is running
        const timerIsRunning = state.timerEnd && state.timerEnd > Date.now();
        document.querySelectorAll('#hostTeamSelector button').forEach(btn => {
            btn.disabled = timerIsRunning;
        });

        renderLiveResults(data, Number(roundSelector.value));
        renderLeaderboard(data);
        // Update timer controls state
        const startBtn = document.getElementById('timerStartBtn');
        const stopBtn = document.getElementById('timerStopBtn');
        // Start button disabled if no team selected or timer running
        if (state.currentTeamIndex === undefined || state.currentTeamIndex === null) {
            startBtn.disabled = true;
        } else {
            startBtn.disabled = timerIsRunning;
        }
        // Stop button active only if timer running
        stopBtn.disabled = !timerIsRunning;
    });
    state.subscriptions.push({ off: () => refRoom.off('value', sub) });
    // Start timer update interval
    if (!state.hostTimerInterval) {
        state.hostTimerInterval = setInterval(updateHostTimer, 1000);
    }
}

// Subscribe player to realtime database updates
function subscribePlayer() {
    clearSubscriptions();
    const refRoom = db.ref('rooms/' + state.roomCode);
    const sub = refRoom.on('value', snapshot => {
        const data = snapshot.val();
        if (!data) return;
        state.teams = data.teams || [];
        state.currentRound = data.currentRound || 0;
        state.currentTeamIndex = data.currentTeam;
        state.timerEnd = data.timerEnd || 0;
        // Update team name
        const currentNameEl = document.getElementById('currentTeamName');
        if (state.currentTeamIndex === undefined || state.currentTeamIndex === null) {
            currentNameEl.textContent = 'Team in valutazione: --';
        } else {
            currentNameEl.textContent = `Team in valutazione: ${state.teams[state.currentTeamIndex]}`;
        }
        // Update rating form accessibility
        const submitBtn = document.getElementById('submitVoteBtn');
        // Determine if this player can vote: not their own team, timer running, not voted yet
        const timerRunning = state.timerEnd && state.timerEnd > Date.now();
        const isOwnTeam = state.currentTeamIndex === state.myTeamIndex;
        const alreadyVoted = playerHasVoted(data);
        submitBtn.disabled = !(timerRunning && !isOwnTeam && !alreadyVoted);
        // Disable star inputs if cannot vote
        document.querySelectorAll('#ratingForm input').forEach(inp => {
            inp.disabled = submitBtn.disabled;
        });
        // Show message if cannot vote
        if (isOwnTeam && timerRunning) {
            submitBtn.textContent = 'Non puoi votare il tuo team';
        } else if (alreadyVoted) {
            submitBtn.textContent = 'Già votato';
        } else {
            submitBtn.textContent = 'Invia Voto';
        }
        // For players, always show live results of the CURRENT round
        renderLiveResults(data, data.currentRound);
        renderLeaderboard(data);
    });
    state.subscriptions.push({ off: () => refRoom.off('value', sub) });
    // Start timer update interval
    if (!state.playerTimerInterval) {
        state.playerTimerInterval = setInterval(updatePlayerTimer, 1000);
    }
}

// Document ready
document.addEventListener('DOMContentLoaded', () => {
    // Landing choice buttons
    document.getElementById('hostChoice').addEventListener('click', () => {
        state.role = 'host';
        showPanel('hostLogin');
    });
    document.getElementById('playerChoice').addEventListener('click', () => {
        state.role = 'player';
        showPanel('playerJoin');
    });
    // Back buttons
    document.getElementById('backToLanding1').addEventListener('click', () => {
        showPanel('landing');
    });
    document.getElementById('backToLanding2').addEventListener('click', () => {
        showPanel('landing');
    });
    document.getElementById('backToLanding3').addEventListener('click', () => {
        showPanel('landing');
    });
    document.getElementById('hubBackToLanding').addEventListener('click', () => {
        showPanel('landing');
    });
    // Host login
    document.getElementById('hostLoginBtn').addEventListener('click', () => {
        const pwd = document.getElementById('hostPassword').value;
        if (pwd === 'D4t4p1zz4') {
            showPanel('hostHub');
            loadHostHistory();
        } else {
            alert('Password errata');
        }
    });

    // Host Hub: Go to create room
    document.getElementById('goToCreateRoomBtn').addEventListener('click', () => {
        showPanel('hostSetup');
    });

    // Add team button
    document.getElementById('addTeamBtn').addEventListener('click', () => {
        addTeamInput();
    });
    // Create room button
    document.getElementById('createRoomBtn').addEventListener('click', () => {
        const list = document.querySelectorAll('#teamList input');
        const names = Array.from(list).map(i => i.value.trim()).filter(n => n);
        if (names.length < 2) {
            alert('Inserisci almeno due squadre');
            return;
        }
        const code = generateRoomCode();
        state.roomCode = code;
        state.teams = names;
        state.currentRound = 0;
        state.currentTeamIndex = null;
        state.timerEnd = 0;
        // Write room data to Firebase
        db.ref('rooms/' + code).set({
            teams: names,
            currentRound: 0,
            currentTeam: null,
            timerEnd: 0,
            roundTeams: {},
            votes: {},
            createdAt: firebase.database.ServerValue.TIMESTAMP // Add creation timestamp
        }).then(() => {
            // Save room code to host's history in localStorage
            let history = JSON.parse(localStorage.getItem('hostHistory')) || [];
            if (!history.includes(code)) {
                history.push(code);
                localStorage.setItem('hostHistory', JSON.stringify(history));
            }
            // Show dashboard and subscribe
            document.getElementById('roomCodeDisplay').textContent = code;
            showPanel('hostDashboard');
            subscribeHost();
        }).catch(err => {
            console.error('Errore durante la creazione della stanza', err);
            alert('Errore durante la creazione della stanza');
        });
    });
    // Host: Timer controls
    document.getElementById('timerStartBtn').addEventListener('click', () => {
        if (state.currentTeamIndex === undefined || state.currentTeamIndex === null) {
            alert('Seleziona prima un team da valutare');
            return;
        }
        const end = Date.now() + 3 * 60 * 1000;
        db.ref('rooms/' + state.roomCode).update({ timerEnd: end });
    });
    document.getElementById('timerStopBtn').addEventListener('click', () => {
        db.ref('rooms/' + state.roomCode).update({ timerEnd: 0 });
    });
    // Host: Previous round button
    document.getElementById('prevRoundBtn').addEventListener('click', () => {
        db.ref('rooms/' + state.roomCode).transaction(room => {
            if (!room) return room;
            // Ensure round doesn't go below 0
            room.currentRound = Math.max(0, (room.currentRound || 0) - 1);
            room.currentTeam = null;
            room.timerEnd = 0;
            return room;
        });
    });
    // Host: Next round button
    document.getElementById('nextRoundBtn').addEventListener('click', () => {
        db.ref('rooms/' + state.roomCode).transaction(room => {
            if (!room) return room;
            room.currentRound = (room.currentRound || 0) + 1;
            room.currentTeam = null;
            room.timerEnd = 0;
            return room;
        });
    });
    // Tab navigation for host
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const target = tab.getAttribute('data-tab');
            document.getElementById('liveResults').classList.toggle('hidden', target !== 'live');
            document.getElementById('leaderboard').classList.toggle('hidden', target !== 'leaderboard');
            // Also hide/show round selector with the live results tab
            document.getElementById('roundSelectorContainer').classList.toggle('hidden', target !== 'live');
        });
    });

    // Host: Round selector change
    document.getElementById('roundSelector').addEventListener('change', (e) => {
        const selectedRound = Number(e.target.value);
        // We need the latest room data to render old rounds
        db.ref('rooms/' + state.roomCode).once('value').then(snapshot => {
            if (snapshot.exists()) {
                renderLiveResults(snapshot.val(), selectedRound);
            }
        });
    });

    // Player: join room
    document.getElementById('joinRoomBtn').addEventListener('click', () => {
        const code = document.getElementById('joinRoomCode').value.trim().toUpperCase();
        if (!code) {
            alert('Inserisci un codice stanza');
            return;
        }
        // Check if room exists
        db.ref('rooms/' + code).once('value').then(snap => {
            if (snap.exists()) {
                state.roomCode = code;
                // Retrieve team names
                state.teams = snap.val().teams || [];
                // Move to team selection
                const teamListEl = document.getElementById('playerTeamList');
                teamListEl.innerHTML = '';
                state.teams.forEach((name, index) => {
                    const label = document.createElement('label');
                    label.style.display = 'block';
                    const radio = document.createElement('input');
                    radio.type = 'radio';
                    radio.name = 'playerTeam';
                    radio.value = index;
                    label.appendChild(radio);
                    label.appendChild(document.createTextNode(name));
                    teamListEl.appendChild(label);
                });
                showPanel('playerTeamSelect');
            } else {
                alert('Stanza non trovata');
            }
        });
    });
    // Player: confirm team selection
    document.getElementById('confirmTeamBtn').addEventListener('click', () => {
        const selected = document.querySelector('input[name="playerTeam"]:checked');
        if (!selected) {
            alert('Seleziona un team');
            return;
        }
        state.myTeamIndex = parseInt(selected.value);
        // Generate or retrieve voterId from localStorage so the same user uses the same id for the same room
        const key = `voterId_${state.roomCode}`;
        let voterId = localStorage.getItem(key);
        if (!voterId) {
            voterId = Math.random().toString(36).substr(2, 9);
            localStorage.setItem(key, voterId);
        }
        state.voterId = voterId;
        // Build rating form
        buildRatingForm();
        // Reset timer display for players
        document.getElementById('playerTimer').textContent = '03:00';
        showPanel('playerVoting');
        subscribePlayer();
    });
    // Player: submit vote
    document.getElementById('submitVoteBtn').addEventListener('click', () => {
        const ratings = readRatings();
        // Ensure all criteria selected
        const allSelected = CRITERIA.every(c => ratings[c.key]);
        if (!allSelected) {
            alert('Compila tutte le valutazioni');
            return;
        }
        // Write vote
        const votePath = `rooms/${state.roomCode}/votes/${state.currentRound}/${state.voterId}`;
        db.ref(votePath).set(ratings).then(() => {
            // After successful vote, disable button
            document.getElementById('submitVoteBtn').disabled = true;
            document.getElementById('submitVoteBtn').textContent = 'Già votato';
        });
    });
});