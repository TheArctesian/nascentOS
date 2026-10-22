"""Icon-grid software selection shown before the Calamares installation wizard."""
import argparse
import json
from pathlib import Path
import sys

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QScrollArea, QStyle, QToolButton, QVBoxLayout, QWidget,
)
from nascent_software_model import defaults, load_manifest, validate
from nascent_optional_profiles import GAMING_KEYS, STEAM, gaming_defaults, providers, validate_vpn

STYLE = """
QWidget { background: #2e3440; color: #eceff4; font-family: 'Noto Sans'; font-size: 14px; }
QLabel#heading { font-size: 27px; font-weight: 600; }
QLabel#muted { color: #d8dee9; }
QLineEdit { background: #3b4252; border: 1px solid #4c566a; border-radius: 6px; padding: 9px; }
QListWidget { border: 0; background: #2e3440; outline: none; }
QListWidget::item { padding: 12px; border-radius: 6px; }
QListWidget::item:selected { background: #434c5e; color: #eceff4; }
QToolButton { border: 2px solid transparent; border-radius: 9px; padding: 6px; }
QToolButton:hover { background: #3b4252; }
QToolButton:checked { background: #434c5e; border-color: #88c0d0; }
QToolButton:focus, QPushButton:focus, QCheckBox:focus { border: 2px solid #88c0d0; }
QToolButton:disabled { color: #d8dee9; }
QPushButton { background: #434c5e; border: 2px solid transparent; border-radius: 6px; padding: 8px 16px; }
QPushButton#continue { background: #88c0d0; color: #2e3440; font-weight: 600; }
QPushButton:disabled { background: #3b4252; color: #d8dee9; }
QScrollArea { border: 0; }
"""


