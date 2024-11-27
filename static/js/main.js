let gameState = {
    inventory: {},
    history: []
};

// Create a styled message element for chat-like interface
function createMessageElement(text, isUser = false) {
    const messageContainer = document.createElement('div');
    messageContainer.className = `message-container ${isUser ? 'user' : 'bot'}`;
    
    const message = document.createElement('div');
    message.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    message.textContent = text;
    
    messageContainer.appendChild(message);
    return messageContainer;
}

async function submitAction() {
    const input = document.getElementById('userInput');
    const action = input.value;
    if (!action.trim()) return;
    
    // Add user message to chat
    const output = document.getElementById('gameOutput');
    output.appendChild(createMessageElement(action, true));
    input.value = '';

    try {
        const response = await fetch('/action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        // Add bot response to chat
        output.appendChild(createMessageElement(result.response, false));
        updateInventory(result.inventory);
        
        // Store in history
        gameState.history.push({
            action: action,
            response: result.response,
            inventory: result.inventory
        });
        
        // Scroll to bottom of output
        output.scrollTop = output.scrollHeight;
    } catch (error) {
        console.error('Error:', error);
        output.appendChild(createMessageElement('Error processing your action. Please try again.', false));
    }
}

function updateGameOutput(text) {
    const output = document.getElementById('gameOutput');
    output.appendChild(createMessageElement(text, false));
    output.scrollTop = output.scrollHeight;
}

function updateInventory(inventory) {
    const slots = document.getElementById('inventorySlots');
    slots.innerHTML = '';
    gameState.inventory = inventory;
    
    // Create a nicely formatted inventory display
    Object.entries(inventory).forEach(([item, count]) => {
        const slot = document.createElement('div');
        slot.className = 'inventory-slot';
        slot.draggable = true;
        
        // Create item name element
        const itemName = document.createElement('div');
        itemName.className = 'item-name';
        itemName.textContent = item;
        
        // Create item count element
        const itemCount = document.createElement('div');
        itemCount.className = 'item-count';
        itemCount.textContent = `x${count}`;
        
        slot.appendChild(itemName);
        slot.appendChild(itemCount);
        
        // Add drag functionality
        slot.addEventListener('dragstart', handleDragStart);
        slot.addEventListener('dragend', handleDragEnd);
        
        slots.appendChild(slot);
    });
}

function handleDragStart(e) {
    e.target.classList.add('dragging');
    e.dataTransfer.setData('text/plain', e.target.querySelector('.item-name').textContent);
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
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
        // Remove last two messages (user message and bot response)
        output.removeChild(output.lastElementChild);
        output.removeChild(output.lastElementChild);
        
        // Restore previous inventory state
        if (gameState.history.length > 0) {
            updateInventory(gameState.history[gameState.history.length - 1].inventory);
        }
    }
}

function clearChat() {
    const output = document.getElementById('gameOutput');
    output.innerHTML = '';
    gameState.history = [];
    // Reset to initial inventory state
    updateInventory({
        "cloth pants": 1,
        "cloth shirt": 1,
        "gold": 5
    });
}

function useExample(example) {
    const input = document.getElementById('userInput');
    input.value = example;
    submitAction();
}

// Handle Enter key
document.getElementById('userInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        submitAction();
    }
});

// Initialize game
document.addEventListener('DOMContentLoaded', () => {
    submitAction('start game');
});