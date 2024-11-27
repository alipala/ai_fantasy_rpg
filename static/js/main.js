let gameState = {
    started: false,
    phase: 'initial',
    character: null,
    world: null,
    kingdom: null,
    town: null,
    inventory: {},
    history: [],
    examples: []
};

async function startGame() {
    if (gameState.started) return;
    
    gameState.started = true;
    gameState.phase = 'world'; // Changed from 'character' to 'world'
    
    document.getElementById('startGameBtn').disabled = true;
    document.getElementById('selectionPhase').classList.remove('hidden');
    document.getElementById('worldSelect').classList.remove('hidden');
    
    try {
        const response = await fetch('/world-info');
        const data = await response.json();
        displayWorlds(data);
        updateExamples([
            'Select a world to begin',
            'Learn about Kyropeia',
            'Read world descriptions'
        ]);
    } catch (error) {
        console.error('Error fetching game data:', error);
        updateGameOutput('Error starting game. Please try again.');
    }
}

function displayWorlds(data) {
    const worldList = document.getElementById('worldList');
    worldList.innerHTML = `
        <button class="floating-button" onclick="selectWorld('${data.name}')">
            <h3>${data.name}</h3>
            <p>${data.description.substring(0, 100)}...</p>
        </button>
    `;
}

function selectWorld(worldName) {
    gameState.world = worldName;
    gameState.phase = 'kingdom';
    
    document.getElementById('worldSelect').classList.add('hidden');
    document.getElementById('kingdomSelect').classList.remove('hidden');
    
    displayKingdoms();
    updateExamples([
        'Choose a kingdom',
        'Read kingdom histories',
        'Compare kingdoms'
    ]);
}

async function displayKingdoms() {
    try {
        const response = await fetch('/world-info');
        const data = await response.json();
        
        const kingdomList = document.getElementById('kingdomList');
        kingdomList.innerHTML = '';
        
        Object.values(data.kingdoms).forEach(kingdom => {
            const button = document.createElement('button');
            button.className = 'floating-button';
            button.innerHTML = `
                <h3>${kingdom.name}</h3>
                <p>${kingdom.description.substring(0, 100)}...</p>
            `;
            button.onclick = () => selectKingdom(kingdom);
            kingdomList.appendChild(button);
        });
    } catch (error) {
        console.error('Error fetching kingdoms:', error);
    }
}

async function selectKingdom(kingdom) {
    gameState.kingdom = kingdom;
    gameState.phase = 'town';
    
    displayTowns(kingdom);
    updateExamples([
        'Choose a town',
        'Read town descriptions',
        'Learn about locations'
    ]);
}

function displayTowns(kingdom) {
    const townList = document.getElementById('townList');
    townList.innerHTML = '';
    document.getElementById('kingdomSelect').classList.add('hidden');
    document.getElementById('townSelect').classList.remove('hidden');
    
    Object.values(kingdom.towns).forEach(town => {
        const button = document.createElement('button');
        button.className = 'floating-button';
        button.innerHTML = `
            <h3>${town.name}</h3>
            <p>${town.description.substring(0, 100)}...</p>
        `;
        button.onclick = () => selectTown(town);
        townList.appendChild(button);
    });
}

function selectTown(town) {
    gameState.town = town;
    gameState.phase = 'character';
    
    displayCharacters(town);
    updateExamples([
        'Choose a character',
        'Read character stories',
        'Learn about NPCs'
    ]);
}

function displayCharacters(town) {
    const characterList = document.getElementById('characterList');
    characterList.innerHTML = '';
    document.getElementById('townSelect').classList.add('hidden');
    document.getElementById('characterSelect').classList.remove('hidden');
    
    Object.values(town.npcs).forEach(char => {
        const button = document.createElement('button');
        button.className = 'floating-button';
        button.innerHTML = `
            <h3>${char.name}</h3>
            <p>${char.description.substring(0, 100)}...</p>
        `;
        button.onclick = () => selectCharacter(char);
        characterList.appendChild(button);
    });
}

async function selectCharacter(character) {
    gameState.character = character;
    
    try {
        const response = await fetch('/load-inventory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ character: character.name })
        });
        const data = await response.json();
        updateInventory(data.inventory);
        
        document.getElementById('characterSelect').classList.add('hidden');
        await initializeGame();
        
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}