class Picker(QDialog):
    def __init__(self, manifest):
        super().__init__()
        self.manifest = manifest
        self.selected = set(defaults(manifest))
        self.accepted = set()
        self.vpn = None
        self.gaming = gaming_defaults()
        self.tiles = {}
        self.group = manifest["apps"][0]["group"]
        self.current = None
        self.setWindowTitle("Install nascentOS — choose your apps")
        self.resize(980, 740)
        self.setMinimumSize(820, 650)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Make room for your tools")
        title.setObjectName("heading")
        outer.addWidget(title)
        hint = QLabel("Choose apps and fonts for your new system. You can change these choices later.")
        hint.setObjectName("muted")
        outer.addWidget(hint)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Find an app…")
        self.search.setAccessibleName("Find an app in all categories")
        outer.addWidget(self.search)
        body = QHBoxLayout()
        self.categories = QListWidget()
        self.categories.setAccessibleName("App categories")
        self.categories.setFixedWidth(198)
        self.categories.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for group in dict.fromkeys(app["group"] for app in manifest["apps"]):
            item = QListWidgetItem("3D & games" if group == "3D & game development" else group)
            item.setData(Qt.ItemDataRole.UserRole, group)
            self.categories.addItem(item)
        system_item = QListWidgetItem("VPN & gaming")
        system_item.setData(Qt.ItemDataRole.UserRole, "optional-profiles")
        self.categories.addItem(system_item)
        self.categories.setCurrentRow(0)
        body.addWidget(self.categories)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        # A regular Finder-like icon collection keeps names directly under logos.
        from PySide6.QtWidgets import QGridLayout
        self.grid = QGridLayout(content)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid.setSpacing(12)
        scroll.setWidget(content)
        body.addWidget(scroll, 1)
        outer.addLayout(body, 1)
        self.detail = QLabel("Select an app to see installation details.")
        self.detail.setWordWrap(True)
        self.detail.setMinimumHeight(62)
        self.detail.setTextFormat(Qt.TextFormat.PlainText)
        outer.addWidget(self.detail)
        detail_actions = QHBoxLayout()
        self.website = QPushButton("App website")
        self.website.setEnabled(False)
        self.website.clicked.connect(self.open_website)
        detail_actions.addWidget(self.website)
        detail_actions.addStretch()
        reset = QPushButton("Restore defaults")
        reset.clicked.connect(self.reset)
        detail_actions.addWidget(reset)
        outer.addLayout(detail_actions)
        footer = QHBoxLayout()
        self.count = QLabel()
        footer.addWidget(self.count, 1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        footer.addWidget(cancel)
        proceed = QPushButton("Continue to installation")
        proceed.setObjectName("continue")
        proceed.clicked.connect(self.accept)
        footer.addWidget(proceed)
        outer.addLayout(footer)
        self.categories.currentItemChanged.connect(
            lambda item: self.change_group(item.data(Qt.ItemDataRole.UserRole)) if item else None)
        self.search.textChanged.connect(self.render)
        self.render()

    def change_group(self, group):
        self.group = group
        self.render()

    def describe(self, app):
        self.current = app
        kind = {"package": "Native package", "web": "Browser shortcut", "manual": "Manual setup only"}[app["kind"]]
        if app.get("backend") == "appimage":
            kind = "Nix-wrapped AppImage"
        parts = [f"{app['name']} — {kind}", app["description"]]
        if app.get("group") == "Passwords":
            parts.append("Choose one password manager; selecting this replaces your previous choice.")
        if app["proprietary"]:
            parts.append("Proprietary service" if app["kind"] == "web" else "Proprietary software")
        if not app["available"]:
            parts.append(app.get("reason") or "Unavailable on this architecture")
        self.detail.setText("\n".join(parts))
        self.website.setEnabled(True)

    def open_website(self):
        if self.current:
            QDesktopServices.openUrl(QUrl(self.current["url"]))

    def confirm_proprietary(self, app):
        dialog = QDialog(self)
        dialog.setWindowTitle(app["name"])
        layout = QVBoxLayout(dialog)
        text = QLabel(f"{app['name']} uses proprietary software or a proprietary service.\n"
                      "Selecting it adds the package from the pinned software collection.\n"
                      "An account, subscription or separate terms may be required.")
        text.setWordWrap(True)
        layout.addWidget(text)
        license_label = QLabel("License / service terms: " + app["license"])
        license_label.setWordWrap(True)
        layout.addWidget(license_label)
        site = QPushButton("View app website and terms")
        site.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(app["url"])))
        layout.addWidget(site)
        consent = QCheckBox("Include this optional app")
        layout.addWidget(consent)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        consent.toggled.connect(buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def toggle(self, app, checked):
        self.describe(app)
        name = app["id"]
        focused = self.tiles[name].hasFocus()
        if checked and app["proprietary"] and not self.confirm_proprietary(app):
            self.tiles[name].setChecked(False)
            return
        if checked:
            if app.get("group") == "Passwords":
                previous = {item["id"] for item in self.manifest["apps"]
                            if item.get("group") == "Passwords"}
                self.selected.difference_update(previous)
                self.accepted.difference_update(previous)
            self.selected.add(name)
            if app["proprietary"]:
                self.accepted.add(name)
        else:
            self.selected.discard(name)
            self.accepted.discard(name)
        self.render()
        if focused and name in self.tiles:
            self.tiles[name].setFocus()

    def reset(self):
        self.selected = set(defaults(self.manifest))
        self.accepted.clear()
        self.vpn = None
        self.gaming = gaming_defaults()
        self.render()

    def set_vpn(self, index):
        self.vpn = validate_vpn(self.vpn_choice.itemData(index), self.manifest["system"])

    def toggle_gaming(self, key, checked):
        if key == "enable":
            self.gaming = gaming_defaults(checked)
            self.accepted.discard("steam")
        elif key == "steam":
            if checked and not self.confirm_proprietary(STEAM):
                self.gaming_controls[key].setChecked(False)
                return
            self.gaming[key] = checked
            if checked:
                self.accepted.add("steam")
            else:
                self.accepted.discard("steam")
                self.gaming["steamGamescopeSession"] = False
        else:
            self.gaming[key] = checked
            if key == "gamescope" and not checked:
                self.gaming["steamGamescopeSession"] = False
        self.render()

    def render_profiles(self):
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        vpn_label = QLabel("VPN — optional, choose one")
        layout.addWidget(vpn_label)
        self.vpn_choice = QComboBox()
        self.vpn_choice.setAccessibleName("Optional VPN provider")
        self.vpn_choice.addItem("None", None)
        for provider in providers(self.manifest["system"]):
            label = provider["name"] + ("" if provider["available"] else " — unavailable on this architecture")
            self.vpn_choice.addItem(label, provider["id"])
            item = self.vpn_choice.model().item(self.vpn_choice.count() - 1)
            item.setEnabled(provider["available"])
            item.setToolTip(provider["description"])
        self.vpn_choice.setCurrentIndex(self.vpn_choice.findData(self.vpn))
        self.vpn_choice.currentIndexChanged.connect(self.set_vpn)
        layout.addWidget(self.vpn_choice)
        note = QLabel("Installs support only. Sign in or import your profile after installation; no VPN connects here.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.gaming_controls = {}
        labels = {"enable": "Gaming support (optional)", "gamemode": "GameMode — on-demand game tuning",
                  "gamescope": "gamescope — nested game compositor", "steam": "Steam — proprietary, x86_64 only",
                  "steamGamescopeSession": "Additional Steam gamescope login session",
                  "maxMapCount": "Mapping compatibility tuning (system-wide)"}
        for key in GAMING_KEYS:
            control = QCheckBox(labels[key])
            control.setChecked(self.gaming[key])
            enabled = key == "enable" or self.gaming["enable"]
            if key == "steam":
                enabled = enabled and self.manifest["system"] == "x86_64-linux"
            if key == "steamGamescopeSession":
                enabled = enabled and self.gaming["steam"] and self.gaming["gamescope"]
            control.setEnabled(enabled)
            control.toggled.connect(lambda checked, key=key: self.toggle_gaming(key, checked))
            layout.addWidget(control)
            self.gaming_controls[key] = control
        gaming_note = QLabel("Steam requires explicit proprietary inclusion and may download its client on first launch. "
                             "No game, login, GPU tuning or extra session is selected automatically.")
        gaming_note.setWordWrap(True)
        layout.addWidget(gaming_note)
        self.grid.addWidget(panel, 0, 0, 1, 4)
        self.detail.setText("Optional system support is separate from app selection. "
                            "Turning gaming off clears every gaming component.")
        self.current = None
        self.website.setEnabled(False)

    def render(self):
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        while self.grid.count():
            previous = self.grid.takeAt(0).widget()
            previous.hide()
            previous.deleteLater()
        self.tiles.clear()
        query = self.search.text().strip().casefold()
        apps = [app for app in self.manifest["apps"]
                if (query in (app["name"] + " " + app["description"]).casefold()
                    if query else app["group"] == self.group)]
        if self.group == "optional-profiles" and not query:
            self.render_profiles()
        for position, app in enumerate(apps):
            tile = QToolButton()
            tile.setFixedSize(128, 136)
            tile.setIconSize(QSize(64, 64))
            tile.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            icon = QIcon.fromTheme(app["icon"])
            if icon.isNull():
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            tile.setIcon(icon)
            selectable = app["available"] and app["kind"] == "package"
            tile.setCheckable(selectable)
            selected = app["id"] in self.selected
            tile.setChecked(selected)
            suffix = "✓ Selected" if selected else {"web": "Not offered", "manual": "Manual setup"}.get(app["kind"], "Proprietary" if app["proprietary"] else "Add app")
            if not app["available"] and app["kind"] != "manual":
                suffix = "Unavailable"
            tile.setText(app["name"] + "\n" + suffix)
            tile.setAccessibleName(app["name"] + ", " + suffix)
            tile.setToolTip(app["description"] + "\n" + (app.get("reason") or suffix))
            # Unavailable entries remain focusable so their reason is discoverable.
            tile.clicked.connect(lambda checked=False, app=app, ok=selectable:
                                 self.toggle(app, checked) if ok else self.describe(app))
            self.grid.addWidget(tile, position // 4, position % 4)
            self.tiles[app["id"]] = tile
        if not apps and (self.group != "optional-profiles" or query):
            self.grid.addWidget(QLabel("No apps match your search."), 0, 0)
        fonts = sum(app["id"] in self.selected and app.get("role") == "font"
                    for app in self.manifest["apps"])
        self.count.setText(f"{len(self.selected) - fonts} apps · {fonts} fonts selected · optional downloads may be large")

    def result_value(self):
        return validate(self.manifest, {"selected": list(self.selected),
                                        "acceptedProprietary": list(self.accepted),
                                        "vpn": self.vpn, "gaming": self.gaming})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--icon-path", type=Path)
    parser.add_argument("--screenshot", type=Path, help="Render the real UI then exit without selecting")
    args = parser.parse_args()
    application = QApplication(sys.argv[:1])
    application.setStyleSheet(STYLE)
    if args.icon_path:
        QIcon.setThemeSearchPaths([str(args.icon_path)] + QIcon.themeSearchPaths())
    QIcon.setThemeName("Papirus-Dark")
    try:
        picker = Picker(load_manifest(args.manifest))
        if args.screenshot:
            picker.show()
            application.processEvents()
            if not picker.grab().save(str(args.screenshot)):
                raise ValueError("Could not save software picker screenshot")
            picker.deleteLater()
            application.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            return 0
        accepted = picker.exec() == QDialog.DialogCode.Accepted
        if accepted:
            print(json.dumps(picker.result_value()))
        picker.deleteLater()
        application.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        return 0 if accepted else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        QMessageBox.critical(None, "Software selection unavailable", str(error))
        return 2


if __name__ == "__main__":
    sys.exit(main())
