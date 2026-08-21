"""AirSlide light and dark visual systems."""

from __future__ import annotations


LIGHT = {
    "bg": "#F3F5F7", "surface": "#FFFFFF", "surface2": "#E9EDF1",
    "text": "#1D252C", "muted": "#64717C", "border": "#D9E0E5",
    "accent": "#2F7658", "accent_hover": "#28674D", "camera": "#151B1F",
}
DARK = {
    "bg": "#171B1E", "surface": "#22282C", "surface2": "#2C3439",
    "text": "#EDF1F3", "muted": "#A8B1B7", "border": "#3A444A",
    "accent": "#62A984", "accent_hover": "#74B795", "camera": "#101315",
}


def stylesheet(dark: bool) -> str:
    c = DARK if dark else LIGHT
    return f"""
    * {{ font-family: 'Segoe UI'; font-size: 10pt; color: {c['text']}; }}
    QMainWindow, QDialog {{ background: {c['bg']}; }}
    QWidget#card, QFrame#card {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 14px; }}
    QLabel#title {{ font-size: 22pt; font-weight: 700; }}
    QLabel#subtitle, QLabel#muted {{ color: {c['muted']}; }}
    QLabel#section {{ font-size: 12pt; font-weight: 700; }}
    QLabel#camera {{ background: {c['camera']}; color: #B9C2C8; border-radius: 14px; }}
    QLabel#action {{ background: {c['accent']}; color: white; border-radius: 10px; font-size: 14pt; font-weight: 700; padding: 12px; }}
    QPushButton {{ background: {c['surface2']}; border: 1px solid {c['border']}; border-radius: 9px; padding: 8px 14px; font-weight: 600; }}
    QPushButton:hover {{ border-color: {c['accent']}; }}
    QPushButton#primary {{ background: {c['accent']}; color: white; border: none; padding: 13px 24px; font-size: 11pt; }}
    QPushButton#primary:hover {{ background: {c['accent_hover']}; }}
    QComboBox, QSpinBox, QDoubleSpinBox {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 7px; padding: 6px 8px; min-height: 22px; }}
    QGroupBox {{ border: 1px solid {c['border']}; border-radius: 10px; margin-top: 12px; padding: 14px 10px 8px; font-weight: 700; background: {c['surface']}; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 5px; }}
    QTabWidget::pane {{ border: 1px solid {c['border']}; border-radius: 10px; background: {c['surface']}; }}
    QTabBar::tab {{ padding: 9px 16px; color: {c['muted']}; }}
    QTabBar::tab:selected {{ color: {c['accent']}; font-weight: 700; }}
    QCheckBox {{ spacing: 8px; }}
    QProgressBar {{ border: none; background: {c['surface2']}; border-radius: 5px; height: 10px; text-align: center; }}
    QProgressBar::chunk {{ background: {c['accent']}; border-radius: 5px; }}
    """
