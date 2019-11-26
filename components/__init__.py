import re
import sys
from threading import Thread
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QTextEdit, QMessageBox 
from PyQt5.QtGui import QFontDatabase, QTextCursor
from config import APP_NAME
from datamosh_api import Datamosh


ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')


# Is this bad because the UI doesn't 'KNOW' when the thread has finished?
# It just acts like it. Which maybe is good enough.
# The alternative is to use pyqtSignals, but I used this before and saw no need
class DatamoshThreadHandler:
    """Shows a waiting mouse cursor and disables most of the ui until the datamosh thread completes
    This object is initialized/constructed as the target of a new thread started in the main GUI thread.
    It then creates another thread and waits for it to finish
    The target is the static run method of Datamosh api class.
    Why use these threads? So we can keep the output of the script in UI!
    Else the yaspin use in the API would need to be in UI, which perhaps it should.
    Either way it was fun to use threading. :)
    """
    def __init__(self, parent): # dependent on parent data
        QApplication.setOverrideCursor(Qt.WaitCursor)
        parent.inputGroupBox.setEnabled(False) 
        parent.main_button.setEnabled(False)
       
        datamosh_thread = Thread(name='datamosh',
                                 target=Datamosh.run,
                                 args=[parent.file_path,
                                       parent.clipStartBox.value(),
                                       parent.clipEndBox.value(),
                                       parent.moshStartBox.value(),
                                       parent.moshLengthBox.value(),
                                       parent.p_frames.value(), 
                                       parent.size.displayText(),
                                       parent.output_dir])
        datamosh_thread.start()
        datamosh_thread.join() # wait for datamosh to finish
        
        QApplication.restoreOverrideCursor()
        parent.inputGroupBox.setEnabled(True) 
        parent.main_button.setEnabled(True)
        
        ##### TODO: let user set whether they want to be alerted or not
        # alert = QMessageBox()
        # alert.setText('DATAMOSH COMPLETE')
        # alert.setWindowTitle(APP_NAME)
        # # alert.buttonClicked.connect(parent.logGui._clear_log_display)
        # alert.exec()


class EmittingStream(QObject):
    textWritten = pyqtSignal(str)
    textFlushed = pyqtSignal()

    def write(self, text):
        self.textWritten.emit(text)

    def isatty(self):
        return True
    
    def flush(self):
        try: self.textFlushed.emit()
        except: return # we know this fails on every exit...


# need to diasable typing and clicking in the box or use a different Widget
class LogGui(QTextEdit):
    def __init__(self, parent=None):
        super(LogGui, self).__init__(parent)
        self.everyother = 0
        # stdout -> Emitter -> callbacks update the gui text
        sys.stdout = EmittingStream(textWritten=self._on_log_updated,
                                    textFlushed=self._on_log_flushed)
        # not sure this is even working...?
        self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        #self.setFontPointSize(8) 
        self.document().setMaximumBlockCount(11)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setReadOnly(True) 
    
    def __del__(self):
        sys.stdout = sys.__stdout__  # Restore sys.stdout

    #overwrite events we want to hide for this logger
    def wheelEvent(self, event):
        return
    def mousePressEvent(self, event):
        return
    def mouseReleaseEvent(self, e):
        return
    def dragMoveEvent(self, e):
        return
    def dragEnterEvent(self, e):
        return
    def mouseMoveEvent(self, e):
        return
    def mouseDoubleClickEvent(self, e):
        return

    def _on_log_updated(self, text):
        """escapes ansi from terminal and puts its into Qt.
        Could be platform specific to linux"""
        #self.verticalScrollBar().hide() 
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        text = ansi_escape.sub('', text)
        cursor.insertText(text)
        self.setTextCursor(cursor)
        #self.ensureCursorVisible()
    
    def _on_log_flushed(self):
        """This does some fun hacky glitchy shit to make yaspin work from another
        script inside pyqt. Could be easier and better with a logger"""
        self.everyother += 1
        if not self.everyother % 2 == 0: return
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.EndOfLine, mode=QTextCursor.MoveAnchor)
        cursor.insertText("\n")
        cursor.movePosition(QTextCursor.Up, mode=QTextCursor.KeepAnchor, n=2)
        cursor.removeSelectedText()
        self.setTextCursor(cursor)

    ### May use later
    # def _clear_log_display(self):
    #     everyother = 0
    #     cursor = self.textCursor()
    #     cursor.movePosition(QTextCursor.Start, mode=QTextCursor.MoveAnchor)
    #     cursor.movePosition(QTextCursor.End, mode=QTextCursor.KeepAnchor)
    #     cursor.removeSelectedText()
    #     self.setTextCursor(cursor)
    
    
## Didn't need pyqtSignal for threading...
        # super(DatamoshCompletionResponse, self).__init__(parent)
    # job_completed = pyqtSignal() No need for signal Does it need to be a QObject?
        # Setup the signal-slot mechanism in instance method _handle_datamosh
        #self.job_completed.connect(self._on_datamosh_finished) 
        #self.job_completed.emit()

