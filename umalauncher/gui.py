import copy
import math
from loguru import logger
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import util
import threading
import requests
import settings_elements as se
import version
import constants

ICONS = qtw.QMessageBox.Icon

THREADER = None

APPLICATION = None
CURRENTLY_RUNNING = False


def show_widget(widget, *args, **kwargs):
    global APPLICATION
    global CURRENTLY_RUNNING

    if threading.main_thread() != threading.current_thread():
        if not THREADER:
            logger.error("Widget called from non-main thread without threader instance")
            return
        THREADER.widget_queue.append((widget, args, kwargs))
        return

    if not APPLICATION:
        logger.debug("Creating new QT app instance")
        APPLICATION = UmaApp()
    
    if CURRENTLY_RUNNING:
        new_widget = widget(APPLICATION, *args, **kwargs)
        if hasattr(new_widget, "exec_"):
            new_widget.exec_()
        
        # Wait for widget to close
        while new_widget.isVisible():
            qtw.QApplication.processEvents()
        return

    CURRENTLY_RUNNING = True
    APPLICATION.run(widget(APPLICATION, *args, **kwargs))

    CURRENTLY_RUNNING = False


def stop_application():
    global APPLICATION

    if APPLICATION:
        logger.debug("Closing QT app instance")
        APPLICATION.close_widget()
        APPLICATION.close()
        APPLICATION = None


class UmaApp():
    def __init__(self):
        self.app = qtw.QApplication([])
        self.app.setWindowIcon(qtg.QIcon(util.get_asset("_assets/icon/default.ico")))
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
            self.main_widget.deleteLater()
            self.main_widget = None

    def close(self):
        self.app.exit()
        self.app.deleteLater()


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


class UmaPresetMenu(UmaMainDialog):
    default_preset = None
    selected_preset = None
    preset_list = None
    row_types_enum = None
    new_preset_class = None

    def init_ui(self, selected_preset, default_preset, new_preset_class, preset_list, scenario_preset_dict, row_types_enum, output_list, output_dict, *args, **kwargs):
        self.selected_preset = selected_preset
        self.default_preset = default_preset
        self.preset_list = copy.deepcopy(preset_list)
        self.scenario_preset_dict = copy.deepcopy(scenario_preset_dict)
        self.row_types_enum = row_types_enum
        self.new_preset_class = new_preset_class
        self.output_list = output_list
        self.output_dict = output_dict

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
        self.btn_copy_to_preset.setEnabled(False)
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
        self.btn_delete_from_preset.setEnabled(False)
        self.btn_row_options = qtw.QPushButton(self.grp_current_preset)
        self.btn_row_options.setObjectName(u"btn_row_options")
        self.btn_row_options.setGeometry(qtc.QRect(170, 280, 151, 23))
        self.btn_row_options.setText(u"Row options")
        self.btn_row_options.setEnabled(False)

        self.btn_copy_to_preset.clicked.connect(self.on_copy_to_preset)
        self.btn_delete_from_preset.clicked.connect(self.on_delete_from_preset)
        self.btn_row_options.clicked.connect(self.on_row_options)

        self.btn_close = qtw.QPushButton(self)
        self.btn_close.setObjectName(u"btn_close")
        self.btn_close.setGeometry(qtc.QRect(610, 440, 71, 23))
        self.btn_close.setText(u"Cancel")
        self.btn_close.setDefault(True)
        self.btn_close.clicked.connect(self._parent.cancel)
        self.btn_apply = qtw.QPushButton(self)
        self.btn_apply.setObjectName(u"btn_apply")
        self.btn_apply.setGeometry(qtc.QRect(510, 440, 91, 23))
        self.btn_apply.setText("Save && close")
        self.btn_apply.clicked.connect(self._parent.save_and_close)
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

        self.check_scenario_presets = qtw.QCheckBox(self)
        self.check_scenario_presets.setObjectName(u"check_scenario_presets")
        self.check_scenario_presets.setGeometry(qtc.QRect(10, 440, 161, 21))
        self.check_scenario_presets.setText(u"Enable per-scenario presets")
        self.check_scenario_presets.setChecked(self.output_dict[0])

        self.btn_scenario_presets = qtw.QPushButton(self)
        self.btn_scenario_presets.setObjectName(u"btn_scenario_presets")
        self.btn_scenario_presets.setGeometry(qtc.QRect(180, 440, 101, 23))
        self.btn_scenario_presets.setText(u"Scenario Presets")
        self.btn_scenario_presets.clicked.connect(self.on_scenario_presets)

        self.reload_preset_combobox()


    def closeEvent(self, event):
        self.close()

    @qtc.pyqtSlot()
    def on_close(self):
        self.close()
    
    @qtc.pyqtSlot()
    def save_settings(self):
        self.output_list.append(self.selected_preset)
        for preset in self.preset_list:
            self.output_list.append(preset)
        
        self.output_dict[0] = (self.check_scenario_presets.isChecked())
        self.output_dict.append(self.scenario_preset_dict)
        return True

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

            # Ask the user if they are sure.
            reply = qtw.QMessageBox.question(self, "Delete preset", f"Are you sure you want to delete preset '{current_preset}'?", qtw.QMessageBox.Yes | qtw.QMessageBox.No, qtw.QMessageBox.No)
            if reply == qtw.QMessageBox.No:
                return

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
        self.btn_copy_to_preset.setEnabled(True)
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
            self.btn_delete_from_preset.setEnabled(True)
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
    
    @qtc.pyqtSlot()
    def on_scenario_presets(self):
        UmaScenarioPresetDialog(self).exec_()


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
            UmaInfoPopup(self, "Error", "Preset name cannot be empty.", ICONS.Critical).exec_()
            return

        names_list = [preset.name for preset in self._parent.preset_list + [self._parent.default_preset]]
        if self.lne_preset_name.text() in names_list:
            UmaInfoPopup(self, "Error", "Preset with this name already exists.", ICONS.Critical).exec_()
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

