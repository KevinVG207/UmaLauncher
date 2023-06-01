import copy
from loguru import logger
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import util
import threading
import requests

ICONS = qtw.QMessageBox.Icon

THREADER = None

APPLICATION = None


def show_widget(widget, *args, **kwargs):
    global APPLICATION

    if threading.main_thread() != threading.current_thread():
        if not THREADER:
            logger.error("Widget called from non-main thread without threader instance")
            return
        THREADER.widget_queue.append((widget, args, kwargs))
        return

    if not APPLICATION:
        logger.debug("Creating new QT app instance")
        APPLICATION = UmaApp()

    APPLICATION.run(widget(APPLICATION, *args, **kwargs))
    APPLICATION.close_widget()


def stop_application():
    global APPLICATION

    if APPLICATION:
        logger.debug("Closing QT app instance")
        APPLICATION.close()
        APPLICATION = None


class UmaApp():
    def __init__(self):
        self.app = qtw.QApplication([])
        self.app.setWindowIcon(qtg.QIcon(util.get_asset("favicon.ico")))
        self.main_widget = None

        self.init_app()

    def init_app(self):
        pass

    def run(self, main_widget: qtw.QWidget, retain_font=True):
        self.close_widget()

        if not retain_font:
            font = main_widget.font()
            font.setPointSizeF(8.75)
            main_widget.setFont(font)

        self.main_widget = main_widget
        self.main_widget.activateWindow()
        self.main_widget.setFocus(True)
        self.main_widget.raise_()
        self.app.exec_()
    
    def close_widget(self):
        if self.main_widget:
            self.main_widget.close()
            del self.main_widget
            self.main_widget = None

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


class UmaMainDialog(qtw.QDialog):
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


    def init_ui(self, *args, **kwargs):
        pass


