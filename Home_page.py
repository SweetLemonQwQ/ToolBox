from PyQt5.QtWidgets import QWidget


from Ui_home import Ui_HomePage

from ver import VER


class HomePage(QWidget,Ui_HomePage):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        
        self.ver.setText(f'<html><head/><body><p align="right"><span style=" font-size:6pt; color:#808080;">Ver:{VER}</span></p></body></html>')
        self.SwitchButton.setOnText('打开')
        self.SwitchButton.setOffText('关闭')
        

    