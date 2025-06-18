import sys, os, json, re, yaml
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QPushButton, QListWidget,
    QListWidgetItem, QCheckBox, QFileDialog, QMessageBox, QLabel, QComboBox
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt
import google.generativeai as genai

# Configure Gemini
GEN_API_KEY = "your_gemini_api_key"
genai.configure(api_key=GEN_API_KEY)
model = genai.GenerativeModel("gemini-pro")

TAGS = ["Cleanup", "Security", "Documentation", "Refactoring", "Linting"]

class CursorRuleGod(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ Cursor Rule God - Gemini Powered")
        self.setMinimumSize(1000, 720)
        self.rules = []
        self.init_ui()
        self.set_dark_theme()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("🧠 Cursor Rule God")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Describe a rule (e.g. remove all console.log from JS)")
        layout.addWidget(self.prompt_input)

        self.generate_btn = QPushButton("🤖 Generate with Gemini")
        layout.addWidget(self.generate_btn)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Description")
        self.glob_input = QLineEdit()
        self.glob_input.setPlaceholderText("Globs (e.g. *.js, *.ts)")
        self.replacement_input = QTextEdit()
        self.replacement_input.setPlaceholderText("Replacement logic")
        self.always_apply = QCheckBox("Always Apply")

        self.tag_combo = QComboBox()
        self.tag_combo.setEditable(True)
        self.tag_combo.addItems(TAGS)
        self.tag_combo.setInsertPolicy(QComboBox.InsertAtTop)
        self.tag_combo.setPlaceholderText("Tag")

        layout.addWidget(self.description_input)
        layout.addWidget(self.glob_input)
        layout.addWidget(self.replacement_input)
        layout.addWidget(self.always_apply)
        layout.addWidget(self.tag_combo)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("➕ Add")
        self.enhance_btn = QPushButton("💡 Enhance")
        self.import_btn = QPushButton("📥 Import .mdc")
        self.preview_btn = QPushButton("👁 Preview")
        self.export_json_btn = QPushButton("💾 Export JSON")
        self.export_mdc_btn = QPushButton("📂 Export .mdc")
        self.sync_btn = QPushButton("🧠 Sync to Cursor")
        self.clear_btn = QPushButton("🧹 Clear")
        for b in [self.add_btn, self.enhance_btn, self.import_btn, self.preview_btn,
                  self.export_json_btn, self.export_mdc_btn, self.sync_btn, self.clear_btn]:
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self.rule_list = QListWidget()
        layout.addWidget(self.rule_list)

        # Signals
        self.generate_btn.clicked.connect(self.generate_with_gemini)
        self.add_btn.clicked.connect(self.add_rule)
        self.preview_btn.clicked.connect(self.preview_rule)
        self.export_json_btn.clicked.connect(self.export_json)
        self.export_mdc_btn.clicked.connect(self.export_mdc)
        self.sync_btn.clicked.connect(self.sync_to_cursor)
        self.clear_btn.clicked.connect(self.clear_rules)
        self.enhance_btn.clicked.connect(self.enhance_rule)
        self.import_btn.clicked.connect(self.import_mdc)

    def set_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#121212"))
        palette.setColor(QPalette.Base, QColor("#1e1e1e"))
        palette.setColor(QPalette.Text, QColor("#ffffff"))
        palette.setColor(QPalette.Button, QColor("#2d2d2d"))
        palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
        self.setPalette(palette)

    def generate_with_gemini(self):
        prompt = self.prompt_input.text().strip()
        if not prompt:
            return
        try:
            res = model.generate_content(f"""
Create a Cursor IDE rule in JSON:
{{
  "description": "...",
  "globs": ["*.js"],
  "replacement": "...",
  "alwaysApply": true
}}
From instruction: {prompt}
""")
            rule = json.loads(res.text.strip())
            self.description_input.setText(rule['description'])
            self.glob_input.setText(", ".join(rule['globs']))
            self.replacement_input.setText(rule['replacement'])
            self.always_apply.setChecked(rule['alwaysApply'])
        except Exception as e:
            QMessageBox.critical(self, "Gemini Error", str(e))

    def add_rule(self):
        rule = {
            "description": self.description_input.text().strip(),
            "globs": [g.strip() for g in self.glob_input.text().split(",") if g.strip()],
            "replacement": self.replacement_input.toPlainText().strip(),
            "alwaysApply": self.always_apply.isChecked(),
            "tags": [self.tag_combo.currentText().strip()] if self.tag_combo.currentText().strip() else []
        }
        if not rule['description'] or not rule['globs'] or not rule['replacement']:
            QMessageBox.warning(self, "Missing Fields", "Fill all fields.")
            return
        self.rules.append(rule)
        self.rule_list.addItem(f"{rule['description']} | Tags: {', '.join(rule['tags'])}")
        self.description_input.clear()
        self.glob_input.clear()
        self.replacement_input.clear()
        self.always_apply.setChecked(False)
        self.tag_combo.setCurrentIndex(0)

    def preview_rule(self):
        i = self.rule_list.currentRow()
        if i < 0:
            return
        QMessageBox.information(self, "Preview", json.dumps(self.rules[i], indent=2))

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "cursor_rules.json", "*.json")
        if path:
            with open(path, 'w') as f:
                json.dump(self.rules, f, indent=2)

    def export_mdc(self):
        dir = QFileDialog.getExistingDirectory(self, "Export .mdc")
        if not dir:
            return
        for rule in self.rules:
            fname = rule['description'].lower().replace(" ", "_") + ".mdc"
            fpath = Path(dir) / fname
            with open(fpath, 'w') as f:
                f.write("---\n")
                f.write(f"description: \"{rule['description']}\"\n")
                f.write(f"globs: {json.dumps(rule['globs'])}\n")
                f.write(f"alwaysApply: {str(rule['alwaysApply']).lower()}\n")
                f.write("---\n\n")
                f.write(f"- {rule['replacement']}\n")

    def sync_to_cursor(self):
        return self.export_mdc()

    def clear_rules(self):
        self.rules.clear()
        self.rule_list.clear()

    def enhance_rule(self):
        i = self.rule_list.currentRow()
        if i < 0:
            return
        rule = self.rules[i]
        try:
            res = model.generate_content(f"""
Improve this Cursor IDE rule:
{json.dumps(rule, indent=2)}
Return JSON only.
""")
            self.rules[i] = json.loads(res.text.strip())
            self.rule_list.item(i).setText(f"{self.rules[i]['description']} | Tags: {', '.join(self.rules[i].get('tags', []))}")
        except Exception as e:
            QMessageBox.critical(self, "Gemini Error", str(e))

    def import_mdc(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import .mdc", "", "*.mdc")
        if not path:
            return
        with open(path, 'r') as f:
            content = f.read()
        match = re.search(r"---\n(.*?)\n---\n(.*)", content, re.DOTALL)
        if not match:
            return
        meta = yaml.safe_load(match.group(1))
        rule = {
            "description": meta.get("description", "Imported Rule"),
            "globs": meta.get("globs", []),
            "replacement": match.group(2).strip().lstrip("- ").strip(),
            "alwaysApply": meta.get("alwaysApply", False),
            "tags": []
        }
        self.rules.append(rule)
        self.rule_list.addItem(f"{rule['description']} | Tags: None")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CursorRuleGod()
    window.show()
    sys.exit(app.exec_())
