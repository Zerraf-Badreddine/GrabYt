import sys
import yt_dlp as youtube_dl
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFileDialog, QRadioButton, 
                             QHBoxLayout, QProgressBar, QComboBox, QButtonGroup)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRectF
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QConicalGradient


class CircularProgressBar(QWidget):
    """Custom circular/analog progress bar widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.setMinimumSize(200, 200)
        
    def setValue(self, value):
        self.value = max(0, min(100, value))
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        size = min(width, height)
        
        # Center the circle
        rect = QRectF((width - size) / 2 + 20, (height - size) / 2 + 20, size - 40, size - 40)
        
        # Draw background circle
        painter.setPen(QPen(QColor("#45475a"), 12, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 90 * 16, -360 * 16)
        
        # Draw progress arc with gradient
        if self.value > 0:
            gradient = QConicalGradient(rect.center(), 90)
            gradient.setColorAt(0, QColor("#89b4fa"))
            gradient.setColorAt(0.5, QColor("#a6e3a1"))
            gradient.setColorAt(1, QColor("#89b4fa"))
            
            pen = QPen(QColor("#a6e3a1"), 12, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            
            span_angle = -int(self.value * 3.6 * 16)
            painter.drawArc(rect, 90 * 16, span_angle)
        
        # Draw percentage text
        painter.setPen(QColor("#cdd6f4"))
        font = QFont("Inter", 32, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, f"{self.value}%")
        
        # Draw status text below percentage
        if self.value > 0 and self.value < 100:
            painter.setPen(QColor("#89b4fa"))
            font = QFont("Inter", 11)
            painter.setFont(font)
            status_rect = QRectF(rect.x(), rect.y() + rect.height() / 2 + 25, rect.width(), 30)
            painter.drawText(status_rect, Qt.AlignCenter, "Downloading...")
        elif self.value == 100:
            painter.setPen(QColor("#a6e3a1"))
            font = QFont("Inter", 11)
            painter.setFont(font)
            status_rect = QRectF(rect.x(), rect.y() + rect.height() / 2 + 25, rect.width(), 30)
            painter.drawText(status_rect, Qt.AlignCenter, "Complete!")


class QualityFetchThread(QThread):
    """Separate thread for fetching video qualities to prevent UI freezing"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.url, download=False)
                formats = info_dict.get('formats', [])
                
                # Get unique heights and sort them
                heights = set()
                for f in formats:
                    if 'height' in f and f['height']:
                        heights.add(f['height'])
                
                available_qualities = sorted(list(heights), reverse=True)
                self.finished.emit(available_qualities)
        except Exception as e:
            self.error.emit(str(e))


class VideoDownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.download_folder = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Video Downloader")
        self.setGeometry(100, 100, 750, 650)
        
        # Set default font for the application
        app_font = QFont("Inter", 10)
        QApplication.setFont(app_font)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Inter', 'Segoe UI', 'San Francisco', Arial, sans-serif;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #313244;
                border: 2px solid #45475a;
                border-radius: 8px;
                padding: 14px;
                color: #cdd6f4;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #89b4fa;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
            QPushButton:pressed {
                background-color: #89dceb;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            QComboBox {
                background-color: #313244;
                border: 2px solid #45475a;
                border-radius: 8px;
                padding: 12px;
                color: #cdd6f4;
                font-size: 14px;
            }
            QComboBox:hover {
                border: 2px solid #89b4fa;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #cdd6f4;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
                border: 2px solid #45475a;
                border-radius: 8px;
                padding: 5px;
            }
            QRadioButton {
                color: #cdd6f4;
                font-size: 14px;
                spacing: 10px;
            }
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #313244;
                border: 2px solid #45475a;
                border-radius: 10px;
            }
            QRadioButton::indicator:checked {
                background-color: #89b4fa;
                border: 2px solid #89b4fa;
                border-radius: 10px;
            }
            QRadioButton::indicator:checked::after {
                background-color: #1e1e2e;
                width: 8px;
                height: 8px;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(18)
        layout.setContentsMargins(35, 35, 35, 35)

        # Title
        title = QLabel("🎬 Video Downloader")
        title_font = QFont("Inter", 26, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #89b4fa; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # URL Input Section
        self.url_label = QLabel("Video URL:")
        url_label_font = QFont("Inter", 13, QFont.DemiBold)
        self.url_label.setFont(url_label_font)
        self.url_label.setStyleSheet("font-size: 15px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(self.url_label)

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Paste YouTube or video URL here...")
        layout.addWidget(self.url_input)

        # Fetch Quality Button
        self.fetch_quality_button = QPushButton('🔍 Fetch Available Qualities', self)
        self.fetch_quality_button.clicked.connect(self.fetch_qualities)
        layout.addWidget(self.fetch_quality_button)

        # Download Type Selection
        type_label = QLabel("Download Type:")
        type_label_font = QFont("Inter", 13, QFont.DemiBold)
        type_label.setFont(type_label_font)
        type_label.setStyleSheet("font-size: 15px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(type_label)

        self.button_group = QButtonGroup(self)
        self.video_and_audio_radio = QRadioButton("🎥 Video + Audio", self)
        self.sound_only_radio = QRadioButton("🎵 Audio Only", self)
        
        self.video_and_audio_radio.setChecked(True)
        self.button_group.addButton(self.video_and_audio_radio)
        self.button_group.addButton(self.sound_only_radio)
        
        self.sound_only_radio.toggled.connect(self.on_type_changed)

        type_layout = QHBoxLayout()
        type_layout.addWidget(self.video_and_audio_radio)
        type_layout.addWidget(self.sound_only_radio)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Video Quality Selection
        self.quality_label = QLabel("Video Quality:")
        quality_label_font = QFont("Inter", 13, QFont.DemiBold)
        self.quality_label.setFont(quality_label_font)
        self.quality_label.setStyleSheet("font-size: 15px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(self.quality_label)

        self.quality_combobox = QComboBox(self)
        self.quality_combobox.addItem("Click 'Fetch Available Qualities' first")
        self.quality_combobox.setEnabled(False)
        layout.addWidget(self.quality_combobox)

        # Download Location
        location_label = QLabel("Download Location:")
        location_label_font = QFont("Inter", 13, QFont.DemiBold)
        location_label.setFont(location_label_font)
        location_label.setStyleSheet("font-size: 15px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(location_label)

        location_layout = QHBoxLayout()
        self.folder_path_label = QLabel("No folder selected")
        self.folder_path_label.setStyleSheet("font-size: 13px; color: #f38ba8; font-style: italic;")
        
        self.download_location_button = QPushButton('📁 Select Folder', self)
        self.download_location_button.setStyleSheet("""
            QPushButton {
                background-color: #f9e2af;
                color: #1e1e2e;
            }
            QPushButton:hover {
                background-color: #f5c2e7;
            }
        """)
        self.download_location_button.clicked.connect(self.select_folder)
        
        location_layout.addWidget(self.folder_path_label, 1)
        location_layout.addWidget(self.download_location_button)
        layout.addLayout(location_layout)

        # Status and File Size
        self.status_label = QLabel('')
        self.status_label.setStyleSheet("font-size: 14px; color: #89b4fa; margin-top: 12px;")
        layout.addWidget(self.status_label)

        self.file_size_label = QLabel('')
        self.file_size_label.setStyleSheet("font-size: 13px; color: #a6e3a1;")
        layout.addWidget(self.file_size_label)

        # Circular Progress Bar
        progress_container = QHBoxLayout()
        progress_container.addStretch()
        self.progress_bar = CircularProgressBar(self)
        progress_container.addWidget(self.progress_bar)
        progress_container.addStretch()
        layout.addLayout(progress_container)

        # Download Button
        self.download_button = QPushButton('⬇️  Download', self)
        download_btn_font = QFont("Inter", 14, QFont.Bold)
        self.download_button.setFont(download_btn_font)
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
                font-size: 16px;
                padding: 16px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
        """)
        self.download_button.clicked.connect(self.download_video)
        layout.addWidget(self.download_button)

        layout.addStretch()
        self.setLayout(layout)

    def on_type_changed(self):
        """Enable/disable quality selection based on download type"""
        if self.sound_only_radio.isChecked():
            self.quality_combobox.setEnabled(False)
            self.quality_label.setStyleSheet("font-size: 15px; font-weight: 600; margin-top: 10px; color: #6c7086;")
        else:
            if self.quality_combobox.count() > 1:
                self.quality_combobox.setEnabled(True)
            self.quality_label.setStyleSheet("font-size: 15px; font-weight: 600; margin-top: 10px;")

    def fetch_qualities(self):
        """Fetch available video qualities"""
        url = self.url_input.text().strip()
        
        if not url:
            self.status_label.setText("⚠️  Please enter a URL first")
            self.status_label.setStyleSheet("font-size: 14px; color: #f38ba8;")
            return
        
        self.status_label.setText("🔄 Fetching available qualities...")
        self.status_label.setStyleSheet("font-size: 14px; color: #89b4fa;")
        self.fetch_quality_button.setEnabled(False)
        self.fetch_quality_button.setText("⏳ Fetching...")
        
        # Start quality fetch in separate thread
        self.fetch_thread = QualityFetchThread(url)
        self.fetch_thread.finished.connect(self.on_qualities_fetched)
        self.fetch_thread.error.connect(self.on_fetch_error)
        self.fetch_thread.start()

    def on_qualities_fetched(self, qualities):
        """Handle successfully fetched qualities"""
        self.fetch_quality_button.setEnabled(True)
        self.fetch_quality_button.setText("🔍 Fetch Available Qualities")
        
        self.quality_combobox.clear()
        
        if qualities:
            self.quality_combobox.addItem("Select Quality")
            for quality in qualities:
                self.quality_combobox.addItem(f"{quality}p")
            
            if not self.sound_only_radio.isChecked():
                self.quality_combobox.setEnabled(True)
            
            self.status_label.setText(f"✅ Found {len(qualities)} quality options")
            self.status_label.setStyleSheet("font-size: 14px; color: #a6e3a1;")
        else:
            self.quality_combobox.addItem("No qualities found")
            self.status_label.setText("⚠️  No video qualities found")
            self.status_label.setStyleSheet("font-size: 14px; color: #f38ba8;")

    def on_fetch_error(self, error_msg):
        """Handle quality fetch errors"""
        self.fetch_quality_button.setEnabled(True)
        self.fetch_quality_button.setText("🔍 Fetch Available Qualities")
        self.status_label.setText(f"❌ Error: {error_msg}")
        self.status_label.setStyleSheet("font-size: 14px; color: #f38ba8;")

    def select_folder(self):
        """Select download folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_folder = folder
            self.folder_path_label.setText(f"📂 {folder}")
            self.folder_path_label.setStyleSheet("font-size: 13px; color: #a6e3a1;")
        else:
            self.download_folder = None
            self.folder_path_label.setText("No folder selected")
            self.folder_path_label.setStyleSheet("font-size: 13px; color: #f38ba8; font-style: italic;")

    def download_video(self):
        """Start video download"""
        url = self.url_input.text().strip()

        self.status_label.setText('')
        self.file_size_label.setText('')
        self.progress_bar.setValue(0)

        if not url:
            self.status_label.setText("⚠️  Please enter a valid URL")
            self.status_label.setStyleSheet("font-size: 14px; color: #f38ba8;")
            return

        if not self.download_folder:
            self.status_label.setText("⚠️  Please select a download location")
            self.status_label.setStyleSheet("font-size: 14px; color: #f38ba8;")
            return

        if not self.sound_only_radio.isChecked() and self.quality_combobox.currentIndex() == 0:
            self.status_label.setText("⚠️  Please select a quality option")
            self.status_label.setStyleSheet("font-size: 14px; color: #f38ba8;")
            return

        try:
            download_options = {
                'outtmpl': f'{self.download_folder}/%(title)s.%(ext)s',
                'progress_hooks': [self.show_progress],
                'quiet': False,
                'no_warnings': False,
            }

            if self.sound_only_radio.isChecked():
                download_options['format'] = 'bestaudio/best'
                download_options['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            else:
                selected_quality = self.quality_combobox.currentText().replace("p", "")
                download_options['format'] = f'bestvideo[height<={selected_quality}]+bestaudio/best[height<={selected_quality}]'

            with youtube_dl.YoutubeDL(download_options) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', 'Unknown')
                
                self.status_label.setText(f"🎬 {video_title}")
                self.status_label.setStyleSheet("font-size: 14px; color: #89b4fa;")
                
                ydl.download([url])
                
                self.status_label.setText(f"✅ Downloaded: {video_title}")
                self.status_label.setStyleSheet("font-size: 14px; color: #a6e3a1;")

        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("font-size: 14px; color: #f38ba8;")
            self.progress_bar.setValue(0)

    def show_progress(self, d):
        """Update progress bar during download"""
        if d['status'] == 'downloading':
            # Try to get percentage directly first
            if '_percent_str' in d:
                # Parse percentage string like "50.0%"
                percent_str = d['_percent_str'].strip().replace('%', '')
                try:
                    percent = float(percent_str)
                    self.progress_bar.setValue(int(percent))
                except:
                    pass
            
            # Show download info
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed')
            
            if total > 0:
                percent = int((downloaded / total) * 100)
                self.progress_bar.setValue(percent)
                
                speed_text = f" at {self.format_size(speed)}/s" if speed else ""
                self.file_size_label.setText(f"📊 {self.format_size(downloaded)} / {self.format_size(total)}{speed_text}")
            elif downloaded > 0:
                # If we don't have total, just show downloaded amount
                speed_text = f" at {self.format_size(speed)}/s" if speed else ""
                self.file_size_label.setText(f"📊 {self.format_size(downloaded)}{speed_text}")
                
        elif d['status'] == 'finished':
            self.progress_bar.setValue(100)
            self.file_size_label.setText("✅ Merging video and audio...")

    def format_size(self, size):
        """Convert bytes to human-readable format"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 ** 3:
            return f"{size / (1024 ** 2):.2f} MB"
        else:
            return f"{size / (1024 ** 3):.2f} GB"


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoDownloaderApp()
    ex.show()
    sys.exit(app.exec_())