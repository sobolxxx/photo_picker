import sys
import os
import json
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtCore import Qt

class PhotoPickerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Picker")
        self.resize(800, 600)
        self.allowed_extensions = self.load_config()

        # State
        self.source_folder = ""
        self.photo_files = []
        self.current_photo_index = -1

        self.setup_ui()

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return [ext.lower() for ext in config.get("allowed_extensions", [])]
        except Exception as e:
            print(f"Error loading config.json: {e}")
            return [".jpg", ".jpeg", ".png"] # fallback

    def setup_ui(self):
        # Central widget for image display
        self.image_label = QLabel("Open a folder to view photos", self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.image_label)

        # Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        # Open Source Folder Action
        open_source_action = QAction("Open Source Folder", self)
        open_source_action.triggered.connect(self.open_source_folder)
        file_menu.addAction(open_source_action)

    def open_source_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder_path:
            self.source_folder = folder_path
            self.load_photos_from_folder()

    def load_photos_from_folder(self):
        self.photo_files = []
        for file in os.listdir(self.source_folder):
            ext = os.path.splitext(file)[1].lower()
            if ext in self.allowed_extensions:
                self.photo_files.append(os.path.join(self.source_folder, file))

        if self.photo_files:
            self.current_photo_index = 0
            self.display_current_photo()
        else:
            self.image_label.setText("No photos found in the selected folder.")
            self.current_photo_index = -1

    def display_current_photo(self):
        if 0 <= self.current_photo_index < len(self.photo_files):
            photo_path = self.photo_files[self.current_photo_index]
            pixmap = QPixmap(photo_path)
            
            # Scale pixmap to fit the label while keeping aspect ratio
            # Use label's size or window size if label is not fully laid out
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.setWindowTitle(f"Photo Picker - {os.path.basename(photo_path)}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-scale image when window is resized if an image is loaded
        if self.current_photo_index != -1:
            self.display_current_photo()

def main():
    app = QApplication(sys.argv)
    window = PhotoPickerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
