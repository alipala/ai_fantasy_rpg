// components/puzzle-progress.js

function createPuzzleProgress() {
    const container = document.createElement('div');
    container.className = 'puzzle-progress-container';
    container.innerHTML = `
        <div class="card w-full bg-gray-800 rounded-lg p-4 mb-4">
            <div class="card-header border-none">
                <h3 class="text-sm font-medium text-white">Quest Progress</h3>
            </div>
            <div class="card-content p-4">
                <div class="space-y-2">
                    <p class="puzzle-description text-sm text-gray-300"></p>
                    <div class="progress-bar-container w-full bg-gray-700 rounded-full h-2.5">
                        <div class="progress-bar bg-green-600 h-2.5 rounded-full transition-all duration-500" style="width: 0%"></div>
                    </div>
                    <div class="flex justify-between">
                        <span class="progress-count text-xs text-gray-400">0/0 tasks</span>
                        <span class="progress-text text-xs text-gray-400">0% Complete</span>
                    </div>
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
        container.querySelector('.progress-count').textContent = 
            `${puzzleProgress.completed_tasks}/${puzzleProgress.total_tasks} tasks`;
        container.querySelector('.progress-text').textContent = `${Math.round(progress)}% Complete`;
    }
}

window.createPuzzleProgress = createPuzzleProgress;
window.updatePuzzleProgress = updatePuzzleProgress;