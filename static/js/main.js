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
    // Hide all screens
    document.querySelectorAll('.selection-screen').forEach(screen => {
        screen.classList.remove('visible');
        void screen.offsetWidth; // Trigger reflow
    });
    
    // Show selected screen with animation
    const screen = document.getElementById(screenId);
    if (screen) {
        screen.classList.remove('hidden');
        void screen.offsetWidth; // Trigger reflow
        screen.classList.add('visible');
        updateBackButton();
    }
}

function updateBackButton() {
    const backButton = document.getElementById('backButton');
    const screens = ['characterSelect', 'townSelect', 'kingdomSelect', 'worldSelect'];
    const currentIndex = screens.indexOf(gameState.currentScreen);
    
    if (currentIndex > 0) {
        backButton.classList.remove('hidden');
    } else {
        backButton.classList.add('hidden');
    }
}

function goBack() {
    const screens = ['characterSelect', 'townSelect', 'kingdomSelect', 'worldSelect'];
    const currentIndex = screens.indexOf(gameState.currentScreen);
    
    if (currentIndex > 0) {
        const previousScreen = screens[currentIndex - 1];
        gameState.currentScreen = previousScreen;
        showScreen(previousScreen);
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
    worldList.innerHTML = `
        <button class="selection-button" onclick="selectWorld('${data.name}')">
            <h3>${data.name}</h3>
            <p>${data.description.substring(0, 100)}...</p>
        </button>
    `;
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
        
        // Transition to game screen
        document.getElementById('selectionPhase').classList.add('fade-out');
        setTimeout(() => {
            document.getElementById('selectionPhase').classList.add('hidden');
            const gameContainer = document.getElementById('gameContainer');
            gameContainer.classList.remove('hidden');
            setTimeout(() => {
                gameContainer.classList.add('visible');
            }, 50);
        }, 300);
        
        // Initialize game state
        updateInventory(inventory);
        document.getElementById('userInput').disabled = false;
        document.getElementById('submitBtn').disabled = false;
        
        // Display initial story
        const story = `Welcome to ${gameState.world}! You are ${gameState.character.name} in ${gameState.town.name}, ${gameState.town.description}`;
        updateGameOutput(story);
        
        // Set initial possible actions
        updateExamples([
            'Look around',
            'Talk to locals',
            'Visit the market'
        ]);
    } catch (error) {
        console.error('Error initializing game:', error);
    }
}

// Game Interaction Functions
async function submitAction() {
    const input = document.getElementById('userInput');
    const action = input.value.trim();
    if (!action) return;
    
    // Disable input and button while processing
    input.disabled = true;
    document.getElementById('submitBtn').disabled = true;
    
    // Add user's action to game output
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
        
        // Add game response
        const botMessage = document.createElement('div');
        botMessage.className = 'message bot-message';
        botMessage.textContent = result.response;
        document.getElementById('gameOutput').appendChild(botMessage);
        
        // Update game state
        updateInventory(result.inventory);
        generateNewExamples(result.response);
        
        // Clear input and scroll to bottom
        input.value = '';
        document.getElementById('gameOutput').scrollTop = document.getElementById('gameOutput').scrollHeight;
    } catch (error) {
        console.error('Error:', error);
        
        // Show error message to user
        const errorMessage = document.createElement('div');
        errorMessage.className = 'message bot-message';
        errorMessage.textContent = 'Sorry, something went wrong. Please try again.';
        document.getElementById('gameOutput').appendChild(errorMessage);
    } finally {
        // Re-enable input and button
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

function generateNewExamples(context) {
    let examples = [
        'Explore further',
        'Talk to someone',
        'Use inventory item'
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
    
    // Add inventory-based examples
    Object.keys(gameState.inventory).forEach(item => {
        if (item !== 'gold') {
            examples.push(`Use ${item}`);
        }
    });
    
    // Keep only unique examples and limit to 5
    examples = [...new Set(examples)].slice(0, 5);
    updateExamples(examples);
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