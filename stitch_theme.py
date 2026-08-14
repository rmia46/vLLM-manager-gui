STITCH_DARK_STYLESHEET = """
QMainWindow {
    background-color: #0A0A0A;
    color: #e5e2e1;
}
QWidget {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 12px;
    color: #e5e2e1;
}

/* Left Sidebar (Fixed 240px) */
QFrame#sidebar {
    background-color: #121212;
    border-right: 1px solid #2A2A2A;
}

QPushButton#navBtn {
    background-color: transparent;
    color: #ac8888;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    text-align: left;
    font-family: 'Inter';
    font-size: 12px;
    font-weight: 600;
}
QPushButton#navBtn:hover {
    background-color: #1A1A1A;
    color: #ffb3b3;
}
QPushButton#navBtn:checked {
    background-color: #1A1A1A;
    color: #ffb3b3;
    border-left: 3px solid #dc143c;
}

/* Layer 1 Pane Surfaces */
QFrame#panelCard {
    background-color: #121212;
    border: 1px solid #2A2A2A;
    border-radius: 12px;
}

/* Uniform Card Header Bar */
QLabel#cardHeader {
    background-color: #1A1A1A;
    color: #ffb3b3;
    font-family: 'JetBrains Mono';
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.08em;
    padding: 5px 12px;
    min-height: 15px;
    max-height: 15px;
    border-top-left-radius: 11px;
    border-top-right-radius: 11px;
    border-bottom: 1px solid #2A2A2A;
}

/* Sweetspot Input Fields */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1A1A1A;
    border: 1px solid #353534;
    border-radius: 8px;
    padding: 6px 10px;
    font-family: 'Inter';
    font-size: 12px;
    color: #e5e2e1;
    min-height: 18px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #dc143c;
}
QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

/* Sweetspot Primary Crimson Button */
QPushButton#primaryBtn {
    background-color: #dc143c;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 7px 15px;
    font-family: 'Inter';
    font-size: 12px;
    font-weight: 700;
    min-height: 18px;
}
QPushButton#primaryBtn:hover {
    background-color: #bf0030;
}

/* Sweetspot Secondary Ghost Button */
QPushButton#secondaryBtn {
    background-color: transparent;
    color: #ffb3b3;
    border: 1px solid #dc143c;
    border-radius: 8px;
    padding: 6px 12px;
    font-family: 'Inter';
    font-size: 12px;
    font-weight: 600;
    min-height: 18px;
}
QPushButton#secondaryBtn:hover {
    background-color: #1A1A1A;
    color: #ffffff;
}

/* Sweetspot Stop Button */
QPushButton#stopBtn {
    background-color: #920703;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 7px 15px;
    font-family: 'Inter';
    font-size: 12px;
    font-weight: 700;
    min-height: 18px;
}
QPushButton#stopBtn:hover {
    background-color: #690000;
}

/* System Progress Gauges */
QProgressBar {
    border: 1px solid #2A2A2A;
    border-radius: 4px;
    text-align: center;
    background-color: #1A1A1A;
    color: #e5e2e1;
    font-family: 'JetBrains Mono';
    font-size: 10px;
    font-weight: 700;
    max-height: 13px;
}
QProgressBar::chunk {
    background-color: #dc143c;
    border-radius: 3px;
}

/* Terminal Console (#000000 Fill, JetBrains Mono) */
QTextEdit, QTableWidget {
    background-color: #000000;
    border: 1px solid #2A2A2A;
    border-radius: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #BC8F8F;
    padding: 6px;
}
QHeaderView::section {
    background-color: #1A1A1A;
    color: #ffb3b3;
    padding: 6px;
    border: 1px solid #2A2A2A;
    font-family: 'JetBrains Mono';
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
}
"""
