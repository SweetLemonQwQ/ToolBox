from pathlib import Path

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget

from Ui_sec import Ui_SecondPage
from qfluentwidgets import FluentIcon

from PIL import Image

from ver import VER


class SecondPage(QWidget, Ui_SecondPage):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.filePathIn = ''
        self.filePathOut = ''
        self.outType = ''
        self.image: Image.Image | None = None

        self.in_path_ico.setIcon(FluentIcon.FOLDER)
        self.out_path_ico.setIcon(FluentIcon.SAVE_AS)
        self.start_button_ico.setIcon(FluentIcon.PLAY)
        self.ver.setText(f'<html><head/><body><p align="right"><span style=" font-size:6pt; color:#808080;">Ver:{VER}</span></p></body></html>')
        self.in_path_ico.clicked.connect(self.onInpath)
        self.out_path_ico.clicked.connect(self.onOutpath)
        self.start_button_ico.clicked.connect(self.onStart)
        self.type_buttonGroup.buttonClicked.connect(self.onChooseType)

    def convert_image(self, input_path: str, output_path: str, out_format: str):
        source = Path(input_path)
        target_dir = Path(output_path) if output_path else source.parent
        target_path = target_dir / f"{source.stem}.{out_format}"

        image_to_save = self.image
        if image_to_save is None:
            raise ValueError('图片尚未加载')

        if image_to_save.format == 'PNG' and out_format in ('jpg', 'jpeg'):
            image_to_save = image_to_save.convert('RGB')

        save_kwargs = {}
        if out_format == 'ico':
            save_kwargs['format'] = 'ICO'

        image_to_save.save(str(target_path), **save_kwargs)
        return str(target_path)

    def onInpath(self):
        self.filePathIn, _ = QFileDialog.getOpenFileName(
            self,
            "选择要转换的图片",
            r"c:\\",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if self.filePathIn == '':
            return
        self.image = Image.open(self.filePathIn)
        self.in_path_text_ico.setText('已选择文件:\n' + self.filePathIn)

    def onOutpath(self):
        self.filePathOut = QFileDialog.getExistingDirectory(self, "选择存储路径")
        self.out_path_text_ico.setText('已选择目录:\n' + self.filePathOut)

    def onChooseType(self):
        choiceId = self.type_buttonGroup.checkedId()
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

    def onStart(self):
        if self.filePathIn == '':
            QMessageBox.warning(self, '警告', '文件未选择')
            return

        if not self.outType:
            QMessageBox.warning(self, '警告', '请选择输出格式')
            return

        try:
            out_file = self.convert_image(self.filePathIn, self.filePathOut, self.outType)
            QMessageBox.information(self, '图片转换', f'转换完成！\n输出文件：\n{out_file}')
        except Exception as exc:
            QMessageBox.critical(self, '图片转换失败', f'转换失败：{exc}')
