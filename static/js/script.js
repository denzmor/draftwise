document.addEventListener('DOMContentLoaded', function() {
    // Utility Functions
    const utils = {
        // Safe element selection
        select: (selector) => document.querySelector(selector),
        selectAll: (selector) => document.querySelectorAll(selector),
        
        // Create element with optional classes
        createElement: (tag, classes = [], text = '') => {
            const element = document.createElement(tag);
            element.classList.add(...classes);
            if (text) element.textContent = text;
            return element;
        },

        // Debounce function to limit rapid event firing
        debounce: (func, delay) => {
            let timeoutId;
            return (...args) => {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => func.apply(this, args), delay);
            };
        }
    };

    // Notification System
    const NotificationManager = {
        container: null,

        init() {
            if (!this.container) {
                this.container = utils.createElement('div', ['notification-container']);
                this.container.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1000;
                `;
                document.body.appendChild(this.container);
            }
        },

        show(message, type = 'info') {
            this.init();
            const notification = utils.createElement('div', ['notification', `notification-${type}`]);
            notification.textContent = message;

            // Style based on type
            const styles = {
                'success': { bg: '#d4edda', color: '#155724' },
                'error': { bg: '#f8d7da', color: '#721c24' },
                'warning': { bg: '#fff3cd', color: '#856404' },
                'info': { bg: '#e2e3e5', color: '#383d41' }
            };

            const style = styles[type] || styles['info'];
            notification.style.cssText = `
                background-color: ${style.bg};
                color: ${style.color};
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            `;

            this.container.appendChild(notification);

            // Auto-remove
            setTimeout(() => {
                this.container.removeChild(notification);
            }, 3000);
        }
    };

    // Player List Management
    const PlayerListManager = {
        init() {
            const listItems = utils.selectAll('.player-list-item');
            listItems.forEach(item => {
                item.addEventListener('click', this.handleRemoval.bind(this));
            });

            // Player Search
            const searchInput = utils.select('#player-search');
            if (searchInput) {
                searchInput.addEventListener('input', 
                    utils.debounce(this.filterPlayers.bind(this), 300)
                );
            }
        },

        handleRemoval(event) {
            const item = event.currentTarget;
            const playerName = item.dataset.playerName;
            const listType = item.dataset.listType;

            if (confirm(`Remove ${playerName} from ${listType} list?`)) {
                this.removePlayer(playerName, listType, item);
            }
        },

        removePlayer(playerName, listType, element) {
            fetch('/remove_player', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': this.getCsrfToken()
                },
                body: JSON.stringify({
                    player: playerName,
                    list_type: listType
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    element.remove();
                    NotificationManager.show(
                        `${playerName} removed successfully`, 
                        'success'
                    );
                } else {
                    NotificationManager.show(
                        data.message || 'Failed to remove player', 
                        'error'
                    );
                }
            })
            .catch(error => {
                console.error('Error:', error);
                NotificationManager.show(
                    'An unexpected error occurred', 
                    'error'
                );
            });
        },

        filterPlayers(event) {
            const searchTerm = event.target.value.toLowerCase();
            const listItems = utils.selectAll('.player-list-item');

            listItems.forEach(item => {
                const playerName = item.dataset.playerName.toLowerCase();
                item.style.display = playerName.includes(searchTerm) 
                    ? '' 
                    : 'none';
            });
        },

        getCsrfToken() {
            const token = document.querySelector('meta[name="csrf-token"]');
            return token ? token.getAttribute('content') : '';
        }
    };

    // Optimization Run Management
    const OptimizationManager = {
        init() {
            const optimizeButton = utils.select('#run-optimize-btn');
            if (optimizeButton) {
                optimizeButton.addEventListener('click', this.runOptimization.bind(this));
            }
        },

        runOptimization(event) {
            if (!confirm('Are you sure you want to run the NHL Pool optimization?')) {
                event.preventDefault();
                return;
            }

            // Show loading state
            event.target.disabled = true;
            event.target.textContent = 'Optimizing...';

            fetch('/run_optimization', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': PlayerListManager.getCsrfToken()
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Optimization failed');
                }
                return response.json();
            })
            .then(data => {
                NotificationManager.show(
                    'Optimization completed successfully', 
                    'success'
                );
                this.displayOptimizationResults(data);
            })
            .catch(error => {
                console.error('Optimization error:', error);
                NotificationManager.show(
                    'Optimization failed', 
                    'error'
                );
            })
            .finally(() => {
                event.target.disabled = false;
                event.target.textContent = 'Run Optimization';
            });
        },

        displayOptimizationResults(data) {
            const resultsContainer = utils.select('#optimization-results');
            if (resultsContainer) {
                resultsContainer.innerHTML = `
                    <h2>Optimization Results</h2>
                    <p>Total Salary: $${data.total_salary.toLocaleString()}</p>
                    <p>Total Score: ${data.total_score}</p>
                    <!-- Add more detailed results rendering -->
                `;
            }
        }
    };

    // Theme Management
    const ThemeManager = {
        init() {
            const themeToggle = utils.select('#theme-toggle');
            if (themeToggle) {
                themeToggle.addEventListener('click', this.toggleTheme.bind(this));
                this.loadSavedTheme();
            }
        },

        toggleTheme() {
            document.body.classList.toggle('dark-mode');
            const isDarkMode = document.body.classList.contains('dark-mode');
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
        },

        loadSavedTheme() {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {
                document.body.classList.add('dark-mode');
            }
        }
