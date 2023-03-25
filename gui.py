import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import util

ICONS = qtw.QMessageBox.Icon

class UmaApp():
    app = None
    main_widget = None

    def __init__(self):
        self.app = qtw.QApplication([])
        self.app.setWindowIcon(qtg.QIcon(util.get_asset("favicon.ico")))

        self.init_app()

    def init_app(self):
        pass

    def run(self, main_widget: qtw.QWidget):

        font = main_widget.font()
        font.setPointSizeF(8.75)
        main_widget.setFont(font)

        self.main_widget = main_widget
        self.app.exec_()

    def close(self):
        self.app.exit()
        del self.app


class UmaMainWidget(qtw.QWidget):
    _parent = None

    def __init__(self, parent: UmaApp, *args, **kwargs):
        self._parent = parent
        super().__init__()

        # Init defaults
        self.setWindowTitle("Uma Launcher")

        # Init unique
        self.init_ui(*args, **kwargs)

        # Generate geometry before showing, otherwise centering doesn't work
        self.adjustSize()

        # Center widget to primary screen        
        screen = qtw.QDesktopWidget().primaryScreen()
        screen_size = qtw.QDesktopWidget().screenGeometry(screen)
        self.move(screen_size.center() - self.rect().center())

        self.raise_()

        self.show()


    def init_ui(self, *args, **kwargs):
        pass


class UmaUpdateConfirm(UmaMainWidget):
    choice = None

    def init_ui(self, latest_release, release_version, choice: list, *args, **kwargs):
        self.choice = choice
        self.setWindowTitle("Update Available")
        self.setWindowFlag(qtc.Qt.WindowType.WindowStaysOnTopHint, True)

        self.layout = qtw.QVBoxLayout()
        self.setLayout(self.layout)

        self.label = qtw.QLabel(f"""A new version of Uma Launcher was found.\nVersion: {'Pre-release ' if latest_release.get('prerelease', False) else ''}{release_version}\nUpdate now?""")
        self.label.setWordWrap(True)
        # Center label text
        self.label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        self.button_layout = qtw.QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.update_button = qtw.QPushButton("Yes")
        self.update_button.clicked.connect(self._yes)
        self.button_layout.addWidget(self.update_button)

        self.cancel_button = qtw.QPushButton("No")
        self.cancel_button.clicked.connect(self._no)
        self.button_layout.addWidget(self.cancel_button)

        self.skip_button = qtw.QPushButton("Skip this version")
        self.skip_button.clicked.connect(self._skip)
        self.button_layout.addWidget(self.skip_button)

        # Hide maxminize and minimize buttons
        self.setWindowFlag(qtc.Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowFlag(qtc.Qt.WindowType.WindowMinimizeButtonHint, False)


    @qtc.pyqtSlot()
    def _yes(self):
        self.choice.append(0)
        self._parent.close()

    @qtc.pyqtSlot()
    def _no(self):
        self.choice.append(1)
        self._parent.close()

    @qtc.pyqtSlot()
    def _skip(self):
        self.choice.append(2)
        self._parent.close()


class UmaBorderlessPopup(UmaMainWidget):
    update_object = None
    timer = None

    def init_ui(self, title, message, update_object, check_target, interval=250, *args, **kwargs):
        self.update_object = update_object
        self.check_target = check_target

        self.setWindowTitle(title)
        self.setWindowFlag(qtc.Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(qtc.Qt.WindowType.FramelessWindowHint, True)
        self.layout = qtw.QVBoxLayout()
        self.setLayout(self.layout)
        self.label = qtw.QLabel(message)
        self.label.setWordWrap(False)
        # Center label text
        self.label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        self.label.setContentsMargins(10, 20, 10, 20)
        self.layout.addWidget(self.label)
        # Hide maxminize and minimize buttons
        self.setWindowFlag(qtc.Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowFlag(qtc.Qt.WindowType.WindowMinimizeButtonHint, False)

        # Call function every X ms
        self.timer = qtc.QTimer(self)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self._update)
        self.timer.start()

    @qtc.pyqtSlot()
    def _update(self):
        if len(self.check_target) > 0:
            self.timer.stop()
            self._parent.close()


class UmaUpdatePopup(UmaMainWidget):
    update_object = None
    timer = None

    def init_ui(self, update_object, *args, **kwargs):
        self.update_object = update_object

        self.setWindowTitle("Updating")
        self.setWindowFlag(qtc.Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(qtc.Qt.WindowType.FramelessWindowHint, True)

        self.layout = qtw.QVBoxLayout()
        self.setLayout(self.layout)

        self.label = qtw.QLabel("Please wait while Uma Launcher updates...")
        self.label.setWordWrap(False)

        # Center label text
        self.label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        self.label.setContentsMargins(10, 20, 10, 20)
        self.layout.addWidget(self.label)

        # Hide maxminize and minimize buttons
        self.setWindowFlag(qtc.Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowFlag(qtc.Qt.WindowType.WindowMinimizeButtonHint, False)

        # Call function every 250 ms
        self.timer = qtc.QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._update)
        self.timer.start()

    @qtc.pyqtSlot()
    def _update(self):
        if self.update_object.close_me:
            self.timer.stop()
            self._parent.close()


class UmaInfoPopup(qtw.QMessageBox):
    def __init__(self, title: str, message: str, msg_icon: qtw.QMessageBox.Icon = qtw.QMessageBox.Icon.Information):
        super().__init__()
        self.setWindowTitle(title)
        self.setText(message)
        self.findChild(qtw.QLabel, "qt_msgbox_label").setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        self.setWindowFlag(qtc.Qt.WindowType.WindowStaysOnTopHint, True)
        self.setIcon(msg_icon)
        self.show()
