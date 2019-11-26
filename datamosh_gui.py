import os
import sys
import threading
from PyQt5.QtGui import *
from PyQt5.QtCore import QDateTime, Qt, QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QDialog, QFileDialog, QGridLayout,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QPushButton, QSizePolicy, QSpinBox,
                             QStyleFactory, QTabWidget, QTextEdit, QPlainTextEdit,
                             QVBoxLayout, QWidget)
from config import APP_NAME, APP_VERSION, ABOUT_TEXT
from components import DatamoshThreadHandler, LogGui

class DatamoshDialog(QDialog):
    def __init__(self, parent=None):
        super(DatamoshDialog, self).__init__(parent)
        QApplication.setStyle(QStyleFactory.create('windows'))
        self.setWindowTitle(APP_NAME)
        self._createInputGroupBox()
        self.main_button = QPushButton('COMMENCE MOSH')
        self.about_button = QPushButton('ABOUT MOSHUA')
        self.main_button.show()
        self.main_button.clicked.connect(self._on_datamosh_clicked)
        self.about_button.show()
        self.about_button.clicked.connect(self._on_about_clicked)
        self.logGui = LogGui() # Custom Text 'EDIT' for directing yaspin output
        mainLayout = QGridLayout()
        self.setLayout(mainLayout)
        mainLayout.addWidget(self.inputGroupBox, 0, 0, 1, 2) #, 2, 1)
        mainLayout.addWidget(self.main_button, 1, 1, 1, 1)
        mainLayout.addWidget(self.about_button, 1, 0, 1, 1)
        mainLayout.addWidget(self.logGui, 2, 0, 1, 0) # 2010
        self.output_dir = 'moshed_videos'

    def _on_about_clicked(self, e):
        alert = QMessageBox()
        alert.setWindowTitle('ABOUT MOSHUA')
        alert.setText(ABOUT_TEXT)
        alert.exec()

    def _on_input_video_clicked(self, e):
        vid_filter = ("Videos ( *.mp4 *m4p *m4v *.ogv *.ogg *.mov *.qt *.mpg"
                     " *.mp2 *.mpeg *.mpe *.mpv *.flv *.swf')")
        qt_file_path, _ = QFileDialog().getOpenFileName(self, 'Select Video File', 
                                                        './', filter=vid_filter,
                                                        options=QFileDialog.DontUseNativeDialog)    
                                                        # GTK WARNING REMOVED BY options ABOVE
        self.file_path = qt_file_path
        file_name = os.path.splitext(os.path.basename(qt_file_path))[0]
        self.inputButton.setText(file_name)
        print('INPUT FILE:')
        print(self.file_path)

    def _on_output_dir_clicked(self, e):
        p = QFileDialog.getExistingDirectory(self,'Select Export Directory','./',
                                             options=QFileDialog.DontUseNativeDialog)
        if not p: return
        self.output_dir = p
        t = p.split('/')[-1]
        self.outputButton.setText(t)
        print('OUTPUT DIR:')
        print(p)

    def _on_datamosh_clicked(self, e):
        if not 'file_path' in self.__dict__:
            alert = QMessageBox()
            alert.setText('You must select a video to datamosh')
            alert.setWindowTitle('MOSHUA WARNING!')
            alert.exec()
            return
        # turn off most (but not all) of the ui while running datamosh
        # probably only need just one thread... and just start and join like we are doing in the handler
        waiting_thread = threading.Thread(name='wait_on_datamosh',
                                          target=DatamoshThreadHandler,
                                          args = (self,))
        waiting_thread.start()
        # we don't join on this thread. It joins on the sub thread created
        # it allows UI to recieve output from the script
   
    
    ## CREATE THE INPUTS GUI
    def _createInputGroupBox(self):
        self.inputGroupBox = QGroupBox("Inputs")
        inputFileLabel = QLabel('INPUT VIDEO') # opens a dialog select
        self.inputButton = QPushButton('select video')
        self.inputButton.clicked.connect(self._on_input_video_clicked) # CONNECTION 
        
        clipStartLabel = QLabel('START OF CLIP')
        self.clipStartBox = QSpinBox(self.inputGroupBox)
        self.clipStartBox.setValue(0)
        clipEndLabel = QLabel('END OF CLIP')
        self.clipEndBox = QSpinBox(self.inputGroupBox)
        self.clipEndBox.setValue(5)
        moshStartLabel = QLabel('START OF MOSH')
        self.moshStartBox = QSpinBox(self.inputGroupBox)
        self.moshStartBox.setValue(1)
        moshLengthLabel = QLabel('END OF MOSH')
        self.moshLengthBox = QSpinBox(self.inputGroupBox)
        self.moshLengthBox.setValue(5)
        pFramesLabel = QLabel("P-PHRAMES / BLOOM")
        self.p_frames = QSpinBox(self.inputGroupBox)
        self.p_frames.setValue(5)
        sizeLabel = QLabel("VIDEO WIDTH")
        # these boxes do have a max property -- hacked lineedit below 'sizeBox'
        self.size = QLineEdit('480')
        #TODO: OUTPUT DIRECTORY NOT IMPLEMENTED
        outputFileLabel = QLabel("OUTPUT DIR") ## NEED A DIR SELECT FOR THIS...
        self.outputButton = QPushButton('moshed_videos')
        self.outputButton.clicked.connect(self._on_output_dir_clicked)
        
        layout = QGridLayout()
        layout.addWidget(inputFileLabel, 0, 0, 1, 1)
        layout.addWidget(self.inputButton, 0, 1, 1, 1)
        layout.addWidget(clipStartLabel, 1, 0, 1, 1)
        layout.addWidget(self.clipStartBox, 1, 1, 1, 1)
        layout.addWidget(clipEndLabel, 2, 0, 1, 1)
        layout.addWidget(self.clipEndBox, 2, 1, 1, 1)
        layout.addWidget(moshStartLabel, 3, 0, 1, 1)
        layout.addWidget(self.moshStartBox, 3, 1, 1, 1)
        layout.addWidget(moshLengthLabel, 4, 0, 1, 1)
        layout.addWidget(self.moshLengthBox, 4, 1, 1, 1)
        layout.addWidget(pFramesLabel, 5, 0, 1, 1)
        layout.addWidget(self.p_frames, 5, 1, 1, 1)
        layout.addWidget(sizeLabel, 6, 0, 1, 1)
        layout.addWidget(self.size, 6, 1, 1, 1)
        layout.addWidget(outputFileLabel, 7, 0, 1, 1)
        layout.addWidget(self.outputButton, 7, 1, 1, 1)
        self.inputGroupBox.setLayout(layout)


### APP ENTRY POINT
if __name__ == '__main__':
    app = QApplication(sys.argv) # we have access to vars here 8-0
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    app_icon = QIcon()
    app_icon.addFile('gui/MOSHUA.png')
    app.setWindowIcon(app_icon)
    main = DatamoshDialog()
    main.show()
    main.setMaximumWidth(main.width())
    main.setMaximumHeight(main.height())
    sys.exit(app.exec_())
