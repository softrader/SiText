"""Status bar notification system for non-blocking messages."""

from PyQt6.QtCore import QTimer


class NotificationManager:
    """Manages notifications in the status bar."""
    
    def __init__(self, main_window):
        """Initialize notification manager.
        
        Args:
            main_window: MainWindow instance with statusBar()
        """
        self.main_window = main_window
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._restore_status)
        self.default_message = ""
    
    def show(self, message: str, duration: int = 3000):
        """Show a notification in the status bar.
        
        Args:
            message: Message to display
            duration: How long to show in milliseconds (default 3s)
        """
        # Store the default status message if not already stored
        if not self.default_message:
            notes_dir = self.main_window.notes_directory
            self.default_message = f"Notes: {notes_dir}"
        
        # Show the notification message
        self.main_window.statusBar().showMessage(message)
        
        # Set timer to restore default message
        self.timer.start(duration)
    
    def _restore_status(self):
        """Restore the default status bar message."""
        self.main_window.statusBar().showMessage(self.default_message)