async function initializeGame() {
    try {
        const response = await fetch('/start-game', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                character: gameState.character.name,
                world: gameState.world,
                kingdom: gameState.kingdom.name
            })
        });
        
        const data = await response.json();
        updateInventory(data.inventory);
        
        document.getElementById('selectionPhase').classList.add('hidden');
        document.getElementById('userInput').disabled = false;
        document.querySelectorAll('.button-group button').forEach(button => {
            if (button.id !== 'startGameBtn') {
                button.disabled = false;
            }
        });
        
        const story = `Welcome to ${gameState.world}! You are ${gameState.character.name} in ${gameState.town.name}, ${gameState.town.description}`;
        updateGameOutput(story);
        
        updateExamples([
            'Look around',
            'Talk to locals',
            'Visit the market'
        ]);
    } catch (error) {
        console.error('Error initializing game:', error);
    }
}

function updateInventory(inventory) {
    const slots = document.getElementById('inventorySlots');
    slots.innerHTML = '';
    gameState.inventory = inventory;
    
    Object.entries(inventory).forEach(([item, count]) => {
        if (count > 0) {  // Only show items with count > 0
            const itemElement = createInventoryItem(item, count);
            slots.appendChild(itemElement);
        }
    });
}

function createInventoryItem(item, count) {
    const div = document.createElement('div');
    div.className = 'inventory-item';
    div.draggable = true;
    div.innerHTML = `
        <span>${item}</span>
        <span class="item-count">${count}</span>
    `;
    
    div.addEventListener('dragstart', handleDragStart);
    div.addEventListener('dragend', handleDragEnd);
    return div;
}

function handleDragStart(e) {
    e.target.classList.add('dragging');
    document.getElementById('dropZone').classList.add('active');
    e.dataTransfer.setData('text/plain', e.target.querySelector('span').textContent);
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
    document.getElementById('dropZone').classList.remove('active');
}

async function submitAction() {
    const input = document.getElementById('userInput');
    const action = input.value;
    if (!action.trim()) return;
    
    // Add user's action to game output
    const output = document.getElementById('gameOutput');
    const userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.textContent = action;
    output.appendChild(userMessage);
    
    try {
        const response = await fetch('/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        
        const result = await response.json();
        
        // Add game response
        const botMessage = document.createElement('div');
        botMessage.className = 'message bot-message';
        botMessage.textContent = result.response;
        output.appendChild(botMessage);
        
        updateInventory(result.inventory);
        generateNewExamples(result.response);
        
        // Clear input
        input.value = '';
        
        // Scroll to bottom
        output.scrollTop = output.scrollHeight;
    } catch (error) {
        console.error('Error:', error);
    }
}

function generateNewExamples(context) {
    let examples = [
        'Explore further',
        'Talk to someone',
        'Check inventory'
    ];
    
    // Add context-specific examples
    if (context.toLowerCase().includes('merchant') || context.toLowerCase().includes('market')) {
        examples = [
            'Buy items',
            'Check prices',
            'Negotiate'
        ];
    } else if (context.toLowerCase().includes('npc') || context.toLowerCase().includes('person')) {
        examples = [
            'Ask questions',
            'Learn more',
            'Request help'
        ];
    }
    
    updateExamples(examples);
}

function updateExamples(examples) {
    const container = document.getElementById('exampleActions');
    container.innerHTML = '';
    
    examples.forEach(example => {
        const button = document.createElement('button');
        button.className = 'example-button';
        button.textContent = example;
        button.onclick = () => useExample(example);
        container.appendChild(button);
    });
}

function useExample(example) {
    const input = document.getElementById('userInput');
    input.value = example;
}

function updateGameOutput(text) {
    const output = document.getElementById('gameOutput');
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot-message';
    messageElement.textContent = text;
    output.appendChild(messageElement);
    output.scrollTop = output.scrollHeight;
}

function retryAction() {
    if (gameState.history.length > 0) {
        const lastAction = gameState.history[gameState.history.length - 1].action;
        const input = document.getElementById('userInput');
        input.value = lastAction;
        submitAction();
    }
}

function undoAction() {
    if (gameState.history.length > 0) {
        gameState.history.pop();
        const output = document.getElementById('gameOutput');
        output.removeChild(output.lastElementChild);
        output.removeChild(output.lastElementChild);
        
        if (gameState.history.length > 0) {
            const lastState = gameState.history[gameState.history.length - 1];
            updateInventory(lastState.inventory);
        }
    }
}

function clearChat() {
    document.getElementById('gameOutput').innerHTML = '';
    gameState.history = [];
    updateInventory(gameState.inventory);
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('userInput');
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        const item = e.dataTransfer.getData('text/plain');
        dropZone.value = `Use ${item}`;
        submitAction();
    });
});