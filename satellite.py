import logging
from ftdi import *
from PyQt4 import QtGui
from PyQt4 import QtCore

BAUDRATE = 38400
FILENAME = 'satellite.log'
LENGTH = 1024

class MamiThread(QtCore.QThread):
    def __init__(self, parent, ftdic):
        QtCore.QThread.__init__(self, parent)
        self.ftdic = ftdic
        self.running = True
        handler = logging.FileHandler(FILENAME)
        self.logger = logging.getLogger('Mamitterm')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
    def run(self):
        self.buffer = ''
        while self.running:
            temp = ' ' * LENGTH
            ftdi_read_data(self.ftdic, temp, LENGTH)
            temp = temp.rstrip()
            self.buffer += temp
            if temp != '':
                self.logger.debug(self.buffer)
                self.emit(QtCore.SIGNAL('read(QString)'), self.buffer)
                self.buffer = ''

class Mamitterm(QtGui.QWidget):
    def __init__(self, ftdic):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle('Mamitterm')
        self.connect(self, QtCore.SIGNAL('destroyed()'), self.destroy)
        self.ftdic = ftdic
        vbox = QtGui.QVBoxLayout()
        self.text = QtGui.QTextEdit(self)
        self.text.setReadOnly(True)
        self.line = QtGui.QLineEdit(self)
        self.connect(self.line, QtCore.SIGNAL('returnPressed()'), self.write)
        vbox.addWidget(self.text)
        vbox.addWidget(self.line)
        self.setLayout(vbox)
        self.thread = MamiThread(self, ftdic)
        self.connect(self.thread, QtCore.SIGNAL('read(QString)'), self.read)
        self.thread.start()

    def read(self, buf):
        self.text.append(buf)

    def write(self):
        text = str(self.line.text()) + chr(0x0d)
        size = len(text)
        ftdi_write_data(self.ftdic, text, size)
        self.line.setText('')

    def closeEvent(self, event):
        self.thread.running = False
        self.thread.quit()

def main():
    ftdic = ftdi_new()
    if ftdi_init(ftdic) < 0:
        raise RuntimeError, 'init error'
    if ftdi_usb_open(ftdic, 0x0403, 0x6001) < 0:
        raise RuntimeError, 'open error'
    ftdi_set_baudrate(ftdic, BAUDRATE)
    app = QtGui.QApplication(sys.argv)
    mamitterm = Mamitterm(ftdic)
    mamitterm.show()
    app.exec_()
    if ftdi_usb_close(ftdic) < 0:
        raise RuntimeError, 'close error'
    ftdi_deinit(ftdic)

if __name__ == '__main__':
    main()