class UmaPresetMenu(UmaMainWidget):
    default_preset = None
    selected_preset = None
    preset_list = None
    row_types_enum = None
    new_preset_class = None

    def init_ui(self, selected_preset, default_preset, new_preset_class, preset_list, row_types_enum, output_list, *args, **kwargs):
        self.selected_preset = selected_preset
        self.default_preset = default_preset
        self.preset_list = copy.deepcopy(preset_list)
        self.row_types_enum = row_types_enum
        self.new_preset_class = new_preset_class
        self.output_list = output_list

        self.resize(691, 471)
        # Disable resizing
        self.setFixedSize(self.size())
        self.setWindowFlags(qtc.Qt.WindowCloseButtonHint)

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
        self.cmb_select_preset.setGeometry(qtc.QRect(10, 20, 381, 22))
        self.cmb_select_preset.currentIndexChanged.connect(self.on_preset_change)

        self.but_toggle_elements = qtw.QPushButton(self.grp_preset_catalog)
        self.but_toggle_elements.setObjectName(u"but_toggle_elements")
        self.but_toggle_elements.setGeometry(qtc.QRect(400, 20, 101, 23))
        self.but_toggle_elements.setText(u"Toggle elements")
        self.but_toggle_elements.clicked.connect(self.on_toggle_elements)
        self.but_new_preset = qtw.QPushButton(self.grp_preset_catalog)
        self.but_new_preset.setObjectName(u"but_new_preset")
        self.but_new_preset.setGeometry(qtc.QRect(510, 20, 71, 23))
        self.but_new_preset.setText(u"New")
        self.but_new_preset.clicked.connect(self.on_new_preset)
        self.but_del_preset = qtw.QPushButton(self.grp_preset_catalog)
        self.but_del_preset.setObjectName(u"but_del_preset")
        self.but_del_preset.setGeometry(qtc.QRect(590, 20, 71, 23))
        self.but_del_preset.setText(u"Delete")
        self.but_del_preset.clicked.connect(self.on_delete_preset)
        self.grp_available_rows = qtw.QGroupBox(self)
        self.grp_available_rows.setObjectName(u"grp_available_rows")
        self.grp_available_rows.setGeometry(qtc.QRect(10, 60, 331, 311))
        self.grp_available_rows.setTitle(u"Available rows")
        self.lst_available = qtw.QListWidget(self.grp_available_rows)
        self.lst_available.setObjectName(u"lst_available")
        self.lst_available.setGeometry(qtc.QRect(10, 20, 311, 251))
        self.lst_available.itemSelectionChanged.connect(self.on_available_row_select)
        self.lst_available.itemDoubleClicked.connect(self.on_copy_to_preset)

        for row_data in row_types_enum:
            new_item = qtw.QListWidgetItem(self.lst_available)
            new_item.setText(row_data.value.long_name)
            new_item.setData(qtc.Qt.UserRole, row_data.name)
            new_item.setData(qtc.Qt.UserRole + 1, row_data.value())

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
        self.lst_current.itemSelectionChanged.connect(self.on_current_row_select)
        self.lst_current.itemDoubleClicked.connect(self.on_row_options)
        
        # Signal on drop
        self.lst_current.dropEvent = self.on_current_row_drop

        self.btn_delete_from_preset = qtw.QPushButton(self.grp_current_preset)
        self.btn_delete_from_preset.setObjectName(u"btn_delete_from_preset")
        self.btn_delete_from_preset.setGeometry(qtc.QRect(10, 280, 151, 23))
        self.btn_delete_from_preset.setText(u"Delete from current preset")
        self.btn_row_options = qtw.QPushButton(self.grp_current_preset)
        self.btn_row_options.setObjectName(u"btn_row_options")
        self.btn_row_options.setGeometry(qtc.QRect(170, 280, 151, 23))
        self.btn_row_options.setText(u"Row options")

        self.btn_copy_to_preset.clicked.connect(self.on_copy_to_preset)
        self.btn_delete_from_preset.clicked.connect(self.on_delete_from_preset)
        self.btn_row_options.clicked.connect(self.on_row_options)

        self.btn_close = qtw.QPushButton(self)
        self.btn_close.setObjectName(u"btn_close")
        self.btn_close.setGeometry(qtc.QRect(610, 440, 71, 23))
        self.btn_close.setText(u"Cancel")
        self.btn_close.setDefault(True)
        self.btn_close.clicked.connect(self.on_close)
        self.btn_apply = qtw.QPushButton(self)
        self.btn_apply.setObjectName(u"btn_apply")
        self.btn_apply.setGeometry(qtc.QRect(510, 440, 91, 23))
        self.btn_apply.setText("Apply && close")
        self.btn_apply.clicked.connect(self.on_apply)
        self.grp_help = qtw.QGroupBox(self)
        self.grp_help.setObjectName(u"grp_help")
        self.grp_help.setGeometry(qtc.QRect(10, 370, 671, 61))
        self.grp_help.setTitle(u"Help")
        self.lbl_description = qtw.QLabel(self.grp_help)
        self.lbl_description.setObjectName(u"lbl_description")
        self.lbl_description.setGeometry(qtc.QRect(10, 20, 651, 31))
        self.lbl_description.setText(u"Select a row to see its description.")
        self.lbl_description.setAlignment(qtc.Qt.AlignLeading|qtc.Qt.AlignLeft|qtc.Qt.AlignTop)
        self.lbl_description.setWordWrap(True)

        self.reload_preset_combobox()


    def closeEvent(self, event):
        self.close()

    @qtc.pyqtSlot()
    def on_close(self):
        self.close()
    
    @qtc.pyqtSlot()
    def on_apply(self):
        self.output_list.append(self.selected_preset)
        for preset in self.preset_list:
            self.output_list.append(preset)
        self.close()

    @qtc.pyqtSlot()
    def on_toggle_elements(self):
        current_preset_index = self.cmb_select_preset.currentIndex()
        current_preset = None
        # Get the preset object
        if current_preset_index <= 0:
            current_preset = self.default_preset
        else:
            current_preset = self.preset_list[current_preset_index - 1]
        current_preset.display_settings_dialog(self)

    @qtc.pyqtSlot()
    def on_new_preset(self):
        UmaNewPresetDialog(self, self.new_preset_class).exec()
        self.reload_preset_combobox()

    @qtc.pyqtSlot()
    def on_delete_preset(self):
        if self.cmb_select_preset.count() > 1:
            current_preset = self.cmb_select_preset.currentText()
            new_preset_list = []
            for preset in self.preset_list:
                if preset.name != current_preset:
                    new_preset_list.append(preset)
            self.preset_list = new_preset_list
            self.selected_preset = self.default_preset
            self.reload_preset_combobox()

    @qtc.pyqtSlot()
    def on_row_options(self):
        row = self.lst_current.currentItem()
        if row:
            row_object = row.data(qtc.Qt.UserRole + 1)
            if row_object.settings:
                row_object.display_settings_dialog(self)
                self.update_selected_preset_rows()

    @qtc.pyqtSlot()
    def on_available_row_select(self):
        self.show_row_description(self.lst_available.currentItem())

    @qtc.pyqtSlot()
    def on_current_row_drop(self, event):
        # Perform default drop event
        qtw.QListWidget.dropEvent(self.lst_current, event)

        self.update_selected_preset_rows()


    def update_selected_preset_rows(self):
        self.selected_preset.initialized_rows = []
        for i in range(self.lst_current.count()):
            row_object = self.lst_current.item(i).data(qtc.Qt.UserRole + 1)
            self.selected_preset.initialized_rows.append(row_object)


    @qtc.pyqtSlot()
    def on_current_row_select(self):
        current_item = self.lst_current.currentItem()
        self.show_row_description(current_item)
        if current_item:
            row_object = current_item.data(qtc.Qt.UserRole + 1)
            if row_object.settings:
                self.btn_row_options.setEnabled(True)
            else:
                self.btn_row_options.setEnabled(False)

    def show_row_description(self, item):
        if item and item.data(qtc.Qt.UserRole + 1).description:
            self.lbl_description.setText(item.data(qtc.Qt.UserRole + 1).description)
        else:
            self.lbl_description.setText("No description available.")

    @qtc.pyqtSlot()
    def on_copy_to_preset(self):
        if not self.lst_current.isEnabled():
            return
        selected_items = self.lst_available.selectedItems()
        for item in selected_items:
            # Check if item is already in the list
            if not self.lst_current.findItems(item.text(), qtc.Qt.MatchExactly):
                new_item = qtw.QListWidgetItem(self.lst_current)
                new_item.setText(item.text())
                new_item.setData(qtc.Qt.UserRole, item.data(qtc.Qt.UserRole))
                new_item.setData(qtc.Qt.UserRole + 1, type(item.data(qtc.Qt.UserRole + 1))())
                self.lst_current.setCurrentItem(new_item)
                self.update_selected_preset_rows()
            # Select the next item in the list
            next_row = self.lst_available.row(item) + 1
            if next_row < self.lst_available.count():
                self.lst_available.setCurrentRow(next_row)

    @qtc.pyqtSlot()
    def on_delete_from_preset(self):
        if not self.lst_current.isEnabled():
            return
        selected_items = self.lst_current.selectedItems()
        for item in selected_items:
            self.lst_current.takeItem(self.lst_current.row(item))
        self.update_selected_preset_rows()

    @qtc.pyqtSlot()
    def on_preset_change(self):
        index = self.cmb_select_preset.currentIndex()
        if index <= 0:
            self.selected_preset = self.default_preset
        else:
            self.selected_preset = self.preset_list[index - 1]
        self.reload_current_rows()

    def enable_current_preset(self):
        self.lst_current.setEnabled(True)
        self.btn_delete_from_preset.setEnabled(True)
        self.btn_copy_to_preset.setEnabled(True)
        self.btn_row_options.setEnabled(True)
        self.but_del_preset.setEnabled(True)
        self.but_toggle_elements.setEnabled(True)

    def disable_current_preset(self):
        self.lst_current.setEnabled(False)
        self.btn_delete_from_preset.setEnabled(False)
        self.btn_copy_to_preset.setEnabled(False)
        self.btn_row_options.setEnabled(False)
        self.but_del_preset.setEnabled(False)
        self.but_toggle_elements.setEnabled(False)

    def reload_current_rows(self):
        self.lst_current.clear()
        if self.selected_preset == self.default_preset:
            self.disable_current_preset()
        else:
            self.enable_current_preset()
        for row in self.selected_preset.initialized_rows:
            new_item = qtw.QListWidgetItem(self.lst_current)
            new_item.setText(row.long_name)
            new_item.setData(qtc.Qt.UserRole, self.row_types_enum(type(row)).name)
            new_item.setData(qtc.Qt.UserRole + 1, row)

    @qtc.pyqtSlot()
    def reload_preset_combobox(self):
        sel_preset_name = self.selected_preset.name
        self.cmb_select_preset.clear()
        self.cmb_select_preset.addItem(self.default_preset.name)
        self.preset_list.sort(key=lambda x: x.name.lower())
        for i, preset in enumerate(self.preset_list):
            self.cmb_select_preset.addItem(preset.name)
            if preset.name == sel_preset_name:
                self.cmb_select_preset.setCurrentIndex(i + 1)
                self.lst_current.setEnabled(True)
        self.reload_current_rows()


