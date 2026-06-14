"""Password generator dialog."""

from typing import Callable, Optional

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from .. import password_generator as pwgen


class GeneratorDialog(QDialog):
    def __init__(self, parent=None, embed_callback: Optional[Callable[[str], None]] = None):
        super().__init__(parent)
        self._embed_callback = embed_callback

        self.setWindowTitle("密碼生成器")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.length_spin = QSpinBox()
        self.length_spin.setRange(1, 256)
        self.length_spin.setValue(16)
        form.addRow("長度：", self.length_spin)

        self.digits_spin = QSpinBox()
        self.digits_spin.setRange(0, 256)
        self.digits_spin.setValue(2)
        form.addRow("數字最少數量：", self.digits_spin)

        self.upper_spin = QSpinBox()
        self.upper_spin.setRange(0, 256)
        self.upper_spin.setValue(2)
        form.addRow("大寫最少數量：", self.upper_spin)

        self.lower_spin = QSpinBox()
        self.lower_spin.setRange(0, 256)
        self.lower_spin.setValue(2)
        form.addRow("小寫最少數量：", self.lower_spin)

        self.symbols_spin = QSpinBox()
        self.symbols_spin.setRange(0, 256)
        self.symbols_spin.setValue(2)
        form.addRow("標點最少數量：", self.symbols_spin)

        layout.addLayout(form)

        self.generate_button = QPushButton("生成")
        self.generate_button.clicked.connect(self._on_generate)
        layout.addWidget(self.generate_button)

        self.result_edit = QLineEdit()
        self.result_edit.setReadOnly(True)
        layout.addWidget(self.result_edit)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        button_row = QHBoxLayout()
        self.copy_button = QPushButton("複製結果")
        self.copy_button.clicked.connect(self._on_copy)
        button_row.addWidget(self.copy_button)

        self.use_button = QPushButton("帶入密碼欄")
        self.use_button.clicked.connect(self._on_use)
        button_row.addWidget(self.use_button)
        layout.addLayout(button_row)

        # Generate once on open so the dialog isn't empty.
        self._on_generate()

    def _on_generate(self):
        try:
            result = pwgen.generate_password(
                length=self.length_spin.value(),
                digits=self.digits_spin.value(),
                upper=self.upper_spin.value(),
                lower=self.lower_spin.value(),
                symbols=self.symbols_spin.value(),
            )
        except pwgen.GeneratorError as exc:
            self.error_label.setText(str(exc))
            self.result_edit.clear()
            return

        self.error_label.setText("")
        self.result_edit.setText(result)

    def _on_copy(self):
        text = self.result_edit.text()
        if text:
            QGuiApplication.clipboard().setText(text)

    def _on_use(self):
        text = self.result_edit.text()
        if not text:
            self.error_label.setText("請先生成密碼")
            return
        if self._embed_callback:
            self._embed_callback(text)
        self.accept()
