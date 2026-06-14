"""Main application window: entry list, detail/edit form, search and tag filters."""

import uuid

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .. import vault
from .generator_dialog import GeneratorDialog


class MainWindow(QMainWindow):
    def __init__(self, key: bytes, data: dict):
        super().__init__()
        self.key = key
        self.data = data
        self.current_entry_id: str | None = None  # None => unsaved new entry

        self.setWindowTitle("密碼本")
        self.resize(900, 560)

        self._build_ui()
        self._refresh_tag_list()
        self._refresh_entry_list()
        self._show_placeholder()

    # ---- UI construction ---------------------------------------------------
    def _build_ui(self):
        toolbar = QToolBar("工具列")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        new_action = toolbar.addAction("新增帳密")
        new_action.triggered.connect(self._on_new_entry)

        gen_action = toolbar.addAction("密碼生成器")
        gen_action.triggered.connect(self._on_open_generator)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        # Top bar: search box
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("搜尋："))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("依名稱 / 帳號搜尋（不分大小寫）…")
        self.search_edit.textChanged.connect(self._refresh_entry_list)
        top_bar.addWidget(self.search_edit)
        root_layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter)

        # Left panel: tag filter + entry list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("標籤篩選（可多選）："))
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.tag_list.setMaximumHeight(100)
        self.tag_list.itemSelectionChanged.connect(self._refresh_entry_list)
        left_layout.addWidget(self.tag_list)

        left_layout.addWidget(QLabel("帳密列表："))
        self.entry_list = QListWidget()
        self.entry_list.currentItemChanged.connect(self._on_entry_selected)
        left_layout.addWidget(self.entry_list)

        splitter.addWidget(left_widget)

        # Right panel: detail / edit form
        right_widget = QWidget()
        form_layout = QFormLayout(right_widget)

        self.name_edit = QLineEdit()
        form_layout.addRow("名稱*：", self.name_edit)

        username_row = QHBoxLayout()
        self.username_edit = QLineEdit()
        username_row.addWidget(self.username_edit)
        copy_username_btn = QPushButton("複製")
        copy_username_btn.clicked.connect(self._on_copy_username)
        username_row.addWidget(copy_username_btn)
        form_layout.addRow("帳號：", username_row)

        password_row = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_row.addWidget(self.password_edit)
        self.toggle_password_btn = QPushButton("顯示")
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.toggled.connect(self._on_toggle_password)
        password_row.addWidget(self.toggle_password_btn)
        copy_password_btn = QPushButton("複製")
        copy_password_btn.clicked.connect(self._on_copy_password)
        password_row.addWidget(copy_password_btn)
        form_layout.addRow("密碼：", password_row)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("以逗號分隔，例如：工作, Google")
        form_layout.addRow("標籤：", self.tags_edit)

        button_row = QHBoxLayout()
        self.save_button = QPushButton("儲存")
        self.save_button.clicked.connect(self._on_save_entry)
        button_row.addWidget(self.save_button)

        self.delete_button = QPushButton("刪除")
        self.delete_button.clicked.connect(self._on_delete_entry)
        button_row.addWidget(self.delete_button)
        form_layout.addRow("", button_row)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

    # ---- data helpers ---------------------------------------------------------
    def _entries(self) -> list[dict]:
        return self.data.setdefault("entries", [])

    def _find_entry(self, entry_id: str) -> dict | None:
        for entry in self._entries():
            if entry["id"] == entry_id:
                return entry
        return None

    def _all_tags(self) -> list[str]:
        tags: set[str] = set()
        for entry in self._entries():
            tags.update(entry.get("tags", []))
        return sorted(tags)

    # ---- list refreshing ----------------------------------------------------
    def _refresh_tag_list(self):
        selected = {item.text() for item in self.tag_list.selectedItems()}
        self.tag_list.blockSignals(True)
        self.tag_list.clear()
        for tag in self._all_tags():
            item = QListWidgetItem(tag)
            self.tag_list.addItem(item)
            if tag in selected:
                item.setSelected(True)
        self.tag_list.blockSignals(False)

    def _refresh_entry_list(self):
        keyword = self.search_edit.text().strip().lower()
        selected_tags = {item.text() for item in self.tag_list.selectedItems()}
        previous_id = self.current_entry_id

        self.entry_list.blockSignals(True)
        self.entry_list.clear()

        for entry in self._entries():
            name = entry.get("name", "")
            username = entry.get("username", "")
            entry_tags = set(entry.get("tags", []))

            if keyword and keyword not in name.lower() and keyword not in username.lower():
                continue
            if selected_tags and not (selected_tags & entry_tags):
                continue

            tags_text = ", ".join(entry.get("tags", []))
            label = f"{name}  [{tags_text}]" if tags_text else name
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, entry["id"])
            self.entry_list.addItem(item)
            if entry["id"] == previous_id:
                self.entry_list.setCurrentItem(item)

        self.entry_list.blockSignals(False)

    # ---- form state ----------------------------------------------------------
    def _show_placeholder(self):
        self.current_entry_id = None
        self.name_edit.clear()
        self.username_edit.clear()
        self.password_edit.clear()
        self.tags_edit.clear()
        self.toggle_password_btn.setChecked(False)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def _load_entry_into_form(self, entry: dict):
        self.current_entry_id = entry["id"]
        self.name_edit.setText(entry.get("name", ""))
        self.username_edit.setText(entry.get("username", ""))
        self.password_edit.setText(entry.get("password", ""))
        self.tags_edit.setText(", ".join(entry.get("tags", [])))
        self.toggle_password_btn.setChecked(False)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    # ---- slots ------------------------------------------------------------------
    def _on_entry_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None):
        if current is None:
            return
        entry_id = current.data(Qt.ItemDataRole.UserRole)
        entry = self._find_entry(entry_id)
        if entry:
            self._load_entry_into_form(entry)

    def _on_new_entry(self):
        self.entry_list.setCurrentItem(None)
        self.entry_list.clearSelection()
        self._show_placeholder()
        self.name_edit.setFocus()

    def _on_toggle_password(self, checked: bool):
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setText("隱藏")
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setText("顯示")

    def _on_copy_username(self):
        QGuiApplication.clipboard().setText(self.username_edit.text())

    def _on_copy_password(self):
        QGuiApplication.clipboard().setText(self.password_edit.text())

    def _on_save_entry(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "無法儲存", "名稱為必填欄位")
            return

        tags = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]
        username = self.username_edit.text()
        password = self.password_edit.text()

        is_new_entry = self.current_entry_id is None

        if is_new_entry:
            entry = {
                "id": str(uuid.uuid4()),
                "name": name,
                "username": username,
                "password": password,
                "tags": tags,
            }
            self._entries().append(entry)
            self.current_entry_id = entry["id"]
        else:
            entry = self._find_entry(self.current_entry_id)
            if entry is None:
                return
            entry["name"] = name
            entry["username"] = username
            entry["password"] = password
            entry["tags"] = tags

        self._persist()
        self._refresh_tag_list()
        self._refresh_entry_list()

        if is_new_entry:
            # Immediately clear the form so the user can keep entering
            # consecutive new entries without clicking "新增帳密" again.
            self._on_new_entry()

    def _on_delete_entry(self):
        if self.current_entry_id is None:
            return
        entry = self._find_entry(self.current_entry_id)
        if entry is None:
            return

        confirm = QMessageBox.question(
            self,
            "刪除帳密",
            f"確定要刪除「{entry.get('name', '')}」嗎？此操作無法復原。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._entries().remove(entry)
        self._persist()
        self._show_placeholder()
        self._refresh_tag_list()
        self._refresh_entry_list()

    def _on_open_generator(self):
        dialog = GeneratorDialog(self, embed_callback=self._apply_generated_password)
        dialog.exec()

    def _apply_generated_password(self, password: str):
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        self.toggle_password_btn.setChecked(True)
        self.password_edit.setText(password)

    # ---- persistence -----------------------------------------------------------
    def _persist(self):
        try:
            vault.save_vault(self.key, self.data)
        except vault.VaultError as exc:
            QMessageBox.critical(self, "儲存失敗", str(exc))