class UmaNewPresetDialog(UmaMainDialog):
    def init_ui(self, new_preset_class, *args, **kwargs):
        self.new_presets_class = new_preset_class

        self.resize(321, 121)
        # Disable resizing
        self.setFixedSize(self.size())
        self.setWindowFlags(qtc.Qt.WindowCloseButtonHint)
        self.setWindowTitle(u"New preset")
        self.lbl_instructions = qtw.QLabel(self)
        self.lbl_instructions.setObjectName(u"lbl_instructions")
        self.lbl_instructions.setGeometry(qtc.QRect(10, 10, 371, 16))
        self.lbl_instructions.setText(u"Enter new preset name:")
        self.lne_preset_name = qtw.QLineEdit(self)
        self.lne_preset_name.setObjectName(u"lne_preset_name")
        self.lne_preset_name.setGeometry(qtc.QRect(10, 30, 301, 20))
        self.lne_preset_name.setText(u"")
        self.btn_cancel = qtw.QPushButton(self)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setGeometry(qtc.QRect(230, 90, 81, 23))
        self.btn_cancel.setText(u"Cancel")
        self.btn_cancel.clicked.connect(self.close)
        self.btn_ok = qtw.QPushButton(self)
        self.btn_ok.setObjectName(u"btn_ok")
        self.btn_ok.setGeometry(qtc.QRect(140, 90, 81, 23))
        self.btn_ok.setText(u"OK")
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.on_ok)
        self.checkBox = qtw.QCheckBox(self)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setGeometry(qtc.QRect(10, 60, 121, 21))
        self.checkBox.setText(u"Copy existing:")
        self.comboBox = qtw.QComboBox(self)
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setEnabled(False)
        self.comboBox.setGeometry(qtc.QRect(108, 60, 201, 22))
        # Fill the combobox with presets.
        for preset in [self._parent.default_preset] + self._parent.preset_list:
            self.comboBox.addItem(preset.name)
        self.comboBox.setCurrentIndex(0)
        # Connect the checkbox to the combobox.
        self.checkBox.stateChanged.connect(self.on_checkbox_change)


    @qtc.pyqtSlot()
    def on_checkbox_change(self):
        if self.checkBox.isChecked():
            self.comboBox.setEnabled(True)
        else:
            self.comboBox.setEnabled(False)


    @qtc.pyqtSlot()
    def on_ok(self):
        if self.lne_preset_name.text() == "":
            UmaInfoPopup("Error", "Preset name cannot be empty.", ICONS.Critical).exec_()
            return

        names_list = [preset.name for preset in self._parent.preset_list + [self._parent.default_preset]]
        if self.lne_preset_name.text() in names_list:
            UmaInfoPopup("Error", "Preset with this name already exists.", ICONS.Critical).exec_()
            return
        
        # Check if the user wants to copy a preset.
        if self.checkBox.isChecked():
            selected_preset_name = self.comboBox.currentText()
            for preset in self._parent.preset_list + [self._parent.default_preset]:
                if preset.name == selected_preset_name:
                    selected_preset = preset
                    break
            new_preset = copy.deepcopy(selected_preset)

        else:
            new_preset = self.new_presets_class(self._parent.row_types_enum)

        new_preset.name = self.lne_preset_name.text()
        self._parent.preset_list.append(new_preset)

        self._parent.selected_preset = new_preset
        self.close()

