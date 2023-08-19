import sys

from PyQt5.QtGui import QIcon,QGuiApplication,QColor
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt,QCoreApplication

from qfluentwidgets import SplitFluentWindow, FluentIcon, setTheme, Theme, setThemeColor,label
from First_page import FirstPage
from Second_page import SecondPage
from Home_page import HomePage


class Toolbox(SplitFluentWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('ToolBox')
        self.setWindowIcon(QIcon('ui/logo.ico'))

        self.homePage = HomePage(self)
        self.addSubInterface(self.homePage,FluentIcon.HOME,'主页')

        self.firstPage = FirstPage(self)
        self.addSubInterface(self.firstPage,FluentIcon.DOCUMENT,'PDF处理')
        
        self.secondPage = SecondPage(self)
        self.addSubInterface(self.secondPage,FluentIcon.PHOTO,'图片转换')


        self.homePage.SwitchButton.checkedChanged.connect(self.onSwitch)
    
    def onSwitch(self):
        mode = self.homePage.SwitchButton.getText()
        if mode == '打开':
            setTheme(Theme.DARK)
            self.homePage.TitleLabel.setTextColor(QColor(0, 0, 0))
            self.homePage.TitleLabel_2.setTextColor(QColor(0, 0, 0))
            self.homePage.CaptionLabel.setTextColor(QColor(0, 0, 0))

            self.firstPage.in_path_text.setTextColor(QColor(0, 0, 0))
            self.firstPage.BodyLabel_3.setTextColor(QColor(0, 0, 0))
            self.firstPage.out_path_text.setTextColor(QColor(0, 0, 0))
            self.firstPage.custom_dpi_text.setTextColor(QColor(0, 0, 0))

            self.secondPage.in_path_text_ico.setTextColor(QColor(0, 0, 0))
            self.secondPage.BodyLabel.setTextColor(QColor(0, 0, 0))
            self.secondPage.out_path_text_ico.setTextColor(QColor(0, 0, 0))
            
        else:
            setTheme(Theme.LIGHT)
        return
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
