"""Entry point for the 密碼本 (Password Vault) desktop application."""

import sys

from PySide6.QtWidgets import QApplication, QDialog

from pwvault.ui.main_window import MainWindow
from pwvault.ui.unlock_dialog import UnlockDialog


def main() -> int:
    app = QApplication(sys.argv)

    unlock_dialog = UnlockDialog()
    if unlock_dialog.exec() != QDialog.DialogCode.Accepted:
        return 0

    window = MainWindow(unlock_dialog.key, unlock_dialog.data)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