class UmaSettingsDialog(UmaMainDialog):
    def init_ui(self, settings_var, tab=" General", window_title="Change options", command_dict={}, width_delta=0, *args, **kwargs):
        self.setting_elements = {}
        self.settings_var = settings_var
        self.tab = tab
        self.command_dict = command_dict

        self.resize(481 + width_delta, 401)
        # Disable resizing
        self.setFixedSize(self.size())
        self.setWindowFlags(qtc.Qt.WindowCloseButtonHint)
        self.setWindowTitle(window_title)
        self.scrollArea = qtw.QScrollArea(self)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(qtc.QRect(9, 9, 461 + width_delta, 351))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = qtw.QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(qtc.QRect(0, 0, 459 + width_delta, 349))
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

        self.btn_restore = qtw.QPushButton(self)
        self.btn_restore.setObjectName(u"btn_restore")
        self.btn_restore.setGeometry(qtc.QRect(10, 370, 101, 23))
        self.btn_restore.setText(u"Restore defaults")
        self.btn_restore.clicked.connect(self.restore_defaults)

        self.btn_cancel = qtw.QPushButton(self)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setGeometry(qtc.QRect(400 + width_delta, 370, 71, 23))
        self.btn_cancel.setText(u"Cancel")
        self.btn_cancel.setDefault(True)
        self.btn_save_close = qtw.QPushButton(self)
        self.btn_save_close.setObjectName(u"btn_save_close")
        self.btn_save_close.setGeometry(qtc.QRect(300 + width_delta, 370, 91, 23))
        self.btn_save_close.setText(u"Save && close")

    def load_settings(self):
        # Empty the verticalLayout.
        for i in reversed(range(self.verticalLayout.count())):
            widget = self.verticalLayout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
            else:
                self.verticalLayout.removeItem(self.verticalLayout.itemAt(i))

        # Adding group boxes to the scroll area
        settings_keys = self.settings_var[0].keys()
        last_setting = settings_keys[-1]
        for setting_key in settings_keys:
            setting = self.settings_var[0][setting_key]

            # Filter tab and priority
            if setting.hidden or setting.tab != self.tab:
                continue

            group_box, value_func = self.add_group_box(setting)

            if not group_box:
                continue
            
            # Only add elements that have a value_func.
            # This lets us add elements like messages.
            if value_func:
                self.setting_elements[setting_key] = value_func

            if setting_key == last_setting:
                self.verticalLayout.addWidget(group_box, 0, qtc.Qt.AlignTop)
            else:
                self.verticalLayout.addWidget(group_box)
        
        self.verticalSpacer = qtw.QSpacerItem(0, 0, qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Expanding)
        self.verticalLayout.addItem(self.verticalSpacer)
    
    def restore_defaults(self):
        default_settings_var = type(self.settings_var[0])()
        for setting_key in default_settings_var.keys():
            setting = getattr(default_settings_var, setting_key)
            if setting.priority < 0 or setting.tab != self.tab:
                continue
            logger.debug(f"Resetting {setting_key} to {setting.value}")
            getattr(self.settings_var[0], setting_key).value = setting.value

        self.settings_elements = {}
        self.load_settings()
    
    def save_settings(self):
        new_settings_dict = {}

        for setting_key, value_func in self.setting_elements.items():
            try:
                new_settings_dict[setting_key] = value_func()
            except ValueError:
                UmaInfoPopup(self, "Cannot save settings", f"Invalid value for {getattr(self.settings_var[0], setting_key).name}", ICONS.Critical).exec_()
                return False
        
        for key, value in new_settings_dict.items():
            logger.debug(f"Setting {key} to {value}")
            self.settings_var[0][key].value = value
        return True

    def add_group_box(self, setting):
        # If the setting is a divider, add a horizontal line.
        if setting.type == se.SettingType.DIVIDER:
            line = qtw.QFrame(self.scrollAreaWidgetContents)
            line.setObjectName(f"line_{setting.name}")
            line.setMinimumHeight(16)
            line.setLineWidth(0)
            line.setMidLineWidth(2)
            line.setFrameShape(qtw.QFrame.HLine)
            line.setFrameShadow(qtw.QFrame.Sunken)
            return line, None


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
        lbl_setting_description.setAlignment(qtc.Qt.AlignTop)
        lbl_setting_description.setOpenExternalLinks(True)

        # Make sure the label expands vertically to fit the text if it is very long.
        if setting.type == se.SettingType.MESSAGE:
            lbl_setting_description.setOpenExternalLinks(True)

        sizePolicy2 = qtw.QSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(lbl_setting_description.sizePolicy().hasHeightForWidth())
        lbl_setting_description.setSizePolicy(sizePolicy2)

        horizontalLayout.addWidget(lbl_setting_description)

        input_widgets = [None]
        value_func = None

        match setting.type:
            case se.SettingType.BOOL:
                input_widgets, value_func = self.add_checkbox(setting, grp_setting)
            case se.SettingType.INT:
                input_widgets, value_func = self.add_spinbox(setting, grp_setting)
            case se.SettingType.STRING:
                input_widgets, value_func = self.add_lineedit(setting, grp_setting)
            case se.SettingType.COMBOBOX:
                input_widgets, value_func = self.add_combobox(setting, grp_setting)
            case se.SettingType.COLOR:
                input_widgets, value_func = self.add_colorpicker(setting, grp_setting)
            case se.SettingType.RADIOBUTTONS:
                input_widgets, value_func = self.add_radiobuttons(setting, grp_setting)
            case se.SettingType.FILEDIALOG:
                input_widgets, value_func = self.add_filedialog(setting, grp_setting)
            case se.SettingType.FOLDERDIALOG:
                input_widgets, value_func = self.add_folderdialog(setting, grp_setting)
            case se.SettingType.XYWHSPINBOXES:
                input_widgets, value_func = self.add_multi_spinboxes(setting, grp_setting, ['Left', 'Top', 'Width', 'Height'])
            case se.SettingType.LRTBSPINBOXES:
                input_widgets, value_func = self.add_multi_spinboxes(setting, grp_setting, ['Left', 'Right', 'Top', 'Bottom'])
            case se.SettingType.COMMANDBUTTON:
                input_widgets, _ = self.add_commandbutton(setting, grp_setting)
        
        if not input_widgets:
            logger.debug(f"{setting.type} not implemented for {setting.name}")
            # Delete the group box if there are no input widgets.
            grp_setting.setParent(None)
            return None, None

        for input_widget in input_widgets:
            if input_widget:
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
    
    def add_radiobuttons(self, setting, parent):
        grp_box = qtw.QGroupBox(parent)
        grp_box.setObjectName(f"grp_box_{setting.name}")
        grp_box.setSizePolicy(qtw.QSizePolicy(qtw.QSizePolicy.Maximum, qtw.QSizePolicy.Maximum))
        grp_box.setStyleSheet("QGroupBox { border: 0; }")

        vert_layout = qtw.QVBoxLayout(grp_box)
        vert_layout.setObjectName(f"vert_layout_{setting.name}")
        vert_layout.setContentsMargins(0, 0, 0, 0)
        vert_layout.setSpacing(0)
        vert_layout.setAlignment(qtc.Qt.AlignTop)

        radio_buttons = []
        for choice, enabled in setting.value.items():
            rdb_setting_radiobutton = qtw.QRadioButton(grp_box)
            rdb_setting_radiobutton.setObjectName(f"rdb_setting_{setting.name}_{choice}")
            rdb_setting_radiobutton.setText(choice)
            rdb_setting_radiobutton.setChecked(enabled)
            vert_layout.addWidget(rdb_setting_radiobutton)
            radio_buttons.append(rdb_setting_radiobutton)

        return [grp_box], lambda: {rdb.text(): rdb.isChecked() for rdb in radio_buttons}

    def add_multi_spinboxes(self, setting, parent, names=['Left', 'Top', 'Width', 'Height']):
        grp_box = qtw.QGroupBox(parent)
        grp_box.setObjectName(f"grp_box_{setting.name}")
        grp_box.setSizePolicy(qtw.QSizePolicy(qtw.QSizePolicy.Maximum, qtw.QSizePolicy.Maximum))
        grp_box.setStyleSheet("QGroupBox { border: 0; }")

        vert_layout = qtw.QVBoxLayout(grp_box)
        vert_layout.setObjectName(f"vert_layout_{setting.name}")
        vert_layout.setContentsMargins(0, 0, 0, 0)
        vert_layout.setSpacing(0)
        vert_layout.setAlignment(qtc.Qt.AlignTop)

        spinboxes = []

        for i in range(len(names)):
            horizontalLayout = qtw.QHBoxLayout()
            horizontalLayout.setObjectName(f"horizontalLayout_{setting.name}_{names[i]}")
            horizontalLayout.setAlignment(qtc.Qt.AlignRight|qtc.Qt.AlignVCenter)
            horizontalLayout.setSpacing(3)

            lbl_setting_label = qtw.QLabel(grp_box)
            lbl_setting_label.setObjectName(f"lbl_setting_{setting.name}_{names[i]}")
            lbl_setting_label.setText(names[i])
            horizontalLayout.addWidget(lbl_setting_label)

            spn_setting_spinbox = qtw.QSpinBox(grp_box)
            spn_setting_spinbox.setMaximum(int(math.pow(2, 31) - 1))
            spn_setting_spinbox.setMinimum(int(-math.pow(2, 31)))
            spn_setting_spinbox.setObjectName(f"spn_setting_{setting.name}_{names[i]}")
            sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(spn_setting_spinbox.sizePolicy().hasHeightForWidth())
            spn_setting_spinbox.setSizePolicy(sizePolicy)
            spn_setting_spinbox.setMinimumSize(qtc.QSize(50, 0))
            spn_setting_spinbox.setAlignment(qtc.Qt.AlignRight|qtc.Qt.AlignVCenter)
            spn_setting_spinbox.setValue(setting.value[i] if setting.value and i < len(setting.value) else 0)
            
            horizontalLayout.addWidget(spn_setting_spinbox)
            vert_layout.addLayout(horizontalLayout)
            spinboxes.append(spn_setting_spinbox)
        
        def get_values():
            lst = [spn.value() for spn in spinboxes]
            if all(value == 0 for value in lst):
                return None
            return lst

        return [grp_box], lambda: get_values()

    def add_colorpicker(self, setting, parent):
        lbl_picked_color = qtw.QLabel(parent)
        lbl_picked_color.setObjectName(f"lbl_picked_color_{setting.name}")
        sizePolicy3 = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(lbl_picked_color.sizePolicy().hasHeightForWidth())
        lbl_picked_color.setSizePolicy(sizePolicy3)
        lbl_picked_color.setMaximumSize(qtc.QSize(20, 20))
        lbl_picked_color.setMinimumSize(qtc.QSize(20, 20))
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


    def add_filedialog(self, setting, parent):
        line_edit = qtw.QLineEdit(parent)
        line_edit.setObjectName(f"lineEdit_{setting.name}")
        line_edit.setMinimumSize(qtc.QSize(300, 0))
        line_edit.setMaximumSize(qtc.QSize(300, 16777215))
        line_edit.setText(setting.value)

        browse_button = qtw.QPushButton(parent)
        browse_button.setObjectName(f"pushButton_{setting.name}")
        sizePolicy4 = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(browse_button.sizePolicy().hasHeightForWidth())
        browse_button.setSizePolicy(sizePolicy4)
        browse_button.setMinimumSize(qtc.QSize(50, 0))
        browse_button.setMaximumSize(qtc.QSize(50, 16777215))
        browse_button.setText(u"Browse")

        def browse():
            tmp_path = qtw.QFileDialog.getOpenFileName(parent, "Select file", line_edit.text())
            if tmp_path[0]:
                line_edit.setText(tmp_path[0])

        browse_button.clicked.connect(browse)

        return [line_edit, browse_button], lambda: line_edit.text()


    def add_folderdialog(self, setting, parent):
        line_edit = qtw.QLineEdit(parent)
        line_edit.setObjectName(f"lineEdit_{setting.name}")
        line_edit.setMinimumSize(qtc.QSize(300, 0))
        line_edit.setMaximumSize(qtc.QSize(300, 16777215))
        line_edit.setText(setting.value)

        browse_button = qtw.QPushButton(parent)
        browse_button.setObjectName(f"pushButton_{setting.name}")
        sizePolicy4 = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(browse_button.sizePolicy().hasHeightForWidth())
        browse_button.setSizePolicy(sizePolicy4)
        browse_button.setMinimumSize(qtc.QSize(50, 0))
        browse_button.setMaximumSize(qtc.QSize(50, 16777215))
        browse_button.setText(u"Browse")

        def browse():
            tmp_path = qtw.QFileDialog.getExistingDirectory(parent, "Select folder", line_edit.text())
            if tmp_path:
                line_edit.setText(tmp_path)
            # tmp_path = qtw.QFileDialog.getOpenFileName(parent, "Select file", line_edit.text())
            # if tmp_path[0]:
            #     line_edit.setText(tmp_path[0])

        browse_button.clicked.connect(browse)

        return [line_edit, browse_button], lambda: line_edit.text()


    def add_lineedit(self, setting, parent):
        line_edit = qtw.QLineEdit(parent)
        line_edit.setObjectName(f"lineEdit_{setting.name}")
        line_edit.setMinimumSize(qtc.QSize(300, 0))
        line_edit.setMaximumSize(qtc.QSize(300, 16777215))
        line_edit.setText(setting.value)
        return [line_edit], lambda: line_edit.text()

    def add_commandbutton(self, setting, parent):
        btn_setting_button = qtw.QPushButton(parent)
        btn_setting_button.setObjectName(f"btn_setting_{setting.name}")
        btn_setting_button.setText(f" {setting.name} ")
        # Make the width of the button as small as possible to fit the text.
        size_policy = qtw.QSizePolicy(qtw.QSizePolicy.Maximum, qtw.QSizePolicy.Fixed)
        btn_setting_button.setSizePolicy(size_policy)

        btn_setting_button.clicked.connect(lambda: self.execute_btn_command(setting.value))
        return [btn_setting_button], None

    def execute_btn_command(self, value):
        if value in self.command_dict:
            self.setEnabled(False)
            self.command_dict[value]()
            self.setEnabled(True)


