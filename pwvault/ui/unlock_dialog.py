"""First-run master password setup / subsequent unlock dialog."""

from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout

from .. import vault


class UnlockDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.key: bytes | None = None
        self.data: dict | None = None
        self._is_setup = not vault.vault_exists()

        self.setWindowTitle("密碼本 - 設定主密碼" if self._is_setup else "密碼本 - 解鎖")
        self.setModal(True)
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        if self._is_setup:
            info_text = (
                "首次使用，請設定主密碼。\n"
                "注意：主密碼一旦遺失將無法復原密碼庫內的任何資料，請務必妥善保管。"
            )
        else:
            info_text = "請輸入主密碼以解鎖密碼庫。"
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        form = QFormLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("主密碼：", self.password_edit)

        self.confirm_edit: QLineEdit | None = None
        if self._is_setup:
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
            form.addRow("確認主密碼：", self.confirm_edit)

        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        self.submit_button = QPushButton("設定主密碼並建立密碼庫" if self._is_setup else "解鎖")
        self.submit_button.clicked.connect(self._on_submit)
        layout.addWidget(self.submit_button)

        self.password_edit.returnPressed.connect(self._on_submit)
        if self.confirm_edit is not None:
            self.confirm_edit.returnPressed.connect(self._on_submit)

        self.password_edit.setFocus()

    def _on_submit(self):
        password = self.password_edit.text()

        if self._is_setup:
            confirm = self.confirm_edit.text() if self.confirm_edit else ""
            if not password:
                self.error_label.setText("主密碼不可為空")
                return
            if password != confirm:
                self.error_label.setText("兩次輸入的主密碼不一致")
                return
            try:
                self.key, self.data = vault.create_vault(password)
            except vault.VaultError as exc:
                self.error_label.setText(f"建立密碼庫失敗：{exc}")
                return
            self.accept()
            return

        if not password:
            self.error_label.setText("請輸入主密碼")
            return
        try:
            self.key, self.data = vault.unlock_vault(password)
        except vault.WrongPasswordError:
            self.error_label.setText("主密碼錯誤，請重新輸入")
            self.password_edit.clear()
            self.password_edit.setFocus()
            return
        except vault.CorruptVaultError as exc:
            QMessageBox.critical(self, "錯誤", f"密碼庫檔案損毀：{exc}")
            return
        self.accept()
