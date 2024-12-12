
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

// Landing Page Initialization
function initializeLandingPage() {
    const initialStartBtn = document.getElementById('initialStartBtn');
    const finalStartBtn = document.getElementById('finalStartBtn');
    
    // Add smooth scroll behavior
    document.querySelector('.start-screen').addEventListener('scroll', () => {
        const sections = document.querySelectorAll('.landing-section');
        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            if (rect.top >= 0 && rect.top <= window.innerHeight / 2) {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });
    });

    // Handle start button clicks
    [initialStartBtn, finalStartBtn].forEach(btn => {
        btn.addEventListener('click', startGameTransition);
    });
}

function startGameTransition() {
    const startScreen = document.getElementById('startScreen');
    const selectionPhase = document.getElementById('selectionPhase');
    const gameBackground = document.getElementById('gameBackground');

    // Add fade-out animation
    startScreen.style.opacity = '0';
    
    // Show game background
    gameBackground.style.opacity = '1';
    gameBackground.style.visibility = 'visible';

    // Transition to selection phase after animation
    setTimeout(() => {
        startScreen.classList.add('hidden');
        selectionPhase.classList.remove('hidden');
        
        // Force reflow
        void selectionPhase.offsetWidth;
        
        // Add visible class
        selectionPhase.classList.add('visible');
        
        // Update game state
        gameState.currentScreen = 'worldSelect';
        showScreen('worldSelect');
        startGame();
    }, 300);
}