class UmaPresetSettingsDialog(UmaSettingsDialog):
    def init_ui(self, *args, **kwargs):
        super().init_ui(*args, **kwargs)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_save_close.clicked.connect(self.save_and_close)
    
    def save_and_close(self):
        success = self.save_settings()
        if success:
            self.close()


class UmaGeneralSettingsDialog(UmaSettingsDialog):
    def init_ui(self, *args, **kwargs):
        super().init_ui(*args, width_delta=210, **kwargs)
        self.btn_cancel.clicked.connect(self._parent.cancel)
        self.btn_save_close.clicked.connect(self._parent.save_and_close)

        # self.resize(481, 401)
        # delta = 210
        # self.setFixedWidth(self.width() + delta)
        # self.scrollArea.setFixedWidth(461 + delta)
        # self.scrollAreaWidgetContents.setFixedWidth(459 + delta)





class UmaPreferences(UmaMainWidget):
    def init_ui(self, umasettings, general_var, preset_dict, selected_preset, new_preset_list, default_preset, new_preset_class, new_scenario_preset_dict, row_types_enum, *args, **kwargs):
        self.previous_settings = copy.deepcopy(general_var[0])
        self.previous_presets = copy.deepcopy(preset_dict)
        self.previous_selected_preset = copy.deepcopy(selected_preset)

        self.general_var = general_var

        self.has_saved = False

        self.setWindowTitle("Preferences")
        self.tabWidget = qtw.QTabWidget(self)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Preferred)
        self.tabWidget.currentChanged.connect(self.tab_changed)

        unique_tabs = sorted(list({getattr(general_var[0], key).tab for key in general_var[0].keys()}))

        # # Hack
        # unique_tabs.append(unique_tabs.pop(unique_tabs.index("English Patch")))

        self.command_dict = {
            "open_training_logs": lambda: util.open_folder(util.TRAINING_LOGS_FOLDER)
        }

        self.settings_widgets = []

        for tab in unique_tabs:
            tab_widget = UmaGeneralSettingsDialog(self, general_var, tab=tab, command_dict=self.command_dict)
            tab_widget.setObjectName(f"tab_{tab}")
            self.settings_widgets.append(tab_widget)
            self.tabWidget.addTab(tab_widget, tab.lstrip(" "))

        # self.general_widget = UmaGeneralSettingsDialog(self, general_var)
        # # self.general_widget.setFixedSize(self.general_widget.size())
        # # self.general_widget.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)

        # self.tab_general = self.general_widget
        # self.tab_general.setObjectName("tab_general")
        # self.tabWidget.addTab(self.tab_general, "General")

        self.presets_widget = UmaPresetMenu(self,
            selected_preset=selected_preset,
            default_preset=default_preset,
            new_preset_class=new_preset_class,
            preset_list=list(preset_dict.values()),
            scenario_preset_dict=getattr(general_var[0], 'training_helper_table_scenario_presets').value,
            row_types_enum=row_types_enum,
            output_list=new_preset_list,
            output_dict=new_scenario_preset_dict
        )
        self.tab_presets = self.presets_widget
        self.tab_presets.setObjectName("tab_presets")
        self.tabWidget.addTab(self.tab_presets, "Helper Presets")

        self.tab_about = AboutDialog(self, umasettings)
        self.tab_about.setObjectName("tab_about")
        self.tabWidget.addTab(self.tab_about, "About")

        self.tabWidget.setCurrentIndex(0)

        # JANKY HACK M8
        self.setFixedSize(self.tabWidget.widget(0).size() + qtc.QSize(0, self.tabWidget.tabBar().height() - 9))

    def closeEvent(self, event):
        if not self.has_saved:
            self.cancel()

    def cancel(self):
        self.general_var[0] = self.previous_settings
        self.close()

    def tab_changed(self, index):
        current_widget = self.tabWidget.widget(index)
        if current_widget is not None:
            size = current_widget.size()
            # Add the height of the tab bar
            size.setHeight(size.height() + self.tabWidget.tabBar().height())

            self.tabWidget.resize(size)
            self.resize(size)
            self.setFixedSize(size)
    
    def save_and_close(self):
        # Save general settings
        for widget in self.settings_widgets:
            success = widget.save_settings()
            if not success:
                return

        # Save presets
        success = self.presets_widget.save_settings()
        if not success:
            return

        self.has_saved = True
        self.close()


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

