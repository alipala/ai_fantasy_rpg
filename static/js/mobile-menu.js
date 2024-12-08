class MobileMenu {
    constructor() {
        this.isOpen = false;
        this.menuToggle = document.querySelector('.mobile-nav__toggle');
        this.menu = document.querySelector('.mobile-menu');
        this.overlay = document.querySelector('.mobile-menu__overlay');
        this.closeButton = document.querySelector('.mobile-menu__close');
        this.tabs = document.querySelectorAll('.mobile-menu__tab');
        this.panels = document.querySelectorAll('.mobile-menu__panel');
        this.questProgress = document.querySelector('.puzzle-progress-container');
        this.setupQuestProgress();
        
        this.init();
        this.setupDefaultActions();
    }

    init() {
        this.menuToggle.addEventListener('click', () => this.toggleMenu());
        this.overlay.addEventListener('click', () => this.closeMenu());
        this.closeButton.addEventListener('click', () => this.closeMenu());
        
        this.tabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab));
        });

        this.setupResponsiveContent();
        window.addEventListener('resize', () => this.handleResize());
    }

    setupDefaultActions() {
        const actionsPanel = document.querySelector('[data-panel="actions"]');
        if (actionsPanel && actionsPanel.children.length === 0) {
            const defaultActions = [
                'Look around',
                'Explore area',
                'Check surroundings'
            ];
            
            defaultActions.forEach(action => {
                const button = document.createElement('button');
                button.className = 'example-button';
                button.textContent = action;
                button.onclick = () => this.useAction(action);
                actionsPanel.appendChild(button);
            });
        }
    }

    useAction(action) {
        const input = document.getElementById('userInput');
        if (input) {
            input.value = action;
            this.closeMenu();
            // Optional: auto-submit the action
            document.getElementById('submitBtn')?.click();
        }
    }

    setupQuestProgress() {
        if (this.questProgress) {
            const mobileProgress = document.createElement('div');
            mobileProgress.className = 'mobile-quest-progress';
            mobileProgress.innerHTML = this.questProgress.innerHTML;
            document.querySelector('.mobile-nav').after(mobileProgress);
        }
    }

    toggleMenu() {
        this.isOpen = !this.isOpen;
        this.menu.classList.toggle('active', this.isOpen);
        document.body.style.overflow = this.isOpen ? 'hidden' : '';
    }

    closeMenu() {
        this.isOpen = false;
        this.menu.classList.remove('active');
        document.body.style.overflow = '';
    }

    switchTab(selectedTab) {
        const targetPanel = selectedTab.dataset.tab;
        
        this.tabs.forEach(tab => {
            tab.classList.toggle('active', tab === selectedTab);
        });
        
        this.panels.forEach(panel => {
            panel.classList.toggle('active', panel.dataset.panel === targetPanel);
        });
    }

    setupResponsiveContent() {
        const inventoryContent = document.querySelector('.inventory-section');
        const actionsContent = document.querySelector('.examples');
        const mobileInventoryPanel = document.querySelector('[data-panel="inventory"]');
        const mobileActionsPanel = document.querySelector('[data-panel="actions"]');
        
        this.originalLocations = {
            inventory: { parent: inventoryContent.parentNode, content: inventoryContent },
            actions: { parent: actionsContent.parentNode, content: actionsContent }
        };

        if (window.innerWidth < 768) {
            mobileInventoryPanel.appendChild(inventoryContent);
            mobileActionsPanel.appendChild(actionsContent);
        }
    }

    handleResize() {
        const isMobile = window.innerWidth < 768;
        
        if (isMobile && !this.isMobileView) {
            this.moveToMobile();
        } else if (!isMobile && this.isMobileView) {
            this.moveToDesktop();
        }
        
        this.isMobileView = isMobile;
    }

    moveToMobile() {
        const mobileInventoryPanel = document.querySelector('[data-panel="inventory"]');
        const mobileActionsPanel = document.querySelector('[data-panel="actions"]');
        
        mobileInventoryPanel.appendChild(this.originalLocations.inventory.content);
        mobileActionsPanel.appendChild(this.originalLocations.actions.content);
    }

    moveToDesktop() {
        this.originalLocations.inventory.parent.appendChild(this.originalLocations.inventory.content);
        this.originalLocations.actions.parent.appendChild(this.originalLocations.actions.content);
        this.closeMenu();
    }
}

// Initialize mobile menu when document is ready
document.addEventListener('DOMContentLoaded', () => {
    new MobileMenu();
});