class UmaPresetSettingsDialog(UmaMainDialog):
    settings_parent_object = None
    setting_types_enum = None
    setting_elements = None

    def init_ui(self, settings_parent_object, setting_types_enum, window_title="Change options", *args, **kwargs):
        self.setting_elements = {}
        self.settings_parent_object = settings_parent_object
        self.setting_types_enum = setting_types_enum

        self.resize(481, 401)
        # Disable resizing
        self.setFixedSize(self.size())
        self.setWindowFlags(qtc.Qt.WindowCloseButtonHint)
        self.setWindowTitle(window_title)
        self.scrollArea = qtw.QScrollArea(self)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(qtc.QRect(9, 9, 461, 351))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = qtw.QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(qtc.QRect(0, 0, 459, 349))
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setMinimumSize(qtc.QSize(0, 0))
        self.scrollAreaWidgetContents.setMaximumSize(qtc.QSize(16777215, 16777215))
        self.verticalLayout = qtw.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(f"verticalLayout")

        self.load_settings()

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.btn_cancel = qtw.QPushButton(self)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setGeometry(qtc.QRect(400, 370, 71, 23))
        self.btn_cancel.setText(u"Cancel")
        self.btn_cancel.setDefault(True)
        self.btn_save_close = qtw.QPushButton(self)
        self.btn_save_close.setObjectName(u"btn_save_close")
        self.btn_save_close.setGeometry(qtc.QRect(300, 370, 91, 23))
        self.btn_save_close.setText(u"Save && close")
        self.btn_restore = qtw.QPushButton(self)
        self.btn_restore.setObjectName(u"btn_restore")
        self.btn_restore.setGeometry(qtc.QRect(10, 370, 101, 23))
        self.btn_restore.setText(u"Restore defaults")

        self.btn_cancel.clicked.connect(self.close)
        self.btn_save_close.clicked.connect(self.save_and_close)
        self.btn_restore.clicked.connect(self.restore_defaults)

    def load_settings(self):
        # Empty the verticalLayout.
        for i in reversed(range(self.verticalLayout.count())):
            self.verticalLayout.itemAt(i).widget().setParent(None)

        # Adding group boxes to the scroll area
        settings_keys = self.settings_parent_object.settings.get_settings_keys()
        last_setting = settings_keys[-1]
        for setting_key in settings_keys:
            setting = getattr(self.settings_parent_object.settings, setting_key)
            group_box, value_func = self.add_group_box(setting)

            if not group_box:
                continue

            self.setting_elements[setting_key] = value_func

            if setting_key == last_setting:
                self.verticalLayout.addWidget(group_box, 0, qtc.Qt.AlignTop)
            else:
                self.verticalLayout.addWidget(group_box)
    
    def restore_defaults(self):
        self.settings_parent_object.settings = type(self.settings_parent_object.settings)()
        self.settings_elements = {}
        self.load_settings()
    
    def save_and_close(self):
        for setting_key, value_func in self.setting_elements.items():
            logger.debug(f"Setting {setting_key} to {value_func()}")
            getattr(self.settings_parent_object.settings, setting_key).value = value_func()

        self.close()


    def add_group_box(self, setting):
        grp_setting = qtw.QGroupBox(self.scrollAreaWidgetContents)
        grp_setting.setObjectName(f"grp_setting_{setting.name}")
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(grp_setting.sizePolicy().hasHeightForWidth())
        grp_setting.setSizePolicy(sizePolicy)
        grp_setting.setMinimumSize(qtc.QSize(0, 50))
        grp_setting.setTitle(setting.name)
        horizontalLayout = qtw.QHBoxLayout(grp_setting)
        horizontalLayout.setObjectName(f"horizontalLayout_{setting.name}")
        lbl_setting_description = qtw.QLabel(grp_setting)
        lbl_setting_description.setObjectName(u"lbl_setting_description")
        lbl_setting_description.setText(setting.description)
        lbl_setting_description.setWordWrap(True)

        horizontalLayout.addWidget(lbl_setting_description)

        input_widgets = []
        if setting.type == self.setting_types_enum.BOOL:
            input_widgets, value_func = self.add_checkbox(setting, grp_setting)
        elif setting.type == self.setting_types_enum.INT:
            input_widgets, value_func = self.add_spinbox(setting, grp_setting)
        elif setting.type == self.setting_types_enum.LIST:
            input_widgets, value_func = self.add_combobox(setting, grp_setting)
        elif setting.type == self.setting_types_enum.COLOR:
            input_widgets, value_func = self.add_colorpicker(setting, grp_setting)
        
        if not input_widgets:
            return None, None
        
        for input_widget in input_widgets:
            horizontalLayout.addWidget(input_widget)

        return grp_setting, value_func


    def add_checkbox(self, setting, parent):
        ckb_setting_checkbox = qtw.QCheckBox(parent)
        ckb_setting_checkbox.setObjectName(f"ckb_setting_{setting.name}")
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Maximum, qtw.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ckb_setting_checkbox.sizePolicy().hasHeightForWidth())
        ckb_setting_checkbox.setSizePolicy(sizePolicy)
        ckb_setting_checkbox.setText(u"")
        ckb_setting_checkbox.setChecked(setting.value)
        return [ckb_setting_checkbox], lambda: ckb_setting_checkbox.isChecked()

    def add_spinbox(self, setting, parent):
        spn_setting_spinbox = qtw.QSpinBox(parent)
        spn_setting_spinbox.setObjectName(f"spn_setting_{setting.name}")
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(spn_setting_spinbox.sizePolicy().hasHeightForWidth())
        spn_setting_spinbox.setSizePolicy(sizePolicy)
        spn_setting_spinbox.setMinimumSize(qtc.QSize(46, 0))
        spn_setting_spinbox.setAlignment(qtc.Qt.AlignRight|qtc.Qt.AlignVCenter)
        spn_setting_spinbox.setMinimum(setting.min_value)
        spn_setting_spinbox.setMaximum(setting.max_value)
        spn_setting_spinbox.setValue(setting.value)
        return [spn_setting_spinbox], lambda: spn_setting_spinbox.value()

    def add_combobox(self, setting, parent):
        cmb_setting_combobox = qtw.QComboBox(parent)
        cmb_setting_combobox.setObjectName(f"cmb_setting_{setting.name}")
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(cmb_setting_combobox.sizePolicy().hasHeightForWidth())
        cmb_setting_combobox.setSizePolicy(sizePolicy)
        cmb_setting_combobox.setMinimumSize(qtc.QSize(46, 0))
        
        for choice in setting.choices:
            cmb_setting_combobox.addItem(choice)

        cmb_setting_combobox.setCurrentIndex(setting.value)
        return [cmb_setting_combobox], lambda: cmb_setting_combobox.currentIndex()

    def add_colorpicker(self, setting, parent):
        lbl_picked_color = qtw.QLabel(parent)
        lbl_picked_color.setObjectName(f"lbl_picked_color_{setting.name}")
        sizePolicy3 = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(lbl_picked_color.sizePolicy().hasHeightForWidth())
        lbl_picked_color.setSizePolicy(sizePolicy3)
        lbl_picked_color.setMaximumSize(qtc.QSize(20, 20))
        lbl_picked_color.setAutoFillBackground(False)
        lbl_picked_color.setStyleSheet(f"background-color: {setting.value};")
        lbl_picked_color.setText("")

        lne_color_hex = qtw.QLineEdit(parent)
        lne_color_hex.setObjectName(f"lne_color_hex{setting.name}")
        sizePolicy4 = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(lne_color_hex.sizePolicy().hasHeightForWidth())
        lne_color_hex.setSizePolicy(sizePolicy4)
        lne_color_hex.setMaximumSize(qtc.QSize(52, 16777215))
        lne_color_hex.setText(setting.value)
        lne_color_hex.setMaxLength(7)

        def update_color():
            tmp_color = lne_color_hex.text()
            if not tmp_color.startswith("#") and len(tmp_color) == 6 and tmp_color.isalnum():
                tmp_color = "#" + tmp_color
            if tmp_color.startswith("#") and len(tmp_color) == 7 and tmp_color[1:].isalnum():
                lbl_picked_color.setStyleSheet(f"background-color: {tmp_color};")

        lne_color_hex.textChanged.connect(update_color)

        btn_pick_color = qtw.QPushButton(parent)
        btn_pick_color.setObjectName(f"btn_pick_color_{setting.name}")
        btn_pick_color.setMaximumSize(qtc.QSize(50, 16777215))
        btn_pick_color.setText("Picker")

        def pick_color():
            initial_color = qtg.QColor(lne_color_hex.text())
            if not initial_color.isValid():
                initial_color = qtg.QColor(setting.value)
            if not initial_color.isValid():
                initial_color = qtg.QColor("#000000")
            logger.debug(f"Initial color: {initial_color.name()}")
            tmp_color = qtw.QColorDialog.getColor(initial_color)
            if tmp_color.isValid():
                lne_color_hex.setText(tmp_color.name().upper())

        btn_pick_color.clicked.connect(pick_color)

        def get_color():
            out_color = None
            tmp_color = lne_color_hex.text()
            if not tmp_color.startswith("#") and len(tmp_color) == 6 and tmp_color.isalnum():
                tmp_color = "#" + tmp_color
            if tmp_color.startswith("#") and len(tmp_color) == 7 and tmp_color[1:].isalnum():
                out_color = tmp_color
            else:
                raise ValueError("Invalid color format")
            return out_color

        return [lbl_picked_color, lne_color_hex, btn_pick_color], lambda: get_color()



