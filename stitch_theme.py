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

/* Left Sidebar (Fixed 240px) */
QFrame#sidebar {
    background-color: #121212;
    border-right: 1px solid #2A2A2A;
}

QPushButton#navBtn {
    background-color: transparent;
    color: #ac8888;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-family: 'Inter';
    font-size: 13px;
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

/* Layer 1 Pane Surfaces (16px radius, #121212 fill) */
QFrame#panelCard {
    background-color: #121212;
    border: 1px solid #2A2A2A;
    border-radius: 16px;
}

/* Uniform Card Header Bar (11px JetBrains Mono, 28px Height) */
QLabel#cardHeader {
    background-color: #1A1A1A;
    color: #ffb3b3;
    font-family: 'JetBrains Mono';
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.08em;
    padding: 6px 12px;
    min-height: 16px;
    max-height: 16px;
    border-top-left-radius: 15px;
    border-top-right-radius: 15px;
    border-bottom: 1px solid #2A2A2A;
}

/* Input Fields (12px Radius, #1A1A1A fill) */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1A1A1A;
    border: 1px solid #353534;
    border-radius: 12px;
    padding: 8px 12px;
    font-family: 'Inter';
    font-size: 13px;
    color: #e5e2e1;
    min-height: 20px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #dc143c;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

/* Primary Crimson Button (#DC143C Fill, 12px Radius) */
QPushButton#primaryBtn {
    background-color: #dc143c;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    padding: 10px 18px;
    font-family: 'Inter';
    font-size: 13px;
    font-weight: 700;
}
QPushButton#primaryBtn:hover {
    background-color: #bf0030;
}

/* Secondary Ghost Button */
QPushButton#secondaryBtn {
    background-color: transparent;
    color: #ffb3b3;
    border: 1px solid #dc143c;
    border-radius: 12px;
    padding: 8px 14px;
    font-family: 'Inter';
    font-size: 13px;
    font-weight: 600;
}
QPushButton#secondaryBtn:hover {
    background-color: #1A1A1A;
    color: #ffffff;
}

/* Stop Button (#920703) */
QPushButton#stopBtn {
    background-color: #920703;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    padding: 10px 18px;
    font-family: 'Inter';
    font-size: 13px;
    font-weight: 700;
}
QPushButton#stopBtn:hover {
    background-color: #690000;
}

/* System Progress Gauges */
QProgressBar {
    border: 1px solid #2A2A2A;
    border-radius: 6px;
    text-align: center;
    background-color: #1A1A1A;
    color: #e5e2e1;
    font-family: 'JetBrains Mono';
    font-size: 10px;
    font-weight: 700;
    max-height: 14px;
}
QProgressBar::chunk {
    background-color: #dc143c;
    border-radius: 5px;
}

/* Terminal Console (#000000 Fill, JetBrains Mono) */
QTextEdit, QTableWidget {
    background-color: #000000;
    border: 1px solid #2A2A2A;
    border-radius: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #BC8F8F;
    padding: 8px;
}
QHeaderView::section {
    background-color: #1A1A1A;
    color: #ffb3b3;
    padding: 8px;
    border: 1px solid #2A2A2A;
    font-family: 'JetBrains Mono';
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
}
"""
