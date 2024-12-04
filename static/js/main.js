
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

// Triangle SVG template
const triangleSvg = `
  <svg class="triangle-svg" viewBox="0 0 140 141">
    <g stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
      <polygon class="triangle-polygon" points="70 6 136 138 4 138"></polygon>
    </g>
  </svg>
`;

// Initialize triangles when document loads
document.addEventListener('DOMContentLoaded', () => {
    const triangles = document.querySelectorAll('.triangle');
    triangles.forEach(triangle => {
        triangle.innerHTML = triangleSvg;
    });
});

// Initial Setup and Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('initialStartBtn');
    startBtn.addEventListener('click', handleStartClick);

    // Back button listener
    document.getElementById('backButton').addEventListener('click', handleBackNavigation);

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

function createPuzzleProgress() {
    const progressDiv = document.createElement('div');
    progressDiv.className = 'quest-progress-content';
    progressDiv.innerHTML = '<div class="progress-steps"></div>';
    return progressDiv;
}

function handleStartClick() {
    const startScreen = document.getElementById('startScreen');
    const selectionPhase = document.getElementById('selectionPhase');
    const gameBackground = document.getElementById('gameBackground');
 
    startScreen.classList.add('fade-out');
    gameBackground.style.opacity = '1';
    gameBackground.style.visibility = 'visible';
 
    setTimeout(() => {
        startScreen.classList.add('hidden');
        selectionPhase.classList.remove('hidden');
        
        void selectionPhase.offsetWidth;
        selectionPhase.classList.add('visible');
        
        gameState.currentScreen = 'worldSelect';
        showScreen('worldSelect');
        startGame();
    }, 300);
 }

// Screen Management Functions
function showScreen(screenId) {
    document.querySelectorAll('.selection-screen').forEach(screen => {
        screen.classList.remove('visible');
        screen.classList.add('hidden');
    });
    
    const screen = document.getElementById(screenId);
    if (screen) {
        screen.classList.remove('hidden');
        void screen.offsetWidth;
        screen.classList.add('visible');
        updateBackButton(screenId);
    }
}

function updateBackButton(currentScreenId) {
    const backButton = document.getElementById('backButton');
    if (currentScreenId === 'worldSelect') {
        backButton.classList.add('hidden');
    } else {
        backButton.classList.remove('hidden');
    }
}

function handleBackNavigation() {
    switch(gameState.currentScreen) {
        case 'kingdomSelect':
            gameState.currentScreen = 'worldSelect';
            gameState.kingdom = null;
            showScreen('worldSelect');
            startGame();
            break;
            
        case 'townSelect':
            gameState.currentScreen = 'kingdomSelect';
            gameState.town = null;
            showScreen('kingdomSelect');
            displayKingdoms(gameState.world.kingdoms);
            break;
            
        case 'characterSelect':
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
        console.error('Error starting game:', error);
        showError('Failed to load game worlds. Please refresh and try again.');
    }
}

function displayWorlds(data) {
    const worldList = document.getElementById('worldList');
    worldList.innerHTML = '';
    
    if (data && data.worlds) {
        Object.values(data.worlds).forEach(world => {
            const button = document.createElement('button');
            button.className = 'selection-button';
            button.innerHTML = `
                <h3>${world.name}</h3>
                <p>${world.description ? world.description.substring(0, 100) : ''}...</p>
            `;
            button.addEventListener('click', () => selectWorld(world));
            worldList.appendChild(button);
        });
    } else {
        showError('Error loading worlds');
    }
}

function selectWorld(world) {
    gameState.world = world;
    gameState.currentScreen = 'kingdomSelect';
    showScreen('kingdomSelect');
    displayKingdoms(world.kingdoms);
}

function displayKingdoms(kingdoms) {
    const kingdomList = document.getElementById('kingdomList');
    kingdomList.innerHTML = '';
    
    Object.values(kingdoms).forEach(kingdom => {
        const button = document.createElement('button');
        button.className = 'selection-button';
        button.innerHTML = `
            <h3>${kingdom.name}</h3>
            <p>${kingdom.description.substring(0, 100)}...</p>
        `;
        button.onclick = () => selectKingdom(kingdom);
        kingdomList.appendChild(button);
    });
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
        showLoadingOverlay();
        
        const response = await fetch('/load-inventory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ character: character.name })
        });
        const data = await response.json();
        
        if (data.inventory) {
            await initializeGame(data.inventory);
        } else {
            throw new Error('Failed to load character inventory');
        }
    } catch (error) {
        console.error('Error loading inventory:', error);
        showError('Failed to load character inventory');
    } finally {
        hideLoadingOverlay();
    }
}

function showLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('hidden');
    requestAnimationFrame(() => {
        overlay.classList.add('visible');
    });
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('visible');
    setTimeout(() => {
        overlay.classList.add('hidden');
    }, 300);
}

async function initializeGame(inventory) {
    try {
        const response = await fetch('/start-game', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                character: gameState.character.name,
                world: gameState.world.name,
                kingdom: gameState.kingdom.name
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Transition screens
        hideLoadingOverlay();
        transitionToGameScreen();
        
        // Initialize puzzle progress if available in response
        const puzzleProgressContainer = document.querySelector('.puzzle-progress-container');
        if (puzzleProgressContainer && data.puzzle_progress) {
            puzzleProgressContainer.appendChild(createPuzzleProgress());
            updatePuzzleProgress(data.puzzle_progress);
        }
        
        // Initialize game state
        setupInitialGameState(inventory);
        
        // Display initial story and image
        displayInitialStory(data);
        
        // Generate initial examples
        await generateNewExamples(data.message);
        
        // Focus input
        document.getElementById('userInput').focus();

        console.log('Game data received:', data);
        const gameBackground = document.getElementById('gameBackground');
        gameBackground.classList.add('fade-out');
        setTimeout(() => gameBackground.style.display = 'none', 500);
        console.log('Puzzle progress:', data.puzzle_progress);
        
    } catch (error) {
        console.error('Error initializing game:', error);
        showError('Failed to initialize game');
        hideLoadingOverlay();
    }
}

function transitionToGameScreen() {
    document.getElementById('selectionPhase').classList.add('fade-out');
    setTimeout(() => {
        document.getElementById('selectionPhase').classList.add('hidden');
        const gameContainer = document.getElementById('gameContainer');
        gameContainer.classList.remove('hidden');
        setTimeout(() => {
            gameContainer.classList.add('visible');
        }, 50);
    }, 300);
}

function setupInitialGameState(inventory) {
    gameState.history = [];
    updateInventory(inventory);
    document.getElementById('userInput').disabled = false;
    document.getElementById('submitBtn').disabled = false;
}

function displayInitialStory(data) {
    const story = `Welcome to ${gameState.world.name}! You are ${gameState.character.name} in ${data.location.name}. ${data.location.description}`;
    
    // Display story message
    const welcomeMessage = document.createElement('div');
    welcomeMessage.className = 'message bot-message';
    welcomeMessage.textContent = story;
    document.getElementById('gameOutput').appendChild(welcomeMessage);
    
    // Handle initial story image
    if (data.initial_image) {
        displayStoryImage(data.initial_image);
    }
    
    // Add to history
    gameState.history.push({
        action: 'game_start',
        response: story
    });
}

function displayStoryImage(imageData) {
    // Create container for image loading state
    const container = document.getElementById('storyImageContainer');
    container.innerHTML = '<div class="image-loading"></div>';
    
    // Create image element
    const img = new Image();
    img.src = imageData.url;
    
    img.onload = () => {
        container.innerHTML = `
            <div class="story-image-wrapper">
                <img src="${imageData.url}" 
                     alt="Scene from ${imageData.context?.world || 'the story'}" 
                     class="story-image"
                />
                <div class="story-image-caption">
                    ${imageData.context?.character || ''} in ${imageData.context?.location || ''}
                </div>
            </div>
        `;
    };
    
    img.onerror = () => {
        container.innerHTML = ''; // Remove loading state if image fails
    };
}

async function submitAction() {
    const input = document.getElementById('userInput');
    const action = input.value.trim();
    if (!action) return;
    
    // Disable input during processing
    disableGameControls(true);
    
    // Display user message
    displayUserMessage(action);
    
    try {
        const response = await fetch('/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        
        const result = await response.json();
        
        if (result.error) {
            showError(result.error);
            return;
        }
        
        // Display bot response
        displayBotMessage(result);
        
        // Update game state
        updateGameState(action, result);

        // Update puzzle progress
        if (result.puzzle_progress) {
            updatePuzzleProgress(result.puzzle_progress);
        }
        
        // Handle puzzle completion with completion image
        if (result.puzzle_solved) {
            handlePuzzleCompletion(result);
        }

        // Clear input
        input.value = '';
        
        // Scroll to bottom
        scrollToBottom();
        
    } catch (error) {
        console.error('Error:', error);
        showError('Sorry, something went wrong. Please try again.');
    } finally {
        disableGameControls(false);
        input.focus();
    }
}

function fadeOutGameContainer() {
    const gameContainer = document.getElementById('gameContainer');
    gameContainer.style.opacity = '0';
    gameContainer.style.transition = 'opacity 0.3s ease';
    setTimeout(() => {
        gameContainer.style.display = 'none';
    }, 300);
}

function handlePuzzleCompletion(result) {
    // First fade out the game container
    fadeOutGameContainer();

    // Create and show loading overlay
    const overlay = document.createElement('div');
    overlay.className = 'completion-overlay';
    
    // Show loading state
    const loadingContent = `
        <div class="completion-content">
            <div class="completion-header">
                <h2>Victory in ${result.world.name}!</h2>
                <p class="completion-subtitle">The realm has been saved by ${result.character.name}</p>
            </div>
            <div class="victory-loading-container">
                <div class="loading-spinner"></div>
                <p class="loading-text">Creating your legendary victory scene...</p>
            </div>
        </div>
    `;
    
    overlay.innerHTML = loadingContent;
    document.body.appendChild(overlay);
    
    // Show the overlay with a slight delay to ensure smooth animation
    setTimeout(() => {
        overlay.classList.add('visible');
        
        // Handle image loading if available
        if (result.completion_image) {
            const img = new Image();
            img.onload = () => {
                // Prepare the final content
                const completionContent = `
                    <div class="completion-content">
                        <div class="completion-header">
                            <h2>Victory in ${result.world.name}!</h2>
                            <p class="completion-subtitle">The realm has been saved by ${result.character.name}</p>
                        </div>
                        <div class="completion-image-container">
                            <img src="${result.completion_image.url}" 
                                 alt="Victory scene in ${result.completion_image.context.world}"
                                 class="completion-image"
                            />
                            <div class="completion-image-caption">
                                <h3>The Legend of ${result.completion_image.context.character}</h3>
                                <p>Savior of ${result.completion_image.context.world}</p>
                                <div class="achievement-badges">
                                    ${result.completion_image.context.achievements.map(achievement => 
                                        `<span class="achievement-badge">${achievement}</span>`
                                    ).join('')}
                                </div>
                            </div>
                        </div>
                        <div class="completion-summary">
                            <p>${result.response}</p>
                        </div>
                        <div class="completion-actions">
                            <button onclick="location.reload()" class="completion-button replay-button">
                                <svg xmlns="http://www.w3.org/2000/svg" class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <path d="M3 12a9 9 0 1 1 9 9 9 9 0 0 1-9-9z"/>
                                    <path d="M12 7v5l4 2"/>
                                </svg>
                                Play Again
                            </button>
                            <button onclick="shareStory()" class="completion-button share-button">
                                <svg xmlns="http://www.w3.org/2000/svg" class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
                                    <polyline points="16 6 12 2 8 6"/>
                                    <line x1="12" y1="2" x2="12" y2="15"/>
                                </svg>
                                Share Story
                            </button>
                        </div>
                    </div>`;

                // Add transition class
                overlay.classList.add('transitioning');
                
                // Update content after a short delay
                setTimeout(() => {
                    overlay.innerHTML = completionContent;
                    overlay.classList.remove('transitioning');
                }, 300);
            };
            
            // Start loading the image
            img.src = result.completion_image.url;
        } else {
            // If no image, show completion without loading state
            overlay.classList.add('transitioning');
            setTimeout(() => {
                overlay.innerHTML = `
                    <div class="completion-content">
                        <h2>Victory in ${result.world.name}!</h2>
                        <p>${result.response}</p>
                        <div class="completion-actions">
                            <button onclick="location.reload()" class="completion-button replay-button">Play Again</button>
                            <button onclick="shareStory()" class="completion-button share-button">Share Story</button>
                        </div>
                    </div>`;
                overlay.classList.remove('transitioning');
            }, 300);
        }
    }, 100);
}

// Add share functionality
function shareStory() {
    const shareData = {
        title: `Victory in ${gameState.world.name}`,
        text: `I just completed my quest as ${gameState.character.name} and saved ${gameState.world.name} from destruction!`,
        url: window.location.href
    };
    
    if (navigator.share) {
        navigator.share(shareData)
            .catch((err) => console.error('Error sharing:', err));
    } else {
        // Fallback for browsers that don't support sharing
        const shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareData.text)}&url=${encodeURIComponent(shareData.url)}`;
        window.open(shareUrl, '_blank');
    }
}

function disableGameControls(disabled) {
    document.getElementById('userInput').disabled = disabled;
    document.getElementById('submitBtn').disabled = disabled;
}

function displayUserMessage(action) {
    const userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.textContent = action;
    document.getElementById('gameOutput').appendChild(userMessage);
}

function displayBotMessage(result) {
    const botMessage = document.createElement('div');
    botMessage.className = 'message bot-message';
    botMessage.textContent = result.response;
    document.getElementById('gameOutput').appendChild(botMessage);
    
    // Handle response image if present
    if (result.image) {
        displayStoryImage(result.image);
    }
}

async function updateGameState(action, result) {
    updateInventory(result.inventory);
    await generateNewExamples(result.response);
    
    gameState.history.push({
        action: action,
        response: result.response
    });
    
    if (gameState.history.length > 10) {
        gameState.history.shift();
    }
}

function createInventoryItem(item, count) {
    return `
        <div class="inventory-item relative p-2 bg-gradient-to-r from-gray-800 to-gray-700 rounded-lg border border-gray-600">
            <div class="flex justify-between items-center">
                <div class="flex flex-col flex-1">
                    <span class="text-white">${item}</span>
                    <div class="tooltip-text">${getItemTooltip(item)}</div>
                </div>
            </div>
            <div class="item-count absolute -top-2 -right-2 w-6 h-6 flex items-center justify-center bg-gradient-to-r from-red-500 to-red-600 rounded-full text-white text-xs font-medium shadow-lg">
                ${count}
            </div>
        </div>
    `;
}

function updateInventory(inventory) {
    const slots = document.getElementById('inventorySlots');
    slots.innerHTML = '';
    
    Object.entries(inventory).forEach(([item, count]) => {
        if (count > 0) {
            slots.innerHTML += createInventoryItem(item, count);
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
    container.innerHTML = '<h4>Possible Actions</h4>';
    
    examples.forEach(example => {
        const button = document.createElement('button');
        button.className = 'example-button';
        button.textContent = example;
        button.onclick = () => useExample(example);
        container.appendChild(button);
    });
}

function updatePuzzleProgress(puzzleData) {
    if (!puzzleData) return;
    
    const progressContainer = document.getElementById('puzzleProgress');
    if (!progressContainer) return;

    const percentage = (puzzleData.completed_tasks / puzzleData.total_tasks) * 100;
    
    progressContainer.innerHTML = `
        <div class="quest-progress-content">
            <h2>Quest Progress</h2>
            <p class="puzzle-description">${puzzleData.main_puzzle}</p>
            <div class="progress-steps">
                ${Array.from({length: puzzleData.total_tasks}, (_, i) => `
                    <div class="step-container">
                        <div class="step ${i < puzzleData.completed_tasks ? 'completed' : ''}">${i + 1}</div>
                        ${i < puzzleData.total_tasks - 1 ? 
                            `<div class="connector ${i < puzzleData.completed_tasks - 1 ? 'completed' : ''}"></div>` 
                            : ''}
                    </div>
                `).join('')}
            </div>
            <p class="progress-text">${puzzleData.completed_tasks}/${puzzleData.total_tasks} tasks completed (${Math.round(percentage)}%)</p>
        </div>
    `;
}

function getItemTooltip(item) {
    const tooltips = {
        "Craftsman's hammer": "For construction and repairs",
        "Set of precision tools": "For detailed mechanical work",
        "Blueprint journal": "Contains architectural designs",
        "Enchanted measuring tape": "Reveals structural patterns",
        "Courage charm": "Enhances bravery and leadership"
    };
    return tooltips[item] || "A useful item";
}

function useExample(example) {
    const input = document.getElementById('userInput');
    input.value = example;
    input.focus();
}

function showError(message) {
    const errorMessage = document.createElement('div');
    errorMessage.className = 'message bot-message error';
    errorMessage.textContent = message;
    document.getElementById('gameOutput').appendChild(errorMessage);
}

function scrollToBottom() {
    const gameOutput = document.getElementById('gameOutput');
    gameOutput.scrollTop = gameOutput.scrollHeight;
}