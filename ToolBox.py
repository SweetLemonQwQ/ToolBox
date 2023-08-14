from PySide2.QtGui import QCursor, QIcon
from PySide2.QtCore import Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QFileDialog, QMessageBox
from io import BytesIO
import fitz
from PIL import Image


# PDF处理
def pdf_compress(_pdf, _out, _dpi, _type="png", method=0):
    tb.window.setCursor(QCursor(Qt.WaitCursor))
    merges = []
    _file = None
    with fitz.open(_pdf) as doc:
        total = len(list(enumerate(doc.pages(), start=0)))
        tb.window.progressBar.setRange(0, total)
        for i, page in enumerate(doc.pages(), start=0):
            img = page.get_pixmap(dpi=_dpi)  # 将PDF页面转化为图片
            img_bytes = img.pil_tobytes(format=_type)  # 将图片转为为bytes对象
            image = Image.open(BytesIO(img_bytes))  # 将bytes对象转为PIL格式的图片对象
            if i == 0:
                _file = image  # 取第一张图片用于创建PDF文档的首页
            pix: Image.Image = image.quantize(
                colors=256, method=method).convert('RGB')  # 单张图片压缩处理
            merges.append(pix)  # 组装pdf
            tb.window.progressBar.setValue(i + 1)
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

    QMessageBox.information(tb.window,
                            'PDF操作',
                            '压缩完成！')
    tb.window.progressBar.setValue(0)
    tb.window.setCursor(QCursor(Qt.ArrowCursor))
    return



# ICO转换
def convert_image(input_path, output_path):
    # if input_path and output_path:          #判断参数是否都存在
    # 判断是否自定义输出路径
    if output_path == '':
        image = Image.open(input_path)  # 通过路径读取图片
        # 保存到输出路径 ，并且格式为 “ICO”，大小为32X32
        image.save(output_path, format='ICO', sizes=[(32, 32)])
    else:
        image = Image.open(input_path)  # 通过路径读取图片
        # 保存到输出路径 ，并且格式为 “ICO”，大小为32X32
        image.save(output_path, format='ICO', sizes=[(32, 32)])
    QMessageBox.information(tb.window,
                            'PDF操作',
                            '压缩完成！')


class Toolbox:
    def __init__(self):
        self.window = QUiLoader().load('ui/tb.ui')  # 从文件中加载UI定义,动态创建一个相应的窗口对象
        self.window.setWindowIcon(QIcon('ui/logo.ico'))
        # 注意：里面的控件对象也成为窗口对象的属性了
        # 比如 self.ui.button , self.ui.textEdit
        self.window.in_path.clicked.connect(pdf.onInpath)
        self.window.out_path.clicked.connect(pdf.onOutpath)
        self.window.start_button.clicked.connect(pdf.onStart)
        self.window.choice_buttonGroup.buttonClicked.connect(pdf.onChoice)
        self.window.custom_dpi.textChanged.connect(pdf.onTextChange)

        #self.window.in_path_ico.clicked.connect(ico.onInpath)
        #self.window.out_path_ico.clicked.connect(ico.onOutpath)
        #self.window.start_button_ico.clicked.connect(ico.onStart)
#####################################################
class Pdf:
    filePathIn = ''
    filePathOut = ''
    fileName = ''
    _dpi = 150

    # 读入文件
    def onInpath(self):
        self.filePathIn, fileClass = QFileDialog.getOpenFileName(
            tb.window,  # 父窗口对象
            "选择要压缩的PDF",  # 标题
            r"c:\\",  # 起始目录
            "PDF文件 (*.pdf)"  # 选择类型过滤项，过滤内容在括号中
        )
        # print(fileClass)
        if self.filePathIn == '' or fileClass != 'PDF文件 (*.pdf)':
            return
        tb.window.in_path_text.setPlainText('已选择文件:\n' + self.filePathIn)

    # 输出文件

    def onOutpath(self):
        self.filePathOut = QFileDialog.getExistingDirectory(
            tb.window,
            "选择存储路径")
        tb.window.out_path_text.setPlainText('已选择目录:\n' + self.filePathOut)

    # 点击开始

    def onStart(self):
        if self.filePathIn == '' or self._dpi == '':
            QMessageBox.warning(tb.window,
                                '警告',
                                '文件未选择')
            return
        if self._dpi > 600 or self._dpi < 72:
            QMessageBox.warning(tb.window,
                                '警告',
                                '设定的范围超出阈值')
            return
        pdf_compress(self.filePathIn, self.filePathOut, self._dpi)

    # 选择dpi

    def onChoice(self):
        choiceId = tb.window.choice_buttonGroup.checkedId()
        # print(choiceId)
        if choiceId == -2:
            self._dpi = 300
        elif choiceId == -3:
            self._dpi = 200
        elif choiceId == -4:
            self._dpi = 150
        elif choiceId == -5:
            self._dpi = int(tb.window.custom_dpi.text())
        # print(self._dpi)
        return

    # 自定义dpi

    def onTextChange(self):
        tb.window.choice_buttonGroup.button(-5).click()
        return

#############################################################
class Ico:
    filePathIn = ''
    filePathOut = ''

    # 读入文件
    def onInpath(self):
        self.filePathIn, _ = QFileDialog.getOpenFileName(
            tb.window,  # 父窗口对象
            "选择要压缩的PDF",  # 标题
            r"d:\\",  # 起始目录
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"  # 选择类型过滤项，过滤内容在括号中
        )
        if self.filePathIn == '':
            return
        tb.window.in_path_text_ico.setPlainText('已选择文件:\n' + self.filePathIn)

    # 输出文件
    def onOutpath(self):
        self.filePathOut = QFileDialog.getExistingDirectory(
            tb.window,
            "选择存储路径")
        tb.window.out_path_text_ico.setPlainText('已选择目录:\n' + self.filePathOut)

    # 点击开始
    def onStart(self):
        if self.filePathIn == '':
            QMessageBox.warning(tb.window,
                                '警告',
                                '文件未选择')
            return
        convert_image(self.filePathIn, self.filePathOut)


#########################
app = QApplication([])  #

pdf = Pdf()             #
ico = Ico()             #
tb = Toolbox()          #

tb.window.show()        #
app.exec_()             #
#########################
