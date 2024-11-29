let gameState = {
    currentScreen: 'start',
    world: null,
    kingdom: null,
    town: null,
    character: null,
    inventory: {},
    history: [],
    examples: []
};

// Initial Setup and Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Start button listener
    document.getElementById('initialStartBtn').addEventListener('click', () => {
        const startScreen = document.getElementById('startScreen');
        const selectionPhase = document.getElementById('selectionPhase');

        startScreen.classList.add('fade-out');
        setTimeout(() => {
            // Hide start screen and show selection phase
            startScreen.classList.add('hidden');
            selectionPhase.classList.remove('hidden');
            
            // Trigger reflow
            void selectionPhase.offsetWidth;
            
            // Make selection phase visible
            selectionPhase.classList.add('visible');
            
            // Show world selection screen
            gameState.currentScreen = 'worldSelect';
            showScreen('worldSelect');
            startGame();
        }, 300);
    });

    // Back button listener
    document.getElementById('backButton').addEventListener('click', goBack);

    // Submit button click listener
    document.getElementById('submitBtn').addEventListener('click', submitAction);

    // Enter key for input
    document.getElementById('userInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            submitAction();
        }
    });

    // Send button animations
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.addEventListener('mousedown', function() {
        this.style.transform = 'scale(0.95)';
    });

    submitBtn.addEventListener('mouseup', function() {
        this.style.transform = 'scale(1)';
    });

    submitBtn.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
    });
});

// Screen Management Functions
function showScreen(screenId) {
    // Hide all screens first
    document.querySelectorAll('.selection-screen').forEach(screen => {
        screen.classList.remove('visible');
        screen.classList.add('hidden');
    });
    
    // Show selected screen with animation
    const screen = document.getElementById(screenId);
    if (screen) {
        screen.classList.remove('hidden');
        void screen.offsetWidth; // Trigger reflow
        screen.classList.add('visible');
        updateBackButton(screenId);
    }
}

function updateBackButton(currentScreenId) {
    const backButton = document.getElementById('backButton');
    
    // Only show back button after world selection
    if (currentScreenId === 'worldSelect') {
        backButton.classList.add('hidden');
    } else {
        backButton.classList.remove('hidden');
    }
}

function goBack() {
    switch(gameState.currentScreen) {
        case 'kingdomSelect':
            // Go back to world selection
            gameState.currentScreen = 'worldSelect';
            gameState.kingdom = null;
            showScreen('worldSelect');
            startGame(); // Reload world selection
            break;
            
        case 'townSelect':
            // Go back to kingdom selection
            gameState.currentScreen = 'kingdomSelect';
            gameState.town = null;
            showScreen('kingdomSelect');
            displayKingdoms(); // Reload kingdoms
            break;
            
        case 'characterSelect':
            // Go back to town selection
            gameState.currentScreen = 'townSelect';
            gameState.character = null;
            showScreen('townSelect');
            displayTowns(gameState.kingdom);
            break;
    }
}

// Game Initialization Functions
async function startGame() {
    try {
        const response = await fetch('/world-info');
        const data = await response.json();
        displayWorlds(data);
    } catch (error) {
        console.error('Error fetching game data:', error);
    }
}

function displayWorlds(data) {
    const worldList = document.getElementById('worldList');
    worldList.innerHTML = '';
    
    const button = document.createElement('button');
    button.className = 'selection-button';
    button.innerHTML = `
        <h3>${data.name}</h3>
        <p>${data.description.substring(0, 100)}...</p>
    `;
    button.addEventListener('click', () => selectWorld(data.name));
    worldList.appendChild(button);
}

async function selectWorld(worldName) {
    gameState.world = worldName;
    gameState.currentScreen = 'kingdomSelect';
    showScreen('kingdomSelect');
    await displayKingdoms();
}

