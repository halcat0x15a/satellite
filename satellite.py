import time
from ctypes import *
from ftdi import *
from PyQt4 import QtGui
from PyQt4 import QtCore

TIME = 1

BAUDRATE = 38400

class MamiThread(QtCore.QThread):
    def __init__(self, parent, ftdic):
        QtCore.QThread.__init__(self, parent)
        self.ftdic = ftdic
        self.running = True
    def run(self):
        while self.running:
            buf = ' ' * 1024
            ftdi_read_data(self.ftdic, buf, len(buf))
            buf = buf.strip()
            if buf != "":
                self.emit(QtCore.SIGNAL('read(QString)'), buf)

class Mamitterm(QtGui.QWidget):
    def __init__(self, ftdic):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle('Mikutterm')
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
        text = str(self.line.text())
        size = len(text)
        ftdi_write_data(self.ftdic, text, size)

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
    mamitterm.thread.running = False
    mamitterm.thread.quit()
    if ftdi_usb_close(ftdic) < 0:
        raise RuntimeError, 'close error'
    ftdi_deinit(ftdic)

if __name__ == '__main__':
    main()
