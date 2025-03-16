class NotificationManager {
    constructor(maxNotifications = 3) {
        this.container = this.createContainer();
        this.maxNotifications = maxNotifications;
        this.activeNotifications = 0;
    }

    createContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info') {
        if (this.activeNotifications >= this.maxNotifications) {
            const oldestNotification = this.container.firstChild;
            if (oldestNotification) {
                oldestNotification.remove();
                this.activeNotifications--;
            }
        }

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        // Set background color based on type
        const colors = {
            success: '#4caf50',
            error: '#f44336',
            warning: '#ff9800',
            info: '#2196f3'
        };
        notification.style.backgroundColor = colors[type] || colors.info;

        // Add animation classes
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        notification.style.transition = 'all 0.3s ease-in-out';
        
        // Force reflow
        notification.offsetHeight;
        
        // Add show class for animation
        notification.classList.add('show');


        this.container.appendChild(notification);
        this.activeNotifications++;

        // Trigger animation
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 50);

        // Auto-remove after 5 seconds
        const removeNotification = () => {
            notification.classList.remove('show');
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                notification.remove();
                this.activeNotifications--;
            }, 300);
        };

        setTimeout(removeNotification, 5000);

        // Click to dismiss
        notification.addEventListener('click', () => {
            notification.classList.remove('show');
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => notification.remove(), 300);
        });
        notification.addEventListener('click', removeNotification);
    }
}

// Initialize the notification manager globally
window.notifications = new NotificationManager(3);