// Initialize landing page when document loads
document.addEventListener('DOMContentLoaded', () => {
    initializeLandingPage();
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

async function displayCharacters(town) {
    const characterList = document.getElementById('characterList');
    characterList.innerHTML = '';
    
    // Show loading state while checking puzzles
    characterList.innerHTML = '<div class="loading-message">Loading characters...</div>';
    
    try {
        // Check puzzle availability for all characters
        const characterEntries = Object.entries(town.npcs);
        const characterData = await Promise.all(
            characterEntries.map(async ([_, char]) => {
                const hasPuzzle = await checkCharacterHasPuzzle(char.name);
                return { ...char, hasPuzzle };
            })
        );
        
        // Clear loading message
        characterList.innerHTML = '';
        
        // Create character buttons
        characterData.forEach(char => {
            const button = document.createElement('button');
            button.className = `selection-button ${!char.hasPuzzle ? 'disabled' : ''}`;
            button.innerHTML = `
                <h3>${char.name}</h3>
                <p>${char.description.substring(0, 100)}...</p>
                ${!char.hasPuzzle ? '<span class="no-quest-badge">No Available Quests</span>' : ''}
            `;
            
            if (char.hasPuzzle) {
                button.onclick = () => selectCharacter(char);
            } else {
                button.disabled = true;
            }
            
            characterList.appendChild(button);
        });
        
    } catch (error) {
        console.error('Error displaying characters:', error);
        characterList.innerHTML = '<div class="error-message">Error loading characters</div>';
    }
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

function fadeOutGame() {
    return new Promise(resolve => {
        const gameContainer = document.getElementById('gameContainer');
        const puzzleProgress = document.getElementById('puzzleProgress');
        
        // Fade out both elements
        gameContainer.style.opacity = '0';
        puzzleProgress.style.opacity = '0';
        
        setTimeout(() => {
            gameContainer.style.display = 'none';
            puzzleProgress.style.display = 'none';
            resolve();
        }, 300);
    });
}

async function handlePuzzleCompletion(result) {
    // 1. Fade out game completely
    await fadeOutGame();
    
    // 2. Create and show loading overlay
    const overlay = document.createElement('div');
    overlay.className = 'completion-overlay';
    
    // 3. Show initial completion message with loading
    overlay.innerHTML = `
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
    
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add('visible'));
    
    // 4. Request completion image
    try {
        const imageResponse = await fetch('/generate-completion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const imageData = await imageResponse.json();
        
        if (imageData.success && imageData.completion_image) {
            // 5. Load image
            const img = new Image();
            img.onload = () => {
                // 6. Show final victory screen
                overlay.classList.add('transitioning');
                setTimeout(() => {
                    overlay.innerHTML = `
                        <div class="completion-content">
                            <div class="completion-header">
                                <h2>Victory in ${result.world.name}!</h2>
                                <p class="completion-subtitle">The realm has been saved by ${result.character.name}</p>
                            </div>
                            <div class="completion-image-container">
                                <img src="${imageData.completion_image.url}" 
                                     alt="Victory scene in ${result.world.name}"
                                     class="completion-image"
                                />
                                <div class="completion-image-caption">
                                    <h3>The Legend of ${result.character.name}</h3>
                                    <p>Savior of ${result.world.name}</p>
                                    <div class="achievement-badges">
                                        ${imageData.completion_image.context.achievements.map(achievement => 
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
                        </div>
                    `;
                    overlay.classList.remove('transitioning');
                }, 300);
            };
            img.src = imageData.completion_image.url;
        }
    } catch (error) {
        console.error('Error generating completion image:', error);
        // Show completion screen without image
        showCompletionWithoutImage(result, overlay);
    }
}

function showCompletionWithoutImage(result, overlay) {
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
            </div>
        `;
        overlay.classList.remove('transitioning');
    }, 300);
}

function generateShareableLink() {
    const shareData = {
        world: gameState.world.name,
        character: gameState.character.name,
        completionImage: document.querySelector('.completion-image').src,
        achievements: gameState.achievements || [],
        timestamp: Date.now()
    };
    
    const encoded = btoa(JSON.stringify(shareData));
    return `${window.location.origin}/victory/${encoded}`;
}

function generateQRCode(shareUrl) {
    const qrContainer = document.createElement('div');
    qrContainer.className = 'qr-code';
    new QRCode(qrContainer, {
        text: shareUrl,
        width: 128,
        height: 128,
        colorDark: "#000000",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.H
    });
    return qrContainer;
}

function shareStory() {
    const shareUrl = generateShareableLink();
    const modal = document.createElement('div');
    modal.className = 'share-modal';
    
    modal.innerHTML = `
        <div class="share-content">
            <div class="share-header">
                <h2>Share Your Victory</h2>
                <button class="close-modal" id="closeShareModal">×</button>
            </div>
            <div class="share-preview">
                <img src="${document.querySelector('.completion-image').src}" 
                     alt="Victory Scene" class="share-image"/>
                <p class="share-text">Victory in ${gameState.world.name}! 
                   ${gameState.character.name} has saved the realm!</p>
            </div>
            <div class="share-options">
                <div class="link-section">
                    <h3>Share Link</h3>
                    <div class="share-link-container">
                        <input type="text" readonly value="${shareUrl}" 
                               class="share-link-input" id="shareLinkInput"/>
                        <button class="copy-link-btn" id="copyLinkBtn">
                            Copy Link
                        </button>
                    </div>
                </div>
                <button class="download-btn" id="downloadImageBtn">
                    Download Image
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    setupShareModalListeners(modal);
    requestAnimationFrame(() => modal.classList.add('visible'));
}

async function shareGameAchievement(achievementData) {
    // Get current completion data from the DOM if not provided
    if (!achievementData) {
        const completionImage = document.querySelector('.completion-image');
        achievementData = {
            imageUrl: completionImage.src,
            worldName: gameState.world.name,
            characterName: gameState.character.name
        };
    }

    // Create share modal
    const modal = document.createElement('div');
    modal.className = 'share-modal';
    
    modal.innerHTML = `
        <div class="share-content">
            <div class="share-header">
                <h2>Share Your Victory</h2>
                <button class="close-modal" onclick="closeShareModal()">×</button>
            </div>
            <div class="share-preview">
                <img src="${achievementData.imageUrl}" alt="Victory Scene" class="share-image"/>
                <p class="share-text">Victory in ${achievementData.worldName}! 
                   ${achievementData.characterName} has saved the realm!</p>
            </div>
            <div class="share-options">
                <button class="share-option instagram" id="instagramShare">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" class="share-icon">
                        <path fill="currentColor" d="M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.415 2.227.055 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.415-1.274.055-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06l.045.03zm0 3.678c-3.405 0-6.162 2.76-6.162 6.162 0 3.405 2.76 6.162 6.162 6.162 3.405 0 6.162-2.76 6.162-6.162 0-3.405-2.76-6.162-6.162-6.162zM12 16c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm7.846-10.405c0 .795-.646 1.44-1.44 1.44-.795 0-1.44-.646-1.44-1.44 0-.794.646-1.439 1.44-1.439.793-.001 1.44.645 1.44 1.439z"/>
                    </svg>
                    Share to Instagram Story
                </button>
                <button class="share-option download" id="downloadImage">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" class="share-icon">
                        <path fill="currentColor" d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                    </svg>
                    Download Image
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    requestAnimationFrame(() => modal.classList.add('visible'));

    // Add event listeners
    modal.querySelector('#instagramShare').addEventListener('click', () => shareToInstagram(achievementData.imageUrl));
    modal.querySelector('#downloadImage').addEventListener('click', () => downloadImage(achievementData.imageUrl));
}

function closeShareModal() {
    const modal = document.querySelector('.share-modal');
    if (modal) {
        modal.classList.remove('visible');
        setTimeout(() => modal.remove(), 300);
    }
}


// Function to handle Instagram sharing
function shareToInstagram(imageUrl) {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    
    if (isMobile) {
        // Try to open Instagram app
        window.location.href = 'instagram://story-camera';
        
        // Fallback after a delay if Instagram didn't open
        setTimeout(() => {
            if (!document.hidden) {
                showInstagramBrowserOption(imageUrl);
            }
        }, 2000);
    } else {
        // Show desktop instructions
        showInstagramBrowserOption(imageUrl);
    }
}

// Function to show Instagram browser fallback
function showInstagramBrowserOption(imageUrl) {
    const modal = document.createElement('div');
    modal.className = 'instagram-modal';
    modal.innerHTML = `
        <div class="instagram-content">
            <h3>Share to Instagram Story</h3>
            <ol class="share-instructions">
                <li>First, save the image to your device</li>
                <li>Open Instagram</li>
                <li>Create a new Story</li>
                <li>Select this image from your gallery</li>
            </ol>
            <div class="instagram-actions">
                <button class="instagram-button download-btn">Download Image</button>
                <button class="instagram-button instagram-open-btn">Open Instagram</button>
                <button class="instagram-button close-btn">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners for the new modal
    const downloadBtn = modal.querySelector('.download-btn');
    const instagramBtn = modal.querySelector('.instagram-open-btn');
    const closeBtn = modal.querySelector('.close-btn');
    
    downloadBtn.addEventListener('click', () => downloadImage(imageUrl));
    instagramBtn.addEventListener('click', () => window.open('https://instagram.com/stories/create/', '_blank'));
    closeBtn.addEventListener('click', () => modal.remove());
    
    requestAnimationFrame(() => modal.classList.add('visible'));
}

// Setup event listeners for the share modal
function setupShareModalListeners(modal) {
    const closeBtn = modal.querySelector('#closeShareModal');
    const copyBtn = modal.querySelector('#copyLinkBtn');
    const downloadBtn = modal.querySelector('#downloadImageBtn');
    const linkInput = modal.querySelector('#shareLinkInput');

    closeBtn.addEventListener('click', () => {
        modal.classList.remove('visible');
        setTimeout(() => modal.remove(), 300);
    });

    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(linkInput.value);
            showToast('Link copied to clipboard!');
        } catch (err) {
            console.error('Failed to copy:', err);
            linkInput.select();
            document.execCommand('copy');
            showToast('Link copied to clipboard!');
        }
    });

    downloadBtn.addEventListener('click', () => {
        downloadImage(document.querySelector('.completion-image').src);
    });
}

// Helper function to show toast messages
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    requestAnimationFrame(() => {
        toast.classList.add('visible');
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    });
}

// Function to handle native sharing
async function shareToNative(imageUrl) {
    try {
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        const file = new File([blob], 'victory.png', { type: 'image/png' });
        
        await navigator.share({
            title: `Victory in ${gameState.world.name}!`,
            text: `I completed my quest as ${gameState.character.name} and saved ${gameState.world.name} from destruction!`,
            files: [file]
        });
    } catch (error) {
        console.error('Error sharing:', error);
        showInstagramBrowserOption(imageUrl);
    }
}

// Function to handle image download
async function downloadImage(imageUrl) {
    try {
        // Use proxy route instead of direct URL
        const proxyUrl = `/proxy-image/${encodeURIComponent(imageUrl)}`;
        const response = await fetch(proxyUrl);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `victory-in-${gameState.world.name.toLowerCase()}.png`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        showToast('Image downloaded successfully!');
    } catch (error) {
        console.error('Error downloading image:', error);
        showToast('Failed to download image. Please try again.');
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

async function checkCharacterHasPuzzle(characterName) {
    try {
        const response = await fetch('/check-puzzle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ character: characterName })
        });
        const data = await response.json();
        return data.hasPuzzle;
    } catch (error) {
        console.error('Error checking character puzzles:', error);
        return false;
    }
}