class UmaSimpleDialog(UmaMainDialog):
    def init_ui(self, title: str, message: str, *args, **kwargs):
        self.setWindowTitle(title)
        self.setWindowFlag(qtc.Qt.WindowType.WindowStaysOnTopHint, True)

        self.layout = qtw.QVBoxLayout()
        self.setLayout(self.layout)

        self.label = qtw.QLabel(message)
        self.label.setWordWrap(True)
        # Center label text
        self.label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)


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
        self.cancel_button.setDefault(True)
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
        self.close()

    @qtc.pyqtSlot()
    def _no(self):
        self.choice.append(1)
        self.close()

    @qtc.pyqtSlot()
    def _skip(self):
        self.choice.append(2)
        self.close()


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
            self.close()


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
            self.close()


class UmaInfoPopup(qtw.QMessageBox):
    def __init__(self, parent, title: str, message: str, msg_icon: qtw.QMessageBox.Icon = qtw.QMessageBox.Icon.Information):
        super().__init__()
        self.setWindowTitle(title)
        self.setText(message)

        msgbox_label = self.findChild(qtw.QLabel, "qt_msgbox_label")
        msgbox_label.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        msgbox_label.setTextFormat(qtc.Qt.TextFormat.RichText)
        msgbox_label.setTextInteractionFlags(qtc.Qt.TextInteractionFlag.TextBrowserInteraction)
        msgbox_label.setOpenExternalLinks(True)

        self.setWindowFlag(qtc.Qt.WindowType.WindowStaysOnTopHint, True)
        self.setIcon(msg_icon)
        self.show()


