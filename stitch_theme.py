STITCH_DARK_STYLESHEET = """
QMainWindow {
    background-color: #0B0C0E;
    color: #E2E8F0;
}
QWidget {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 12px;
    color: #E2E8F0;
}
/* Left Navigation Bar */
QFrame#sidebar {
    background-color: #121418;
    border-right: 1px solid #1E2228;
}
QPushButton#navBtn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#navBtn:hover {
    background-color: #1E2228;
    color: #F8FAFC;
}
QPushButton#navBtn:checked {
    background-color: #1E2228;
    color: #F8FAFC;
    border-left: 3px solid #DC143C;
}
/* Dashboard Cards */
QGroupBox {
    background-color: #121418;
    border: 1px solid #1E2228;
    border-radius: 8px;
    margin-top: 10px;
    padding: 12px 14px 12px 14px;
    font-size: 11px;
    font-weight: bold;
    color: #DC143C;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
/* Compact Symmetric Inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #181B20;
    border: 1px solid #282D35;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    color: #E2E8F0;
    min-height: 18px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #DC143C;
}
QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}
QPushButton#primaryBtn {
    background-color: #DC143C;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: bold;
    min-height: 18px;
}
QPushButton#primaryBtn:hover {
    background-color: #FF4D6D;
}
QPushButton#stopBtn {
    background-color: #991B1B;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: bold;
    min-height: 18px;
}
QPushButton#stopBtn:hover {
    background-color: #DC2626;
}
QPushButton#secondaryBtn {
    background-color: #181B20;
    color: #E2E8F0;
    border: 1px solid #282D35;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
    min-height: 18px;
}
QPushButton#secondaryBtn:hover {
    background-color: #282D35;
    color: #F8FAFC;
}
QTextEdit, QTableWidget {
    background-color: #08090A;
    border: 1px solid #1E2228;
    border-radius: 6px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 11px;
    color: #CBD5E1;
    padding: 4px;
}
QHeaderView::section {
    background-color: #181B20;
    color: #F8FAFC;
    padding: 6px;
    border: 1px solid #1E2228;
    font-size: 11px;
    font-weight: bold;
}
"""
