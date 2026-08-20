APP_QSS = r"""
* {
    font-family: "Segoe UI Variable Text", "Segoe UI";
}

QMainWindow, QWidget#AppRoot, QWidget#PageCanvas {
    background: rgb(17,17,17);
    color: #f4f4f5;
}

QLabel, QFrame { border: none; }

QFrame#TopRail {
    background: rgba(22,22,23,235);
    border: 1px solid #303033;
    border-radius: 31px;
}
QWidget#NavZone, QWidget#ToolZone { background: transparent; }

QPushButton#NavPill {
    background: #242425;
    border: none;
    border-radius: 23px;
    min-height: 46px; max-height: 46px;
    color: #b8b8bc;
    padding: 0 17px;
    font-size: 13px;
}
QPushButton#NavPill:hover { background:#2b2b2d; color:white; }
QPushButton#NavPill:checked { background:#29292b; color:white; }

QPushButton#CircleButton {
    background:#242425; border:none; border-radius:23px;
    min-width:46px; max-width:46px; min-height:46px; max-height:46px;
    color:#bbbcc0; font-size:15px;
}
QLabel#Profile {
    background:#eeeeef; color:#171719; border-radius:23px;
    min-width:46px; max-width:46px; min-height:46px; max-height:46px;
    font-weight:700;
}

QLabel#PageTitle { font-size:30px; font-weight:650; color:#f7f7f8; }
QLabel#PageSubtitle { font-size:11px; color:#777b82; }
QLabel#Eyebrow { font-size:9px; font-weight:700; color:#777b82; }
QLabel#HeroState { font-size:31px; font-weight:450; color:white; }
QLabel#SectionTitle { font-size:15px; font-weight:650; color:#f0f0f1; }
QLabel#Muted { font-size:10px; color:#7b7e84; }
QLabel#Value { font-size:22px; color:white; font-weight:500; }
QLabel#Tiny { font-size:9px; color:#65686e; }

QFrame#GlassCard {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(33,33,34,244),
        stop:0.48 rgba(29,29,30,244),
        stop:1 rgba(24,24,25,244));
    border:none; border-radius:25px;
}
QFrame#GlassSoft {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(31,31,32,235),
        stop:1 rgba(25,25,26,235));
    border:none; border-radius:21px;
}
QFrame#InnerRow {
    background: rgba(255,255,255,10);
    border:none; border-radius:16px;
}

QLineEdit#CommandBox {
    background:rgba(10,10,11,65);
    border:none; border-radius:25px;
    min-height:50px; padding:0 19px;
    color:#f5f5f6; font-size:12px;
}
QPushButton#LightPill {
    background:#f5f5f4; color:#171719; border:none; border-radius:21px;
    min-height:42px; padding:0 19px; font-weight:650;
}
QPushButton#DarkPill {
    background:rgba(255,255,255,12); color:#bbbcc1; border:none;
    border-radius:20px; min-height:40px; padding:0 16px;
}
QPushButton#DarkPill:hover { background:rgba(255,255,255,20); color:white; }

QLabel#Good {
    color:#72dfa7; background:rgba(56,145,96,40);
    border-radius:11px; padding:4px 9px; font-size:9px; font-weight:700;
}


/* -------------------------------------------------------------------------
   E.V.I.E. OS status blocks
   ------------------------------------------------------------------------- */

QFrame#StatusGood {
    background: rgba(64, 191, 118, 52);
    border: 1px solid rgba(96, 224, 145, 52);
    border-radius: 15px;
}

QFrame#StatusWarn {
    background: rgba(226, 171, 75, 44);
    border: 1px solid rgba(236, 191, 97, 46);
    border-radius: 15px;
}

QFrame#StatusBad {
    background: rgba(224, 89, 95, 42);
    border: 1px solid rgba(242, 108, 115, 48);
    border-radius: 15px;
}

QLabel#StatusBlockTitle {
    color: #f0f2f1;
    font-size: 11px;
    font-weight: 650;
}

QLabel#StatusBlockValueGood {
    color: #79e2aa;
    font-size: 10px;
    font-weight: 750;
}

QLabel#StatusBlockValueWarn {
    color: #edc272;
    font-size: 10px;
    font-weight: 750;
}

QLabel#StatusBlockValueBad {
    color: #f48389;
    font-size: 10px;
    font-weight: 750;
}

QLabel#UpdatedAt {
    color: #5f636a;
    font-size: 9px;
}

QLabel#Transcript {
    color: #d7d9dc;
    background: rgba(255,255,255,8);
    border-radius: 13px;
    padding: 8px 12px;
    font-size: 11px;
}


/* -------------------------------------------------------------------------
   Navbar favicon / avatar polish
   ------------------------------------------------------------------------- */

QPushButton#NavPill {
    text-align: center;
}

QPushButton#CircleButton {
    padding: 0px;
}

QPushButton#CircleButton:hover {
    background: #2d2d30;
}

QPushButton#CircleButton:pressed {
    background: #353538;
}

QLabel#ProfileAvatar {
    background: transparent;
    border: none;
}

/* -------------------------------------------------------------------------
   Settings / notification dialog polish
   ------------------------------------------------------------------------- */

QDialog {
    background: #141415;
    color: #f4f4f5;
}

QDialog QTabWidget::pane {
    background: rgba(255,255,255,5);
    border: none;
    border-radius: 18px;
}

QDialog QTabBar::tab {
    background: transparent;
    border: none;
    color: #777b82;
    padding: 10px 18px;
    margin-right: 4px;
}

QDialog QTabBar::tab:selected {
    background: rgba(255,255,255,10);
    color: #f4f4f5;
    border-radius: 12px;
}

QDialog QCheckBox {
    color: #c8c9cc;
    spacing: 10px;
    padding: 4px;
}

QDialog QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    background: rgba(255,255,255,10);
    border: 1px solid rgba(255,255,255,15);
}

QDialog QCheckBox::indicator:checked {
    background: rgba(94,211,145,90);
    border: 1px solid rgba(105,225,156,110);
}

QDialog QDialogButtonBox QPushButton {
    background: rgba(255,255,255,10);
    color: #d7d8db;
    border: none;
    border-radius: 15px;
    min-height: 34px;
    padding: 0 16px;
}

QDialog QDialogButtonBox QPushButton:hover {
    background: rgba(255,255,255,18);
    color: white;
}


/* -------------------------------------------------------------------------
   In-app utility panel layer
   ------------------------------------------------------------------------- */

QWidget#PanelLayer {
    background: rgba(8,8,9,105);
}

QFrame#OverlayPanel {
    background: rgba(22,22,23,249);
    border: 1px solid rgba(255,255,255,15);
    border-radius: 28px;
}

QLabel#PanelClose {
    color: #aaaeb5;
    background: rgba(255,255,255,9);
    border-radius: 17px;
    font-size: 23px;
    font-weight: 300;
}

QLabel#PanelClose:hover {
    color: white;
    background: rgba(255,255,255,18);
}

QFrame#OverlayPanel QTabWidget::pane {
    background: rgba(255,255,255,5);
    border: none;
    border-radius: 18px;
}

QFrame#OverlayPanel QTabBar::tab {
    background: transparent;
    border: none;
    color: #777b82;
    padding: 10px 18px;
    margin-right: 4px;
}

QFrame#OverlayPanel QTabBar::tab:selected {
    background: rgba(255,255,255,10);
    color: #f4f4f5;
    border-radius: 12px;
}

QFrame#OverlayPanel QCheckBox {
    color: #c8c9cc;
    spacing: 10px;
    padding: 4px;
}

QFrame#OverlayPanel QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    background: rgba(255,255,255,10);
    border: 1px solid rgba(255,255,255,15);
}

QFrame#OverlayPanel QCheckBox::indicator:checked {
    background: rgba(94,211,145,90);
    border: 1px solid rgba(105,225,156,110);
}

QLabel#ProfileAvatar {
    background: transparent;
    border: none;
}


/* -------------------------------------------------------------------------
   Final V1 conversation surface
   ------------------------------------------------------------------------- */

QFrame#ChatUser {
    background: rgba(80, 95, 125, 38);
    border: 1px solid rgba(150, 170, 215, 20);
    border-radius: 18px;
}

QFrame#ChatAssistant {
    background: rgba(255,255,255,8);
    border: 1px solid rgba(255,255,255,9);
    border-radius: 18px;
}

QLabel#ChatText {
    color: #dedfe2;
    font-size: 12px;
}

QPushButton:disabled, QLineEdit:disabled {
    color: #55575c;
    background: rgba(255,255,255,5);
}

QPushButton#NavPill:disabled {
    color: #4c4f55;
    background: #1b1b1c;
}
"""
