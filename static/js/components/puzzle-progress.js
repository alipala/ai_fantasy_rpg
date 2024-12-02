// components/puzzle-progress.js

function createPuzzleProgress() {
    const container = document.createElement('div');
    container.className = 'puzzle-progress-container';
    container.innerHTML = `
        <div class="card w-full mb-4">
            <div class="card-header">
                <h3 class="text-sm font-medium">Puzzle Progress</h3>
            </div>
            <div class="card-content p-4">
                <div class="space-y-2">
                    <p class="puzzle-description text-sm"></p>
                    <div class="progress-bar-container w-full bg-gray-200 rounded-full h-2.5">
                        <div class="progress-bar bg-blue-600 h-2.5 rounded-full transition-all duration-500" style="width: 0%"></div>
                    </div>
                    <p class="progress-text text-sm text-right">0% Complete</p>
                </div>
            </div>
        </div>
    `;
    return container;
}

function updatePuzzleProgress(puzzleProgress) {
    if (!puzzleProgress) return;

    const progress = (puzzleProgress.completed_tasks / puzzleProgress.total_tasks) * 100;
    const container = document.querySelector('.puzzle-progress-container');
    
    if (container) {
        container.querySelector('.puzzle-description').textContent = puzzleProgress.main_puzzle;
        container.querySelector('.progress-bar').style.width = `${progress}%`;
        container.querySelector('.progress-text').textContent = `${Math.round(progress)}% Complete`;
    }
}

// Export for use in main.js
window.createPuzzleProgress = createPuzzleProgress;
window.updatePuzzleProgress = updatePuzzleProgress;