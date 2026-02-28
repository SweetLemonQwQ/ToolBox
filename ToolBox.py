import sys

from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import FluentIcon, SplitFluentWindow, Theme, setTheme, setThemeColor

from First_page import FirstPage
from Home_page import HomePage
from Second_page import SecondPage
from Python_page import PythonPage


class Toolbox(SplitFluentWindow):
    """应用主窗口，负责组装各功能页面与主题切换。"""
    def __init__(self):
        """初始化窗口、侧边栏页面和主题依赖控件。"""
        super().__init__()

        self.setWindowTitle('ToolBox')
        self.setWindowIcon(QIcon('ui/logo.ico'))

        self.homePage = HomePage(self)
        self.addSubInterface(self.homePage, FluentIcon.HOME, '主页')

        self.firstPage = FirstPage(self)
        self.addSubInterface(self.firstPage, FluentIcon.DOCUMENT, 'PDF处理')

        self.secondPage = SecondPage(self)
        self.addSubInterface(self.secondPage, FluentIcon.PHOTO, '图片转换')

        self.pythonPage = PythonPage(self)
        self.addSubInterface(self.pythonPage, FluentIcon.DOCUMENT, 'Python版本与库管理')

        self._theme_text_widgets = [
            self.homePage.TitleLabel,
            self.homePage.TitleLabel_2,
            self.homePage.CaptionLabel,
            self.firstPage.in_path_text,
            self.firstPage.BodyLabel_3,
            self.firstPage.out_path_text,
            self.firstPage.custom_dpi_text,
            self.secondPage.in_path_text_ico,
            self.secondPage.BodyLabel,
            self.secondPage.out_path_text_ico,
        ]

        self.homePage.SwitchButton.checkedChanged.connect(self.onSwitch)

    def _apply_text_color(self, color: QColor):
        """统一更新主题相关文本控件颜色。"""
        for widget in self._theme_text_widgets:
            widget.setTextColor(color)

    def apply_theme_by_switch(self, is_dark: bool):
        """根据开关状态应用明/暗主题。"""
        setTheme(Theme.DARK if is_dark else Theme.LIGHT)
        self._apply_text_color(QColor(0, 0, 0) if is_dark else QColor(96, 96, 96))

    def onSwitch(self):
        """处理主题开关事件并刷新界面样式。"""
        is_dark = self.homePage.SwitchButton.getText() == '打开'
        self.apply_theme_by_switch(is_dark)


setThemeColor('')
setTheme(Theme.AUTO)

QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
app = QApplication(sys.argv)
tb = Toolbox()
tb.resize(400, 300)
tb.show()
app.exec_()