async function displayKingdoms() {
    try {
        const response = await fetch('/world-info');
        const data = await response.json();
        
        const kingdomList = document.getElementById('kingdomList');
        kingdomList.innerHTML = '';
        
        Object.values(data.kingdoms).forEach(kingdom => {
            const button = document.createElement('button');
            button.className = 'selection-button';
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

function selectKingdom(kingdom) {
    gameState.kingdom = kingdom;
    gameState.currentScreen = 'townSelect';
    showScreen('townSelect');
    displayTowns(kingdom);
}

function displayTowns(kingdom) {
    const townList = document.getElementById('townList');
    townList.innerHTML = '';
    
    Object.values(kingdom.towns).forEach(town => {
        const button = document.createElement('button');
        button.className = 'selection-button';
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
    gameState.currentScreen = 'characterSelect';
    showScreen('characterSelect');
    displayCharacters(town);
}

function displayCharacters(town) {
    const characterList = document.getElementById('characterList');
    characterList.innerHTML = '';
    
    Object.values(town.npcs).forEach(char => {
        const button = document.createElement('button');
        button.className = 'selection-button';
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
        
        // Initialize game with loaded inventory
        await initializeGame(data.inventory);
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}

async function initializeGame(inventory) {
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
        
        // Transition screens
        document.getElementById('selectionPhase').classList.add('fade-out');
        setTimeout(() => {
            document.getElementById('selectionPhase').classList.add('hidden');
            const gameContainer = document.getElementById('gameContainer');
            gameContainer.classList.remove('hidden');
            setTimeout(() => {
                gameContainer.classList.add('visible');
            }, 50);
        }, 300);
        
        // Initialize state
        gameState.history = [];
        updateInventory(inventory);
        document.getElementById('userInput').disabled = false;
        document.getElementById('submitBtn').disabled = false;
        
        // Display initial story
        const story = `Welcome to ${gameState.world}! You are ${gameState.character.name} in ${gameState.town.name}. ${gameState.town.description}`;
        const welcomeMessage = document.createElement('div');
        welcomeMessage.className = 'message bot-message';
        welcomeMessage.textContent = story;
        document.getElementById('gameOutput').appendChild(welcomeMessage);
        
        // Add to history
        gameState.history.push({
            action: 'game_start',
            response: story
        });
        
        // Generate initial examples
        await generateNewExamples(story);
        
        // Focus input
        document.getElementById('userInput').focus();
        
    } catch (error) {
        console.error('Error initializing game:', error);
        const errorMessage = document.createElement('div');
        errorMessage.className = 'message bot-message';
        errorMessage.textContent = 'Failed to initialize game. Please refresh and try again.';
        document.getElementById('gameOutput').appendChild(errorMessage);
    }
 }

// Game Interaction Functions
async function submitAction() {
    const input = document.getElementById('userInput');
    const action = input.value.trim();
    if (!action) return;
    
    input.disabled = true;
    document.getElementById('submitBtn').disabled = true;
    
    const userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.textContent = action;
    document.getElementById('gameOutput').appendChild(userMessage);
    
    try {
        const response = await fetch('/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        
        const result = await response.json();
        
        const botMessage = document.createElement('div');
        botMessage.className = 'message bot-message';
        botMessage.textContent = result.response;
        document.getElementById('gameOutput').appendChild(botMessage);
        
        // Update game state
        updateInventory(result.inventory);
        await generateNewExamples(result.response);
        
        // Update history
        gameState.history.push({
            action: action,
            response: result.response
        });
        
        if (gameState.history.length > 10) {
            gameState.history.shift();
        }
        
        input.value = '';
        const gameOutput = document.getElementById('gameOutput');
        gameOutput.scrollTop = gameOutput.scrollHeight;
        
    } catch (error) {
        console.error('Error:', error);
        
        const errorMessage = document.createElement('div');
        errorMessage.className = 'message bot-message';
        errorMessage.textContent = 'Sorry, something went wrong. Please try again.';
        document.getElementById('gameOutput').appendChild(errorMessage);
    } finally {
        input.disabled = false;
        document.getElementById('submitBtn').disabled = false;
        input.focus();
    }
 }

function updateInventory(inventory) {
    const slots = document.getElementById('inventorySlots');
    slots.innerHTML = '';
    gameState.inventory = inventory;
    
    Object.entries(inventory).forEach(([item, count]) => {
        if (count > 0) {
            const itemElement = document.createElement('div');
            itemElement.className = 'inventory-item';
            itemElement.innerHTML = `
                <span>${item}</span>
                <span class="item-count">${count}</span>
            `;
            slots.appendChild(itemElement);
        }
    });
}

async function generateNewExamples(context) {
    try {
        const response = await fetch('/generate-examples', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                context: context,
                location: gameState.town,
                inventory: gameState.inventory,
                history: gameState.history
            })
        });
        
        const data = await response.json();
        updateExamples(data.examples);
    } catch (error) {
        console.error('Error generating examples:', error);
        updateExamples(['Look around', 'Talk', 'Explore']);
    }
}

function updateExamples(examples) {
    const container = document.getElementById('exampleActions');
    container.innerHTML = '<h4>Possible Actions:</h4>';
    
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