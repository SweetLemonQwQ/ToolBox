from io import BytesIO
from threading import Thread

from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox,QWidget,QProgressBar
from PyQt5.QtCore import pyqtSignal,QObject

from Ui_fst import Ui_FirstPage
from qfluentwidgets import FluentIcon

import fitz
from PIL import Image
from ver import VER


# 自定义信号源对象类型，一定要继承自 QObject
class ProgressSignals(QObject):

    # 定义一种信号，两个参数 类型分别是： QTextBrowser 和 字符串
    # 调用 emit方法 发信号时，传入参数 必须是这里指定的 参数类型
    progress_print = pyqtSignal(QProgressBar,float)
    info_box = pyqtSignal()



#窗体部分
class FirstPage(QWidget,Ui_FirstPage):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.signal = ProgressSignals()

        self.in_path.setIcon(FluentIcon.FOLDER)
        self.out_path.setIcon(FluentIcon.SAVE_AS)
        self.start_button.setIcon(FluentIcon.PLAY)
        self.ver.setText(f'<html><head/><body><p align="right"><span style=" font-size:6pt; color:#808080;">Ver:{VER}</span></p></body></html>')
        self.in_path.clicked.connect(self.onInpath)  # 读入文件
        self.out_path.clicked.connect(self.onOutpath)  # 输出文件
        self.start_button.clicked.connect(self.onStart)  # 开始
        self.custom_dpi.sliderMoved.connect(self.onTextChange)  # 自定义
        self.signal.progress_print.connect(self.updateBar)
        self.signal.info_box.connect(self.infoBox)

#####################################################
#功能部分
    filePathIn = ''
    filePathOut = ''
    fileName = ''
    _dpi = 150


    # PDF处理
    def updateBar(self,bar,step):
        bar.setVal(float(step))
        return
    
    def infoBox(self):
        #infoBar = InfoBarManager()
        #infoBar.make(InfoBarPosition.TOP)
        #infoBar.add(info_bar.InfoBar(icon=InfoBarIcon.SUCCESS,title='PDF操作',content='完成'))
        
        QMessageBox.information(self,
                                'PDF操作',
                                '压缩完成！')
        self.progressBar.setVal(0)
        self.setCursor(QCursor(Qt.ArrowCursor))

    def pdf_compress(self,_pdf, _out, _dpi, _type="png", method=0):
        merges = []
        _file = None
        with fitz.open(_pdf) as doc:
            total = len(list(enumerate(doc.pages(), start=0)))
            for i, page in enumerate(doc.pages(), start=0):
                img = page.get_pixmap(dpi=_dpi)  # 将PDF页面转化为图片
                img_bytes = img.pil_tobytes(format=_type)  # 将图片转为为bytes对象
                image = Image.open(BytesIO(img_bytes))  # 将bytes对象转为PIL格式的图片对象
                if i == 0:
                    _file = image  # 取第一张图片用于创建PDF文档的首页
                pix: Image.Image = image.quantize(
                    colors=256, method=method).convert('RGB')  # 单张图片压缩处理
                merges.append(pix)  # 组装pdf

                self.signal.progress_print.emit(self.progressBar,((i + 1)/total)*100)
        
        # 判断是否自定义输出路径
        if _out == '':
            _file.save(f"{_pdf.rsplit('.')[0]}_in_{_dpi}dpi.pdf",  # 路径
                    "pdf",  # 用PIL自带的功能保存为PDF格式文件
                    save_all=True,
                    append_images=merges[1:])
        else:
            _file.save(f"{_out+'/'+_pdf.rsplit('.')[0].rsplit('/')[-1]}_in_{_dpi}dpi.pdf",  # 路径
                    "pdf",  # 用PIL自带的功能保存为PDF格式文件
                    save_all=True,
                    append_images=merges[1:])
        
        self.signal.info_box.emit()
        
        return
        

    # 读入文件
    def onInpath(self):
        self.filePathIn, fileClass = QFileDialog.getOpenFileName(
            self,  # 父窗口对象
            "选择要压缩的PDF",  # 标题
            r"c:\\",  # 起始目录
            "PDF文件 (*.pdf)"  # 选择类型过滤项，过滤内容在括号中
        )
        # print(fileClass)
        if self.filePathIn == '' or fileClass != 'PDF文件 (*.pdf)':
            return
        self.in_path_text.setText('已选择文件:\n' + self.filePathIn)


    # 输出文件
    def onOutpath(self):
        self.filePathOut = QFileDialog.getExistingDirectory(
            self,
            "选择存储路径")
        self.out_path_text.setText('已选择目录:\n' + self.filePathOut)


    # 点击开始
    def onStart(self):
        if self.filePathIn == '' or self._dpi == '':
            QMessageBox.warning(self,
                                '警告',
                                '文件未选择')
            return
        if self._dpi > 600 or self._dpi < 72:
            QMessageBox.warning(self,
                                '警告',
                                '设定的范围超出阈值')
            return
        self.setCursor(QCursor(Qt.WaitCursor))
        th = Thread(target=self.pdf_compress,args=(self.filePathIn, self.filePathOut, self._dpi))
        th.start()


    # 选择dpi
    def onChoice(self):
        choiceId = self.choice_buttonGroup.checkedId()
        # print(choiceId)
        if choiceId == -2:
            self._dpi = 300
        elif choiceId == -3:
            self._dpi = 200
        elif choiceId == -4:
            self._dpi = 150
        elif choiceId == -5:
            self._dpi = int(self.custom_dpi.text())
        # print(self._dpi)
        return


    # 自定义dpi
    def onTextChange(self):
        self._dpi = self.custom_dpi.value()
        self.custom_dpi_text.setText(f'{self._dpi} DPI')
        return

#############################################################
