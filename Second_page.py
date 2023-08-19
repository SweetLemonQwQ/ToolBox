from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox,QWidget

from Ui_sec import Ui_SecondPage
from qfluentwidgets import FluentIcon,PushButton

from PIL import Image

from ver import VER



class SecondPage(QWidget,Ui_SecondPage):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.in_path_ico.setIcon(FluentIcon.FOLDER)
        self.out_path_ico.setIcon(FluentIcon.SAVE_AS)
        self.start_button_ico.setIcon(FluentIcon.PLAY)
        self.ver.setText(f'<html><head/><body><p align="right"><span style=" font-size:6pt; color:#808080;">Ver:{VER}</span></p></body></html>')
        self.in_path_ico.clicked.connect(self.onInpath)
        self.out_path_ico.clicked.connect(self.onOutpath)
        self.start_button_ico.clicked.connect(self.onStart)
        self.type_buttonGroup.buttonClicked.connect(self.onChooseType)
        


        #self.in_path.setIcon(FluentIcon.FILTER)

#####################################################
#功能部分
    filePathIn = ''
    filePathOut = ''
    image: Image.Image
    outType = ''
        # 图片转换
    def convert_image(self,input_path, output_path, out_format, sizes=None):
        # if input_path and output_path:          #判断参数是否都存在
        
        if output_path == '':  # 不自定义
            if self.image.format == 'PNG' and (out_format == 'jpg' or out_format == 'jpeg'):
                # png->jpg
                # 转换图片模式
                self.image = self.image.convert('RGB')
            if out_format == 'ico':
                self.image.save(input_path.rsplit('.')[0] + '.' + out_format,format='self')
                pass
            self.image.save(input_path.rsplit('.')[0] + '.' + out_format)
        else:  # 自定义输出路径
            if self.image.format == 'PNG' and (out_format == 'jpg' or out_format == 'jpeg'):
                # png->jpg
                # 转换图片模式
                self.image = self.image.convert('RGB')
            if out_format == 'ico':
                self.image.save(output_path + '/' + input_path.rsplit('.')[0].rsplit('/')[-1] + '.' + out_format,format='self')
                pass
            self.image.save(output_path + '/' + input_path.rsplit('.')[0].rsplit('/')[-1] + '.' + out_format)
            # image.save(output_path, format='ICO', sizes=[(32, 32)])
            # 保存到输出路径 ，并且格式为 “ICO”，大小为32X32
        
        QMessageBox.information(self,
                                '图片转换',
                                '转换完成！')
        return


    # 读入文件

    def onInpath(self):
        self.filePathIn, _ = QFileDialog.getOpenFileName(
            self,  # 父窗口对象
            "选择要转换的图片",  # 标题
            r"c:\\",  # 起始目录
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"  # 选择类型过滤项，过滤内容在括号中
        )
        if self.filePathIn == '':
            return
        self.image = Image.open(self.filePathIn)  # 通过路径读取图片
        self.in_path_text_ico.setText('已选择文件:\n' + self.filePathIn)

    # 输出文件

    def onOutpath(self):
        self.filePathOut = QFileDialog.getExistingDirectory(
            self,
            "选择存储路径")
        self.out_path_text_ico.setText('已选择目录:\n' + self.filePathOut)

    # 选择输出类型
    def onChooseType(self):
        choiceId = self.type_buttonGroup.checkedId()
        print(choiceId)
        if choiceId == -2:
            self.outType = 'jpg'
        elif choiceId == -3:
            self.outType = 'gif'
        elif choiceId == -4:
            self.outType = 'jpeg'
        elif choiceId == -5:
            self.outType = 'bmp'
        elif choiceId == -6:
            self.outType = 'png'
        elif choiceId == -7:
            self.outType = 'ico'
        return

    # 点击开始
    def onStart(self):
        if self.filePathIn == '':
            QMessageBox.warning(self,
                                '警告',
                                '文件未选择')
            return
        self.convert_image(self.filePathIn, self.filePathOut, self.outType)