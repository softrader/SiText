"""Toast notification widget for non-blocking messages."""

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PyQt6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PyQt6.QtGui import QFont


class NotificationToast(QLabel):
    """A toast-style notification that appears briefly in the corner."""
    
    def __init__(self, message: str, parent=None, duration: int = 3000):
        """Initialize notification toast.
        
        Args:
            message: Message to display
            parent: Parent widget
            duration: How long to show in milliseconds (default 3000ms = 3s)
        """
        super().__init__(message, parent)
        self.duration = duration
        
        # Style the notification
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 240);
                color: white;
                border: 1px solid rgba(100, 100, 100, 180);
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
            }
        """)
        
        # Set font
        font = QFont()
        font.setPointSize(13)
        self.setFont(font)
        
        # Make it frameless and stay on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Adjust size to content
        self.adjustSize()
        
        # Set up opacity effect for fade out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)
        
        # Timer to auto-hide
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._fade_out)
        
        # Animation for fade out
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.finished.connect(self.hide)
    
    def show_notification(self):
        """Show the notification with animation."""
        if self.parent():
            # Position in top right corner of parent
            parent_rect = self.parent().rect()
            x = parent_rect.right() - self.width() - 20
            y = 20
            self.move(x, y)
        
        self.show()
        self.raise_()
        
        # Start timer to fade out
        self.hide_timer.start(self.duration)
    
    def _fade_out(self):
        """Fade out the notification."""
        self.fade_animation.start()


class NotificationManager:
    """Manages multiple notifications with stacking."""
    
    def __init__(self, parent):
        """Initialize notification manager.
        
        Args:
            parent: Parent widget where notifications will appear
        """
        self.parent = parent
        self.notifications = []
    
    def show(self, message: str, duration: int = 3000):
        """Show a notification.
        
        Args:
            message: Message to display
            duration: How long to show in milliseconds
        """
        # Clean up finished notifications
        self.notifications = [n for n in self.notifications if n.isVisible()]
        
        # Create new notification
        toast = NotificationToast(message, self.parent, duration)
        
        # Position it (stack if multiple notifications)
        if self.parent:
            parent_rect = self.parent.rect()
            x = parent_rect.right() - toast.width() - 20
            
            # Stack notifications vertically
            y = 20
            for existing in self.notifications:
                if existing.isVisible():
                    y += existing.height() + 10
            
            toast.move(x, y)
        
        self.notifications.append(toast)
        toast.show_notification()
        
        # Clean up after it's hidden
        QTimer.singleShot(duration + 500, lambda: self._cleanup(toast))
    
    def _cleanup(self, toast):
        """Remove notification from list."""
        if toast in self.notifications:
            self.notifications.remove(toast)
            toast.deleteLater()
