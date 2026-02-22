import sys
import os
import re
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QFileDialog, QMessageBox, 
                                 QInputDialog, QDialog, QVBoxLayout, QLineEdit, QRadioButton, 
                                 QButtonGroup, QDialogButtonBox)
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtCore import Qt

class NamingStrategyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Naming Strategy")
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Enter prefix for all photos copied to this folder:"))
        self.prefix_input = QLineEdit(self)
        layout.addWidget(self.prefix_input)
        
        self.strategy_group = QButtonGroup(self)
        
        self.radio_default = QRadioButton("keep default name")
        self.radio_default.setChecked(True)
        self.strategy_group.addButton(self.radio_default, 0)
        layout.addWidget(self.radio_default)
        
        self.radio_incremental = QRadioButton("incremental")
        self.strategy_group.addButton(self.radio_incremental, 1)
        layout.addWidget(self.radio_incremental)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_values(self):
        strategy = "default" if self.radio_default.isChecked() else "incremental"
        return self.prefix_input.text(), strategy

class PhotoPickerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Picker")
        self.resize(800, 600)
        self.allowed_extensions = self.load_config()

        # State
        self.source_folder = ""
        self.destination_folder = ""
        self.photo_prefix = ""
        self.naming_strategy = "default"
        self.incremental_counter = 1
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

        # Open Destination Folder Action
        open_dest_action = QAction("Open Destination Folder", self)
        open_dest_action.triggered.connect(self.open_destination_folder)
        file_menu.addAction(open_dest_action)

    def open_source_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder_path:
            self.source_folder = folder_path
            self.load_photos_from_folder()

    def open_destination_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder_path:
            # Check if directory is empty
            if os.listdir(folder_path):
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Folder Not Empty")
                msg_box.setText("The selected target folder is not empty.")
                msg_box.setInformativeText("Are you sure you want to use it as the destination folder?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                
                ret = msg_box.exec()
                if ret != QMessageBox.Yes:
                    return # User aborted

            self.destination_folder = folder_path
            self._ask_for_prefix_and_set_destination()

    def _ask_for_prefix_and_set_destination(self):
        dialog = NamingStrategyDialog(self)
        if dialog.exec() == QDialog.Accepted:
            prefix, strategy = dialog.get_values()
            self.photo_prefix = prefix
            self.naming_strategy = strategy
            
            if self.naming_strategy == "incremental":
                self._set_initial_incremental_counter()
            else:
                self.incremental_counter = 1


    def _set_initial_incremental_counter(self):
        max_num = 0
        if self.destination_folder and os.path.exists(self.destination_folder):
            # Escape prefix in case it contains regex special characters like '.' or '-'
            pattern = re.compile(rf"^{re.escape(self.photo_prefix)}(\d+)")
            
            for file in os.listdir(self.destination_folder):
                # Match the pattern at the start of the filename
                match = pattern.match(file)
                if match:
                    # group(1) captures the digits immediately following the prefix
                    num_str = match.group(1)
                    max_num = max(max_num, int(num_str))
                    
        self.incremental_counter = max_num + 1

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
        if not self.photo_files:
            return

        if self.current_photo_index < 0:
            self.image_label.clear()
            self.image_label.setText("start")
            self.setWindowTitle("Photo Picker - start")
        elif self.current_photo_index >= len(self.photo_files):
            self.image_label.clear()
            self.image_label.setText("end")
            self.setWindowTitle("Photo Picker - end")
        else:
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

    def keyPressEvent(self, event):
        if not self.photo_files:
            return
            
        if event.key() == Qt.Key_Left:
            if self.current_photo_index >= 0:
                self.current_photo_index -= 1
                self.display_current_photo()
        elif event.key() == Qt.Key_Right:
            if self.current_photo_index < len(self.photo_files):
                self.current_photo_index += 1
                self.display_current_photo()

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