class UmaRestartConfirm(UmaMainWidget):
    def init_ui(self, choice: list, *args, **kwargs):
        self.choice = choice

        self.setWindowTitle("Restart Required")
        self.setWindowFlag(qtc.Qt.WindowType.WindowStaysOnTopHint, True)

        self.layout = qtw.QVBoxLayout()
        self.setLayout(self.layout)

        self.label = qtw.QLabel("A game update was detected, and the game must be\nrestarted to reapply the English translations.\nWould you like Uma Launcher to restart the game right now?")
        # Center label text
        self.label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        self.button_layout = qtw.QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.left_horizontal_spacer = qtw.QSpacerItem(40, 20, qtw.QSizePolicy.Policy.Expanding, qtw.QSizePolicy.Policy.Minimum)
        self.button_layout.addItem(self.left_horizontal_spacer)

        self.yes_button = qtw.QPushButton("Yes")
        self.yes_button.clicked.connect(self._yes)
        self.yes_button.setDefault(True)
        self.button_layout.addWidget(self.yes_button)

        self.no_button = qtw.QPushButton("No")
        self.no_button.clicked.connect(self._no)
        self.button_layout.addWidget(self.no_button)

        self.right_horizontal_spacer = qtw.QSpacerItem(40, 20, qtw.QSizePolicy.Policy.Expanding, qtw.QSizePolicy.Policy.Minimum)
        self.button_layout.addItem(self.right_horizontal_spacer)

        # Hide maxminize and minimize buttons
        self.setWindowFlag(qtc.Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowFlag(qtc.Qt.WindowType.WindowMinimizeButtonHint, False)

    @qtc.pyqtSlot()
    def _yes(self):
        self.choice.append(True)
        self.close()

    @qtc.pyqtSlot()
    def _no(self):
        self.choice.append(False)
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
        self.setText(f"<b>{message}<br>You may send this error report to the developer to help fix this issue.<br>If an error appears multiple times, please join the <a href=\"https://discord.gg/wvGHW65C6A\">Discord server</a>, because the developer might need your help to fix the issue.</b><br>{traceback_str}")
        upload_button = qtw.QPushButton("Send error report")
        upload_button.clicked.connect(lambda: self.upload_error_report(traceback_str, user_id))
        self.addButton(upload_button, qtw.QMessageBox.ButtonRole.ActionRole)
        self.addButton(qtw.QPushButton("Close"), qtw.QMessageBox.ButtonRole.RejectRole)

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
            version_str = version.VERSION
            if util.is_script:
                version_str += ".script"
            resp = requests.post("https://umapyoi.net/api/v1/umalauncher/error", json={"traceback": traceback_str, "user_id": user_id, "version": version_str})
            resp.raise_for_status()
        except Exception:
            util.show_error_box("Error", "Failed to upload error report.")

class AboutDialog(UmaMainDialog):
    def init_ui(self, settings, *args, **kwargs):
        self.settings = settings

        super().init_ui(*args, **kwargs)

        self.resize(481 + 210, 401)
        self.setFixedSize(self.size())
        self.verticalLayoutWidget = qtw.QWidget(self)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(qtc.QRect(0, 0, 481 + 210, 401))
        self.verticalLayout = qtw.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.lbl_header = qtw.QLabel(self.verticalLayoutWidget)
        self.lbl_header.setObjectName(u"lbl_header")
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_header.sizePolicy().hasHeightForWidth())
        self.lbl_header.setSizePolicy(sizePolicy)
        self.lbl_header.setLayoutDirection(qtc.Qt.LeftToRight)
        self.lbl_header.setText(u"<html><head/><body><p><br><span style=\" font-size:12pt; font-weight:600;\">Uma Launcher</span></p></body></html>")
        self.lbl_header.setAlignment(qtc.Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbl_header)

        self.lbl_version = qtw.QLabel(self.verticalLayoutWidget)
        self.lbl_version.setObjectName(u"lbl_version")
        sizePolicy.setHeightForWidth(self.lbl_version.sizePolicy().hasHeightForWidth())
        self.lbl_version.setSizePolicy(sizePolicy)
        self.lbl_version.setLayoutDirection(qtc.Qt.LeftToRight)
        self.lbl_version.setText(f"Version {version.VERSION}")
        self.lbl_version.setAlignment(qtc.Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbl_version)

        self.lbl_about = qtw.QLabel(self.verticalLayoutWidget)
        self.lbl_about.setObjectName(u"lbl_about")
        sizePolicy.setHeightForWidth(self.lbl_about.sizePolicy().hasHeightForWidth())
        self.lbl_about.setSizePolicy(sizePolicy)
        self.lbl_about.setLayoutDirection(qtc.Qt.LeftToRight)
        self.lbl_about.setText("""<html><head><meta name="qrichtext" content="1" /><style type="text/css">p, li { white-space: pre-wrap; }</style></head><body style=" font-family:'MS Shell Dlg 2'; font-size:8pt; font-weight:400; font-style:normal;"><p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Created by KevinVG207 and <a href="https://github.com/KevinVG207/UmaLauncher/graphs/contributors">Contributors</a><br /><a href="https://github.com/KevinVG207/UmaLauncher"><span style=" text-decoration: underline; color:#0000ff;">Github</span></a> - <a href="https://umapyoi.net/uma-launcher"><span style=" text-decoration: underline; color:#0000ff;">Website</span></a> - <a href="https://twitter.com/kevinvg207"><span style=" text-decoration: underline; color:#0000ff;">Twitter</span></a></p><a href="https://github.com/KevinVG207/UmaLauncher/blob/main/FAQ.md">Frequently Asked Questions</a></p><p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><b>Special thanks to:</b><br /><a href="https://github.com/CNA-Bld"><span style=" text-decoration: underline; color:#0000ff;">CNA-Bld</span></a> for the race data parser and CarrotJuicer.<br /></p></body></html>""")
        self.lbl_about.setOpenExternalLinks(True)
        self.lbl_about.setAlignment(qtc.Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbl_about)

        self.horizontalLayout = qtw.QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btn_update = qtw.QPushButton(self.verticalLayoutWidget)
        self.btn_update.setObjectName(u"btn_update")
        sizePolicy1 = qtw.QSizePolicy(qtw.QSizePolicy.Maximum, qtw.QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_update.sizePolicy().hasHeightForWidth())
        self.btn_update.setSizePolicy(sizePolicy1)
        self.btn_update.setText(u" Check for updates ")
        self.btn_update.setDefault(True)
        self.btn_update.clicked.connect(self.update_check)

        self.horizontalLayout.addWidget(self.btn_update)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.lbl_unique_header = qtw.QLabel(self.verticalLayoutWidget)
        self.lbl_unique_header.setObjectName(u"lbl_unique_header")
        self.lbl_unique_header.setText(u"Unique ID:")
        self.lbl_unique_header.setAlignment(qtc.Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbl_unique_header)

        self.lbl_unique = qtw.QLabel(self.verticalLayoutWidget)
        self.lbl_unique.setObjectName(u"lbl_unique")
        self.lbl_unique.setText(self.settings['unique_id'])
        self.lbl_unique.setAlignment(qtc.Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lbl_unique)

        self.horizontalLayout_2 = qtw.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btn_refresh_id = qtw.QPushButton(self.verticalLayoutWidget)
        self.btn_refresh_id.setObjectName(u"btn_refresh_id")
        sizePolicy1.setHeightForWidth(self.btn_refresh_id.sizePolicy().hasHeightForWidth())
        self.btn_refresh_id.setSizePolicy(sizePolicy1)
        self.btn_refresh_id.setText(u" Refresh unique ID ")
        self.btn_refresh_id.clicked.connect(self.on_refresh_id)

        self.horizontalLayout_2.addWidget(self.btn_refresh_id)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalSpacer = qtw.QSpacerItem(20, 40, qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)
    
    def update_check(self):
        self.btn_update.setEnabled(False)
        result = version.auto_update(self.settings, force=True)
        if result:
            util.show_info_box("No updates found", "You are running the latest version of Uma Launcher.")
        self.btn_update.setEnabled(True)
    
    def on_refresh_id(self):
        self.settings.regenerate_unique_id()
        self.lbl_unique.setText(self.settings['unique_id'])


