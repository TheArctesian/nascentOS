#!/usr/bin/env python3
"""Focused Qt Widgets layout preview, not an installation or full Calamares run.

Uses the production QSS and the pinned wizard's widget structure; mirrors the
presentation adapter. Fusion approximates Linux theme metrics on macOS.
"""
import argparse
from pathlib import Path
import sys
from PySide6.QtCore import Qt, QSize, QRect, QPoint
from PySide6.QtGui import QFont, QPainter, QPixmap, QPalette, QColor
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QProgressBar, QSizePolicy, QTabWidget, QPlainTextEdit, QToolBar,
    QFormLayout, QLineEdit, QCheckBox, QComboBox, QListView,
    QStyledItemDelegate, QStyleOptionViewItem,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem

HERE = Path(__file__).resolve().parent


class Artwork(QLabel):
    def __init__(self, asset):
        super().__init__()
        self.setPixmap(QPixmap(str(asset)))
        self.setMinimumSize(0, 0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def sizeHint(self):
        return QSize(640, 360)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def paintEvent(self, event):
        target = self.pixmap().size()
        target.scale(QSize(min(self.width(), 640), min(self.height(), 360)), Qt.KeepAspectRatio)
        area = QRect(QPoint(0, 0), target)
        area.moveCenter(self.rect().center())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(area, self.pixmap())


class Steps(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(option.rect.width(), option.fontMetrics.height() + 20)

    def paint(self, painter, option, index):
        painter.save()
        current = index.row() == self.parent().property('currentStep')
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('#88c0d0' if current else '#2e3440'))
        painter.drawRoundedRect(option.rect.adjusted(0, 2, 0, -2), 6, 6)
        painter.setPen(QColor('#2e3440' if current else '#eceff4'))
        font = option.font
        font.setBold(current)
        painter.setFont(font)
        painter.drawText(option.rect.adjusted(10, 10, -10, -10), Qt.AlignLeft | Qt.AlignVCenter, index.data())
        painter.restore()


def named(widget, name):
    widget.setObjectName(name)
    return widget


def make_window(asset, width, height, page='install'):
    compact = height < 660
    inset = 40 if width >= 1100 else 28 if width >= 900 else 20
    window = named(QWidget(), 'mainApp')
    window.resize(width, height)
    main = QHBoxLayout(window)
    main.setContentsMargins(0, 0, 0, 0)
    main.setSpacing(0)
    side = named(QWidget(), 'sidebarApp')
    side.setFixedWidth(196 if width < 1000 else 224)
    sidebar = QVBoxLayout(side)
    sidebar.setContentsMargins(16, 20 if compact else 28, 16, 16 if compact else 24)
    sidebar.setSpacing(12 if compact else 24)
    logo = QLabel()
    logo.setFixedSize(56, 56)
    logo.setPixmap(QPixmap(str(asset)).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    sidebar.addWidget(logo, 0, Qt.AlignHCenter)
    sidebar.addWidget(named(QLabel('nascentOS', alignment=Qt.AlignCenter), 'nascentProductName'))
    steps = named(QListView(), 'sidebarMenuApp')
    steps.setFocusPolicy(Qt.NoFocus)
    steps.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    steps.setSelectionMode(QListView.NoSelection)
    steps.setProperty('currentStep', 7 if page == 'install' else 3)
    model = QStandardItemModel(steps)
    for name in ['Welcome', 'Location', 'Keyboard', 'Users', 'Desktop', 'Partitions', 'Summary', 'Install', 'Finish']:
        model.appendRow(QStandardItem(name))
    steps.setModel(model)
    steps.setItemDelegate(Steps(steps))
    sidebar.addWidget(steps, 1)
    sidebar.addWidget(named(QPushButton('About'), 'aboutButton'))
    main.addWidget(side)
    column = QVBoxLayout()
    column.setContentsMargins(inset, 20 if compact else 32, inset, 0)
    column.setSpacing(0)
    content = named(QWidget(), 'viewManager')
    content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    content.setFixedWidth(min(1080, width - side.width() - 2 * inset))
    body = QVBoxLayout(content)
    body.setContentsMargins(0, 0, 0, 0)
    body.setSpacing(24)
    title = named(QLabel('Installing nascentOS' if page == 'install' else 'Create your account'), 'nascentPageTitle')
    title.setWordWrap(True)
    body.addWidget(title)
    if page == 'install':
        tabs = named(QTabWidget(), 'nascentExecutionTabs')
        tabs.addTab(Artwork(asset), 'Slideshow')
        tabs.addTab(QPlainTextEdit('Installation log'), 'Log')
        tabs.tabBar().hide()
        body.addWidget(tabs, 1)
        bottom = QVBoxLayout()
        bottom.setSpacing(10)
        row = QHBoxLayout()
        row.setSpacing(12)
        progress = named(QProgressBar(), 'exec-progress')
        progress.setMaximum(10000)
        progress.setValue(6800)
        progress.setTextVisible(False)
        row.addWidget(progress, 1)
        row.addWidget(named(QLabel('68%', alignment=Qt.AlignRight | Qt.AlignVCenter), 'nascentProgressValue'))
        toolbar = named(QToolBar(), 'nascentLogToolbar')
        action = toolbar.addAction('≡')
        action.setToolTip('Show installation log')
        action.triggered.connect(lambda: tabs.setCurrentIndex(1 - tabs.currentIndex()))
        row.addWidget(toolbar)
        bottom.addLayout(row)
        bottom.addWidget(named(QLabel('Installing NixOS.'), 'exec-message'))
        body.addLayout(bottom)
    else:
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        for label, value in [('Your name', 'Stephen'), ('Login name', 'stephen'), ('Computer name', 'nascent'), ('Password', ''), ('Confirm password', '')]:
            edit = QLineEdit(value)
            if 'password' in label.lower():
                edit.setEchoMode(QLineEdit.Password)
            form.addRow(label, edit)
        body.addLayout(form)
        body.addWidget(QCheckBox('Use the same password for the administrator account'))
        body.addStretch(1)
    column.addWidget(content, 1, Qt.AlignHCenter)
    nav = QWidget()
    nav.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    nav.setFixedWidth(content.width())
    footer = QHBoxLayout(nav)
    footer.setContentsMargins(0, 12 if compact else 20, 0, 16 if compact else 24)
    footer.setSpacing(12)
    footer.addStretch(1)
    for text, name in [('Back', 'back'), ('Next', 'next'), ('Cancel', 'cancel')]:
        if name == 'cancel':
            footer.addSpacing(12)
        button = named(QPushButton(text), f'view-button-{name}')
        button.setEnabled(page != 'install' or name == 'cancel')
        footer.addWidget(button)
    column.addWidget(nav, 0, Qt.AlignHCenter)
    main.addLayout(column, 1)
    window.setStyleSheet((HERE / 'branding/stylesheet.qss').read_text())
    window.show()
    QApplication.processEvents()
    return window


def check_geometry(window):
    bounds = window.rect()
    for name in ['viewManager', 'view-button-back', 'view-button-next', 'view-button-cancel', 'exec-progress', 'exec-message']:
        widget = window.findChild(QWidget, name)
        if widget:
            rect = QRect(widget.mapTo(window, QPoint(0, 0)), widget.size())
            assert bounds.contains(rect), (name, rect, bounds)
            assert widget.width() > 0 and widget.height() > 0, (name, rect)
    buttons = [window.findChild(QWidget, f'view-button-{n}') for n in ['back', 'next', 'cancel']]
    assert all(b.height() >= 36 for b in buttons)
    assert buttons[-1].mapTo(window, QPoint(buttons[-1].width(), 0)).x() <= window.width() - 20
    return {w.objectName(): [w.x(), w.y(), w.width(), w.height()] for w in buttons}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--asset', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=HERE / 'previews')
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont('Helvetica Neue', 11))
    palette = app.palette()
    for role, color in [(QPalette.Window, '#2e3440'), (QPalette.WindowText, '#eceff4'), (QPalette.Base, '#3b4252'), (QPalette.Text, '#eceff4'), (QPalette.ButtonText, '#eceff4')]:
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    args.out.mkdir(parents=True, exist_ok=True)
    for width, height, page in [(1280, 800, 'install'), (1024, 768, 'install'), (800, 600, 'install'), (800, 520, 'install'), (1280, 800, 'users')]:
        window = make_window(args.asset, width, height, page)
        print(f'{width}x{height} {page}: {check_geometry(window)}')
        assert window.size() == QSize(width, height), window.size()
        assert window.grab().save(str(args.out / f'{page}-{width}x{height}.png'))
        window.close()
