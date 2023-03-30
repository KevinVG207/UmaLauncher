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

    def run(self, main_widget: qtw.QWidget, retain_font=False):

        if not retain_font:
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


class UmaPresetMenu(UmaMainWidget):
    default_preset = None
    selected_preset = None
    preset_list = None
    row_types_dict = None

    def init_ui(self, selected_preset, default_preset, preset_list, row_types_dict, *args, **kwargs):
        self.selected_preset = selected_preset
        self.default_preset = default_preset
        self.preset_list = preset_list
        self.row_types_dict = row_types_dict

        self.resize(691, 471)
        self.setWindowTitle(u"Customize Helper Table")
        self.grp_preset_catalog = qtw.QGroupBox(self)
        self.grp_preset_catalog.setObjectName(u"grp_preset_catalog")
        self.grp_preset_catalog.setGeometry(qtc.QRect(10, 10, 671, 51))
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Maximum, qtw.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.grp_preset_catalog.sizePolicy().hasHeightForWidth())
        self.grp_preset_catalog.setSizePolicy(sizePolicy)
        self.grp_preset_catalog.setTitle(u"Preset catalog")
        self.cmb_select_preset = qtw.QComboBox(self.grp_preset_catalog)
        self.cmb_select_preset.setObjectName(u"cmb_select_preset")
        self.cmb_select_preset.setGeometry(qtc.QRect(10, 20, 491, 22))
        self.but_new_preset = qtw.QPushButton(self.grp_preset_catalog)
        self.but_new_preset.setObjectName(u"but_new_preset")
        self.but_new_preset.setGeometry(qtc.QRect(510, 20, 71, 23))
        self.but_new_preset.setText(u"New")
        self.but_del_preset = qtw.QPushButton(self.grp_preset_catalog)
        self.but_del_preset.setObjectName(u"but_del_preset")
        self.but_del_preset.setGeometry(qtc.QRect(590, 20, 71, 23))
        self.but_del_preset.setText(u"Delete")
        self.grp_available_rows = qtw.QGroupBox(self)
        self.grp_available_rows.setObjectName(u"grp_available_rows")
        self.grp_available_rows.setGeometry(qtc.QRect(10, 60, 331, 311))
        self.grp_available_rows.setTitle(u"Available rows")
        self.lst_available = qtw.QListWidget(self.grp_available_rows)

        for key, row in self.row_types_dict.items():
            new_item = qtw.QListWidgetItem(self.lst_available)
            new_item.setText(row.long_name)
            new_item.setData(qtc.Qt.UserRole, key)
            new_item.setData(qtc.Qt.UserRole + 1, row)
            print(new_item.data(qtc.Qt.UserRole))
            print(new_item.data(qtc.Qt.UserRole + 1))

        self.lst_available.setObjectName(u"lst_available")
        self.lst_available.setGeometry(qtc.QRect(10, 20, 311, 251))
        self.btn_copy_to_preset = qtw.QPushButton(self.grp_available_rows)
        self.btn_copy_to_preset.setObjectName(u"btn_copy_to_preset")
        self.btn_copy_to_preset.setGeometry(qtc.QRect(10, 280, 311, 23))
        sizePolicy1 = qtw.QSizePolicy(qtw.QSizePolicy.Maximum, qtw.QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_copy_to_preset.sizePolicy().hasHeightForWidth())
        self.btn_copy_to_preset.setSizePolicy(sizePolicy1)
        self.btn_copy_to_preset.setText(u"Copy to current preset \u2192")
        self.grp_current_preset = qtw.QGroupBox(self)
        self.grp_current_preset.setObjectName(u"grp_current_preset")
        self.grp_current_preset.setGeometry(qtc.QRect(350, 60, 331, 311))
        self.grp_current_preset.setTitle(u"Current preset")
        self.lst_current = qtw.QListWidget(self.grp_current_preset)
        __qlistwidgetitem1 = qtw.QListWidgetItem(self.lst_current)
        __qlistwidgetitem1.setText(u"1");
        self.lst_current.setObjectName(u"lst_current")
        self.lst_current.setGeometry(qtc.QRect(10, 20, 311, 251))
        self.lst_current.setDragEnabled(True)
        self.lst_current.setDragDropMode(qtw.QAbstractItemView.DragDrop)
        self.lst_current.setDefaultDropAction(qtc.Qt.MoveAction)
        self.btn_delete_from_preset = qtw.QPushButton(self.grp_current_preset)
        self.btn_delete_from_preset.setObjectName(u"btn_delete_from_preset")
        self.btn_delete_from_preset.setGeometry(qtc.QRect(10, 280, 311, 23))
        self.btn_delete_from_preset.setText(u"Delete from current preset")
        self.btn_close = qtw.QPushButton(self)
        self.btn_close.setObjectName(u"btn_close")
        self.btn_close.setGeometry(qtc.QRect(610, 440, 71, 23))
        self.btn_close.setText(u"Close")
        self.btn_apply = qtw.QPushButton(self)
        self.btn_apply.setObjectName(u"btn_apply")
        self.btn_apply.setGeometry(qtc.QRect(530, 440, 71, 23))
        self.btn_apply.setText(u"Apply")
        self.grp_help = qtw.QGroupBox(self)
        self.grp_help.setObjectName(u"grp_help")
        self.grp_help.setGeometry(qtc.QRect(10, 370, 671, 61))
        self.grp_help.setTitle(u"Help")
        self.label = qtw.QLabel(self.grp_help)
        self.label.setObjectName(u"label")
        self.label.setGeometry(qtc.QRect(10, 20, 651, 31))
        self.label.setText(u"DESCRIPTION.")
        self.label.setAlignment(qtc.Qt.AlignLeading|qtc.Qt.AlignLeft|qtc.Qt.AlignTop)
        self.label.setWordWrap(True)

        self.reload_preset_combobox()


    def reload_current_rows(self):
        self.lst_current.clear()
        for row_key in self.selected_preset.rows:
            row = self.row_types_dict[row_key]
            new_item = qtw.QListWidgetItem(self.lst_current)
            new_item.setText(row.long_name)
            new_item.setData(qtc.Qt.UserRole, row_key)
            new_item.setData(qtc.Qt.UserRole + 1, row)

    def reload_preset_combobox(self):
        self.cmb_select_preset.clear()
        self.cmb_select_preset.addItem(self.default_preset.name, -1)
        set_current_index = False
        for i, preset in enumerate(self.preset_list):
            self.cmb_select_preset.addItem(preset.name, i)
            if preset == self.selected_preset:
                self.cmb_select_preset.setCurrentIndex(i + 1)
                set_current_index = True
                print("Set current index to", i + 1)
        
        if not set_current_index:
            self.cmb_select_preset.setCurrentIndex(0)

        self.reload_current_rows()


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