class UmaScenarioPresetDialog(UmaMainDialog):
    def init_ui(self):
        self.setObjectName(u"UmaScenarioPresetDialog")
        self.resize(391, 371)
        self.setFixedSize(self.size())
        self.setWindowFlag(qtc.Qt.WindowContextHelpButtonHint, False)

        self.setWindowTitle(u"Set Scenario Presets")

        self.scrollArea = qtw.QScrollArea(self)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(qtc.QRect(0, 0, 391, 331))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = qtw.QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(qtc.QRect(0, 0, 389, 329))

        self.verticalLayout = qtw.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")

        current_presets = self._parent.scenario_preset_dict
        self.comboboxes = []

        # Fill the layout with scenario preset comboboxes
        for scenario_id, scenario_name in constants.SCENARIO_DICT.items():
            hzl = qtw.QHBoxLayout()
            hzl.setObjectName(f"hzl_scenario_{scenario_id}")
            hzl.setContentsMargins(-1, 5, -1, 5)
            lbl_scenario = qtw.QLabel(self.scrollAreaWidgetContents)
            lbl_scenario.setObjectName(f"lbl_scenario_{scenario_id}")
            lbl_scenario.setText(scenario_name)

            hzl.addWidget(lbl_scenario)

            cmb_preset = qtw.QComboBox(self.scrollAreaWidgetContents)
            cmb_preset.setObjectName(f"cmb_preset_{scenario_id}")
            # Save scenario_id in object data
            cmb_preset.setProperty("scenario_id", str(scenario_id))

            self.comboboxes.append(cmb_preset)

            hzl.addWidget(cmb_preset)
            
            current_preset = current_presets.get(str(scenario_id), None)
            set_index = 0

            for i, preset in enumerate([self._parent.default_preset] + self._parent.preset_list):
                cmb_preset.addItem(preset.name)
                if current_preset is not None and current_preset == preset.name:
                    set_index = i
            
            cmb_preset.setCurrentIndex(set_index)

            self.verticalLayout.addLayout(hzl)

        self.verticalSpacer = qtw.QSpacerItem(20, 40, qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.btn_cancel = qtw.QPushButton(self)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setGeometry(qtc.QRect(300, 340, 81, 23))
        self.btn_cancel.setText(u"Cancel")
        self.btn_cancel.setDefault(True)
        self.btn_cancel.clicked.connect(self.cancel)

        self.btn_ok = qtw.QPushButton(self)
        self.btn_ok.setObjectName(u"btn_ok")
        self.btn_ok.setGeometry(qtc.QRect(210, 340, 81, 23))
        self.btn_ok.setText(u"Apply")
        self.btn_ok.clicked.connect(self.save)


    def save(self):
        out_dict = {}
        for cmb in self.comboboxes:
            scenario_id = cmb.property("scenario_id")
            out_dict[scenario_id] = cmb.currentText()
        self._parent.scenario_preset_dict = out_dict
        self.close()
    
    def cancel(self):
        self.close()
