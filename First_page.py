from io import BytesIO
from pathlib import Path

from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget

from Ui_fst import Ui_FirstPage
from qfluentwidgets import FluentIcon

import fitz
from PIL import Image
from ver import VER


class PdfCompressWorker(QThread):
    progress_changed = pyqtSignal(float)
    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, pdf_path: str, out_dir: str, dpi: int, img_type: str = "png", method: int = 0):
        super().__init__()
        self.pdf_path = Path(pdf_path)
        self.out_dir = Path(out_dir) if out_dir else None
        self.dpi = dpi
        self.img_type = img_type
        self.method = method

    def run(self):
        try:
            merges = []
            first_file = None
            with fitz.open(str(self.pdf_path)) as doc:
                total = len(doc)
                if total == 0:
                    raise ValueError("PDF为空，无法压缩")

                for i, page in enumerate(doc.pages(), start=0):
                    img = page.get_pixmap(dpi=self.dpi)
                    img_bytes = img.pil_tobytes(format=self.img_type)
                    image = Image.open(BytesIO(img_bytes))
                    if i == 0:
                        first_file = image
                    pix: Image.Image = image.quantize(colors=256, method=self.method).convert('RGB')
                    merges.append(pix)
                    self.progress_changed.emit(((i + 1) / total) * 100)

            if first_file is None:
                raise ValueError("无法读取PDF首页")

            out_name = f"{self.pdf_path.stem}_in_{self.dpi}dpi.pdf"
            out_path = (self.out_dir / out_name) if self.out_dir else self.pdf_path.with_name(out_name)

            first_file.save(
                str(out_path),
                "pdf",
                save_all=True,
                append_images=merges[1:],
            )
            self.succeeded.emit(str(out_path))
        except Exception as exc:
            self.failed.emit(str(exc))


class FirstPage(QWidget, Ui_FirstPage):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.filePathIn = ''
        self.filePathOut = ''
        self._dpi = 150
        self.worker = None

        self.in_path.setIcon(FluentIcon.FOLDER)
        self.out_path.setIcon(FluentIcon.SAVE_AS)
        self.start_button.setIcon(FluentIcon.PLAY)
        self.ver.setText(f'<html><head/><body><p align="right"><span style=" font-size:6pt; color:#808080;">Ver:{VER}</span></p></body></html>')
        self.in_path.clicked.connect(self.onInpath)
        self.out_path.clicked.connect(self.onOutpath)
        self.start_button.clicked.connect(self.onStart)
        self.custom_dpi.sliderMoved.connect(self.onTextChange)

    def updateBar(self, step):
        self.progressBar.setVal(float(step))

    def onCompressSuccess(self, out_path: str):
        QMessageBox.information(self, 'PDF操作', f'压缩完成！\n输出文件：\n{out_path}')
        self.progressBar.setVal(0)
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.start_button.setEnabled(True)
        self.worker = None

    def onCompressError(self, err_msg: str):
        QMessageBox.critical(self, 'PDF操作失败', f'压缩失败：{err_msg}')
        self.progressBar.setVal(0)
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.start_button.setEnabled(True)
        self.worker = None

    def onInpath(self):
        self.filePathIn, _ = QFileDialog.getOpenFileName(
            self,
            "选择要压缩的PDF",
            r"c:\\",
            "PDF文件 (*.pdf)",
        )
        if not self.filePathIn:
            return
        self.in_path_text.setText('已选择文件:\n' + self.filePathIn)

    def onOutpath(self):
        self.filePathOut = QFileDialog.getExistingDirectory(self, "选择存储路径")
        self.out_path_text.setText('已选择目录:\n' + self.filePathOut)

    def onStart(self):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.warning(self, '警告', '压缩任务正在进行中，请稍后')
            return

        if not self.filePathIn:
            QMessageBox.warning(self, '警告', '文件未选择')
            return

        if self._dpi > 600 or self._dpi < 72:
            QMessageBox.warning(self, '警告', '设定的范围超出阈值')
            return

        self.setCursor(QCursor(Qt.WaitCursor))
        self.start_button.setEnabled(False)

        self.worker = PdfCompressWorker(self.filePathIn, self.filePathOut, self._dpi)
        self.worker.progress_changed.connect(self.updateBar)
        self.worker.succeeded.connect(self.onCompressSuccess)
        self.worker.failed.connect(self.onCompressError)
        self.worker.start()

    def onChoice(self):
        choiceId = self.choice_buttonGroup.checkedId()
        if choiceId == -2:
            self._dpi = 300
        elif choiceId == -3:
            self._dpi = 200
        elif choiceId == -4:
            self._dpi = 150
        elif choiceId == -5:
            self._dpi = int(self.custom_dpi.text())

    def onTextChange(self):
        self._dpi = self.custom_dpi.value()
        self.custom_dpi_text.setText(f'{self._dpi} DPI')
