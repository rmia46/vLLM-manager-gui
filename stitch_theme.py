STITCH_DARK_STYLESHEET = """
QMainWindow {
    background-color: #0A0A0A;
    color: #e5e2e1;
}
QWidget {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #e5e2e1;
}
/* Left Navigation Bar */
QFrame#sidebar {
    background-color: #131313;
    border-right: 1px solid #353534;
}
QPushButton#navBtn {
    background-color: transparent;
    color: #ac8888;
    border: none;
    border-radius: 6px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#navBtn:hover {
    background-color: #201f1f;
    color: #ffb3b3;
}
QPushButton#navBtn:checked {
    background-color: #201f1f;
    color: #ffb3b3;
    border-left: 3px solid #dc143c;
}
/* Cards & Containers */
QGroupBox {
    background-color: #131313;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 14px;
    font-size: 13px;
    font-weight: bold;
    color: #ffb3b3;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1a1a1a;
    border: 1px solid #353534;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    color: #e5e2e1;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #dc143c;
}
QPushButton#primaryBtn {
    background-color: #dc143c;
    color: #ffffff;
    border-radius: 6px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#primaryBtn:hover {
    background-color: #ff4d6d;
}
QPushButton#stopBtn {
    background-color: #920703;
    color: #ffffff;
    border-radius: 6px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#stopBtn:hover {
    background-color: #c91818;
}
QPushButton#secondaryBtn {
    background-color: #201f1f;
    color: #e5e2e1;
    border: 1px solid #353534;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#secondaryBtn:hover {
    background-color: #2a2a2a;
    color: #ffb3b3;
}
QTextEdit, QTableWidget {
    background-color: #0e0e0e;
    border: 1px solid #201f1f;
    border-radius: 6px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px;
    color: #e5e2e1;
}
QHeaderView::section {
    background-color: #1a1a1a;
    color: #ffb3b3;
    padding: 6px;
    border: 1px solid #201f1f;
    font-size: 13px;
    font-weight: bold;
}
"""
