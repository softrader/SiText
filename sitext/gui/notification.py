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
        
        # Style the notification with light grey background
        self.setStyleSheet("""
            QLabel {
                background-color: rgb(220, 220, 220);
                color: black;
                border: 2px solid rgb(180, 180, 180);
                padding: 14px 24px;
                font-size: 14px;
            }
        """)
        
        # Set font
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.setFont(font)
        
        # Make it frameless and stay on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Make cursor change to pointer on hover
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
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
    
    def mousePressEvent(self, event):
        """Handle mouse click to dismiss notification."""
        self._fade_out()
        event.accept()
    
    def show_notification(self, global_pos=None):
        """Show the notification with animation.
        
        Args:
            global_pos: QPoint with global screen coordinates (optional)
        """
        if global_pos:
            self.move(global_pos)
        
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
        global_pos = None
        if self.parent:
            parent_geometry = self.parent.geometry()
            
            # Stack notifications vertically
            y = 20
            for existing in self.notifications:
                if existing.isVisible():
                    y += existing.height() + 10
            
            # Calculate position in global coordinates
            global_pos = self.parent.mapToGlobal(QPoint(
                parent_geometry.width() - toast.width() - 20,
                y
            ))
        
        self.notifications.append(toast)
        toast.show_notification(global_pos)
        
        # Clean up after it's hidden
        QTimer.singleShot(duration + 500, lambda: self._cleanup(toast))
    
    def _cleanup(self, toast):
        """Remove notification from list."""
        if toast in self.notifications:
            self.notifications.remove(toast)
            toast.deleteLater()
