import sys

from PyQt5.QtGui import QIcon,QGuiApplication
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt,QCoreApplication

from qfluentwidgets import SplitFluentWindow, FluentIcon, setTheme, Theme, setThemeColor
from First_page import FirstPage
from Second_page import SecondPage


class Toolbox(SplitFluentWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('ToolBox')
        self.setWindowIcon(QIcon('ui/logo.ico'))
        self.firstPage = FirstPage(self)
        self.addSubInterface(self.firstPage,FluentIcon.DOCUMENT,'PDF处理')
        
        self.secondPage = SecondPage(self)
        self.addSubInterface(self.secondPage,FluentIcon.PHOTO,'图片转换')

#############################################################

#########################
setThemeColor('')
setTheme(Theme.AUTO)

QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)#高dpi
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
app = QApplication(sys.argv)
tb = Toolbox()
tb.resize(400,300)
tb.show()
app.exec_()
#########################