class UmaErrorPopup(qtw.QMessageBox):
    def __init__(self, parent, title: str, message: str, traceback_str: str, user_id: str, msg_icon: qtw.QMessageBox.Icon = qtw.QMessageBox.Icon.Information):
        super().__init__()
        self.setWindowTitle(title)
        self.setText(f"<b>{message}</b><br>{traceback_str}<br><b>You may send this error report to the developer to help fix this issue.</b>")
        upload_button = qtw.QPushButton("Send error report")
        upload_button.clicked.connect(lambda: self.upload_error_report(traceback_str, user_id))
        self.addButton(upload_button, qtw.QMessageBox.ButtonRole.AcceptRole)
        self.addButton(qtw.QPushButton("Close"), qtw.QMessageBox.ButtonRole.ActionRole)

        msgbox_label = self.findChild(qtw.QLabel, "qt_msgbox_label")
        msgbox_label.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        msgbox_label.setTextFormat(qtc.Qt.TextFormat.RichText)
        msgbox_label.setTextInteractionFlags(qtc.Qt.TextInteractionFlag.TextBrowserInteraction)
        msgbox_label.setOpenExternalLinks(True)

        self.setWindowFlag(qtc.Qt.WindowType.WindowStaysOnTopHint, True)
        self.setIcon(msg_icon)
        self.show()

    def upload_error_report(self, traceback_str, user_id):
        try:
            logger.debug("Uploading error report")
            resp = requests.post("https://umapyoi.net/api/v1/umalauncher/error", json={"traceback": traceback_str, "user_id": user_id})
            resp.raise_for_status()
        except Exception:
            util.show_error_box("Error", "Failed to upload error report.")
