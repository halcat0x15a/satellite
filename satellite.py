import logging
import binascii
from ftdi import *
from PyQt4 import QtGui
from PyQt4 import QtCore
import Image
import StringIO

BAUDRATE = 38400
FILENAME = 'satellite.log'
LENGTH = 1024
JPEGSTART = binascii.unhexlify('ffd8')
JPEGEND = binascii.unhexlify('ffd9')
TITLE = 'Mamitterm'

class MamiThread(QtCore.QThread):
    def __init__(self, parent, ftdic):
        QtCore.QThread.__init__(self, parent)
        self.ftdic = ftdic
        self.running = True
        handler = logging.FileHandler(FILENAME)
        self.logger = logging.getLogger(TITLE)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
    def run(self):
        self.buffer = ''
        self.writing = False
        while self.running:
            temp = ' ' * LENGTH
            r = ftdi_read_data(self.ftdic, temp, LENGTH)
            if r > 0:
                temp = temp[:r]
                start = temp.find(JPEGSTART)
                if start != -1:
                    print 'Start'
                    self.buffer = temp[start:]
                    self.writing = True
                elif self.writing:
                    end = temp.find(JPEGEND)
                    if end == -1:
                        self.buffer += temp
                    else:
                        print 'End'
                        data = (self.buffer + temp[:end + len(JPEGEND)]).replace(binascii.unhexlify('0d0a'), '')
                        f = open('foo.jpg', 'w')
                        f.write(data)
                        f.close()
                        try:
                            size = 160, 120
                            image = Image.fromstring('RGB', size, data)
                            image.save('bar.jpg')
                        except ValueError, e:
                            print e
                        try:
                            image = Image.open(StringIO.StringIO(data))
                            image.save('baz.jpg')
                        except IOError, e:
                            print e
                        self.writing = False
                self.emit(QtCore.SIGNAL('readText(QString)'), temp.strip())
                self.emit(QtCore.SIGNAL('readHex(QString)'), binascii.hexlify(temp))
                self.logger.debug(temp)

class Mamitterm(QtGui.QWidget):
    def __init__(self, ftdic):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle(TITLE)
        self.connect(self, QtCore.SIGNAL('destroyed()'), self.destroy)
        self.ftdic = ftdic
        self.text = QtGui.QTextEdit(self)
        self.text.setReadOnly(True)
        self.hex = QtGui.QTextEdit(self)
        self.hex.setReadOnly(True)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.text)
        hbox.addWidget(self.hex)
        self.line = QtGui.QLineEdit(self)
        self.connect(self.line, QtCore.SIGNAL('returnPressed()'), self.write)
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.line)
        self.setLayout(vbox)
        self.thread = MamiThread(self, ftdic)
        self.connect(self.thread, QtCore.SIGNAL('readText(QString)'), self.readText)
        self.connect(self.thread, QtCore.SIGNAL('readHex(QString)'), self.readHex)
        self.thread.start()

    def readText(self, buf):
        self.text.append(buf)

    def readHex(self, buf):
        self.hex.append(buf)

    def write(self):
        text = str(self.line.text()) + chr(0x0d)
        size = len(text)
        ftdi_write_data(self.ftdic, text, size)
        self.line.setText('')

    def keyPressEvent(self, event):
        text = event.text()
        if text == 'h':
            c = 'z'
        elif text == 'j':
            c = 'v'
        elif text == 'k':
            c = 'c'
        elif text == 'l':
            c = 'x'
        else:
            return
        string = c + chr(0x0d)
        ftdi_write_data(self.ftdic, string, len(string))

    def keyReleaseEvent(self, event):
        pass

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
