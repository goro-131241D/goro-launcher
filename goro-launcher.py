import sys
import subprocess
import yaml
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QMenu,
    QSystemTrayIcon, QSizePolicy
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QSharedMemory, QAbstractNativeEventFilter
import win32gui
import win32con
import win32api
import win32process
import pywintypes
import ctypes
from ctypes import wintypes
import uuid
import traceback  # エラーハンドリング用

# グローバル変数の初期化
menu_path = 'menu.yaml'
tray_icon = None
exiting = False
hot_key = 'ctrl+alt+n'  # デフォルトのホットキー
key_map = '1234567890abcdefghijklmnopqrstuvwxyz'  # デフォルトのキー割り当て
HOTKEY_ID = uuid.uuid4().int & 0xFFFF  # ユニークな HOTKEY_ID を生成
menu_data = []  # メニューのデータを格納

###############################
# 設定ファイルの読み込み関数
###############################

def load_config(config_path):
    global hot_key, key_map, menu_data
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        menu_data = config.get("menu", [])
        hot_key = config.get("hot_key", hot_key)
        key_map = config.get("key_map", key_map)
        print(f"Loaded hotkey: {hot_key}")
        print(f"Loaded key map: {key_map}")
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        menu_data = []
    except yaml.YAMLError as e:
        print(f"YAML Error: {e}")
        menu_data = []
    except Exception as e:
        print(f"Error loading config: {e}")
        menu_data = []

###############################
# ホットキー文字列のパース関数
###############################

def parse_hotkey(hotkey_str):
    modifier_keys = {
        'ctrl': win32con.MOD_CONTROL,
        'alt': win32con.MOD_ALT,
        'shift': win32con.MOD_SHIFT,
        'win': win32con.MOD_WIN,
    }
    special_keys = {
        'f1': win32con.VK_F1,
        'f2': win32con.VK_F2,
        'f3': win32con.VK_F3,
        'f4': win32con.VK_F4,
        'f5': win32con.VK_F5,
        'f6': win32con.VK_F6,
        'f7': win32con.VK_F7,
        'f8': win32con.VK_F8,
        'f9': win32con.VK_F9,
        'f10': win32con.VK_F10,
        'f11': win32con.VK_F11,
        'f12': win32con.VK_F12,
        'home': win32con.VK_HOME,
        'end': win32con.VK_END,
        'insert': win32con.VK_INSERT,
        'delete': win32con.VK_DELETE,
        'left': win32con.VK_LEFT,
        'right': win32con.VK_RIGHT,
        'up': win32con.VK_UP,
        'down': win32con.VK_DOWN,
        'esc': win32con.VK_ESCAPE,
        'escape': win32con.VK_ESCAPE,
        'space': win32con.VK_SPACE,
        'tab': win32con.VK_TAB,
        'enter': win32con.VK_RETURN,
        'return': win32con.VK_RETURN,
        'backspace': win32con.VK_BACK,
        'apps': win32con.VK_APPS,
        'capital': win32con.VK_CAPITAL,
        'capslock': win32con.VK_CAPITAL,
        'printscreen': win32con.VK_SNAPSHOT,
        'scrolllock': win32con.VK_SCROLL,
        'pause': win32con.VK_PAUSE,
        'numlock': win32con.VK_NUMLOCK,
    }

    modifiers = 0
    vk = None
    keys = hotkey_str.lower().split('+')
    for key in keys:
        key = key.strip()
        if key in modifier_keys:
            modifiers |= modifier_keys[key]
        elif key in special_keys:
            vk = special_keys[key]
        elif len(key) == 1:
            vk = ord(key.upper())
        else:
            raise ValueError(f"Unknown key: {key}")
    if vk is None:
        raise ValueError(f"No key specified in hotkey: {hotkey_str}")
    return modifiers, vk

###############################
# Hotkey Registration Functions
###############################

def register_hotkey():
    global hot_key, HOTKEY_ID
    try:
        modifiers, vk = parse_hotkey(hot_key)
        win32gui.RegisterHotKey(None, HOTKEY_ID, modifiers, vk)
        print(f"Hotkey registered: {hot_key}")
    except ValueError as ve:
        print(f"Invalid hotkey: {ve}")
        sys.exit(1)
    except pywintypes.error as e:
        print(f"Failed to register hotkey. Error: {traceback.format_exc()}")
        sys.exit(1)

def unregister_hotkey():
    try:
        ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
        print("Hotkey unregistered")
    except pywintypes.error as e:
        print(f"Failed to unregister hotkey: {traceback.format_exc()}")

class HotkeyEventFilter(QAbstractNativeEventFilter):
    def nativeEventFilter(self, eventType, message):
        if eventType == "windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(message.__int__())
            if msg.message == win32con.WM_HOTKEY:
                if msg.wParam == HOTKEY_ID:
                    controller.toggle_window()
                return True, 0
        return False, 0

###############################
# Class WindowController
###############################

class WindowController(QObject):
    show_signal = pyqtSignal()
    hide_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.window = None
        self.create_window()

    def create_window(self):
        if not self.window:
            try:
                self.window = LauncherWindow(menu_data)
                self.show_signal.connect(self.window.show)
                self.hide_signal.connect(self.window.hide)
            except Exception as e:
                print(f"Error creating LauncherWindow: {traceback.format_exc()}")

    def show_window(self):
        if not self.window:
            self.create_window()
        self.show_signal.emit()

    def hide_window(self):
        self.hide_signal.emit()

    def toggle_window(self):
        if self.window and self.window.isVisible():
            self.hide_window()
        else:
            self.show_window()

    def close_window(self):
        if self.window:
            self.window.close()
            self.window = None

###############################
# Class MyButton
###############################

class MyButton(QPushButton):
    def keyPressEvent(self, event):
        parent = self.parent()
        if parent:
            parent.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

###############################
# Class LauncherWindow
###############################

class LauncherWindow(QWidget):

    def __init__(self, menu_data):
        super().__init__()
        self.setWindowTitle("Goro Launcher")
        self.menu_data = menu_data
        self.buttons = []
        self.current_index = 0
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.grabKeyboard()
        self.init_ui()
        self.dragging = False
        self.drag_position = None
        self.current_menu = None

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        try:
            self.load_menu()
            if self.buttons:
                self.buttons[self.current_index].setFocus()
            else:
                self.hide()
        except Exception as e:
            print(f"Error initializing UI: {traceback.format_exc()}")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

    def load_menu(self):
        global key_map
        self.current_menu = self.menu_data
        self.show_menu(self.current_menu)

    def show_menu(self, menu_items):
        self.clear_layout(self.layout)
        self.buttons = []

        if not menu_items:
            self.hide()
            return

        button_width = 200
        button_height = 30

        button_style = """
            QPushButton {
                text-align: left;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QPushButton:focus {
                background-color: #d0d0ff;
                border: 2px solid #0000ff;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """

        for index, item in enumerate(menu_items):
            try:
                key_label = key_map[index] if index < len(key_map) else str(index + 1)
                button_text = f"{key_label}: {item['name']}"
                button = MyButton(button_text, self)
                button.setFixedSize(button_width, button_height)
                button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                button.setStyleSheet(button_style)
                button.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
                button.clicked.connect(
                    lambda checked=False, idx=index, itm=item: self.handle_button_click(idx, itm)
                )

                self.layout.addWidget(button)
                self.buttons.append(button)

            except Exception as e:
                print(f"Error creating button for menu item '{item}': {traceback.format_exc()}")

        self.adjustSize()
        self.setMinimumSize(self.sizeHint())
        self.setMaximumSize(self.sizeHint())
        self.setFocus()

        if self.buttons:
            self.buttons[self.current_index].setFocus()

        self.current_index = 0
        self.update()

    def reset_menu(self):
        self.current_menu = self.menu_data
        self.current_index = 0
        self.show_menu(self.current_menu)

    def show(self):
        self.reset_menu()
        if self.buttons:
            super().show()
            QApplication.processEvents()
            QTimer.singleShot(0, self.set_focus)
        else:
            self.hide()

    def set_focus(self):
        self.raise_()
        self.activateWindow()
        self.setFocus()
        if self.buttons:
            self.buttons[0].setFocus()
        self.simulate_click()

    def hide(self):
        self.reset_menu()
        super().hide()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def handle_button_click(self, index, item):
        try:
            if "items" in item and item["items"]:
                self.current_menu = item["items"]
                self.show_menu(item["items"])
            else:
                command = item.get("command")
                if command:
                    self.launch(command)
                else:
                    print(f"handle_button_click: No command specified.")
                self.hide()
        except Exception as e:
            print(f"Error in handle_button_click: {traceback.format_exc()}")
            self.hide()

    def launch(self, cmd):
        if cmd:
            try:
                subprocess.Popen(
                    cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            except Exception as e:
                print(f"launch: Command execution failed.: {traceback.format_exc()}")
            finally:
                self.hide()

    def eventFilter(self, source, event):
        global key_map
        if event.type() == event.Type.KeyPress:
            key = event.key()
            key_text = event.text().lower()

            if key in [Qt.Key.Key_Kanji, Qt.Key.Key_Hiragana, Qt.Key.Key_Katakana]:
                event.accept()
                return True

            if key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Tab, Qt.Key.Key_Return,
                       Qt.Key.Key_Enter, Qt.Key.Key_Escape] or key_text in key_map:
                if key == Qt.Key.Key_Up:
                    self.navigate_up()
                    event.accept()
                    return True
                elif key == Qt.Key.Key_Down:
                    self.navigate_down()
                    event.accept()
                    return True
                elif key == Qt.Key.Key_Tab:
                    self.navigate_down()
                    event.accept()
                    return True
                elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    current_focus = self.focusWidget()
                    if current_focus in self.buttons:
                        current_focus.click()
                    event.accept()
                    return True
                elif key_text in key_map and key_text != '':
                    index = key_map.index(key_text)
                    if 0 <= index < len(self.buttons):
                        self.buttons[index].click()
                    event.accept()
                    return True
                elif key == Qt.Key.Key_Escape:
                    self.hide()
                    event.accept()
                    return True
                else:
                    event.accept()
                    return True
            else:
                event.ignore()
                return False

        return super().eventFilter(source, event)

    def navigate_up(self):
        current_focus = self.focusWidget()
        if current_focus in self.buttons:
            current_index = self.buttons.index(current_focus)
            next_index = (current_index - 1) % len(self.buttons)
            self.buttons[next_index].setFocus()

    def navigate_down(self):
        current_focus = self.focusWidget()
        if current_focus in self.buttons:
            current_index = self.buttons.index(current_focus)
            next_index = (current_index + 1) % len(self.buttons)
            self.buttons[next_index].setFocus()

    def keyPressEvent(self, event):
        global key_map
        try:
            key = event.key()
            key_text = event.text().lower()

            if key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape] or key_text in key_map:
                if key == Qt.Key.Key_Up:
                    self.navigate_up()
                    event.accept()
                elif key == Qt.Key.Key_Down:
                    self.navigate_down()
                    event.accept()
                elif key_text in key_map:
                    index = key_map.index(key_text)
                    if 0 <= index < len(self.buttons):
                        self.buttons[index].click()
                    event.accept()
                elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    current_focus = self.focusWidget()
                    if current_focus in self.buttons:
                        current_focus.click()
                    event.accept()
                elif key == Qt.Key.Key_Escape:
                    self.hide()
                    event.accept()
            else:
                event.ignore()
        except Exception as e:
            print(f"Error in keyPressEvent: {traceback.format_exc()}")
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            event.accept()

    def simulate_click(self):
        hwnd = int(self.winId())
        self.bring_to_front(hwnd)

    def bring_to_front(self, hwnd):
        try:
            fgwin = win32gui.GetForegroundWindow()
            if fgwin == hwnd:
                return

            current_thread_id = win32api.GetCurrentThreadId()
            fgwin_thread_id = win32process.GetWindowThreadProcessId(fgwin)[0]

            win32process.AttachThreadInput(current_thread_id, fgwin_thread_id, True)

            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except pywintypes.error as e:
                print(f'SetForegroundWindow failed: {traceback.format_exc()}')

            win32process.AttachThreadInput(current_thread_id, fgwin_thread_id, False)
        except Exception as e:
            print(f"Error in bring_to_front: {traceback.format_exc()}")

###############################
# Main Thread
###############################

def exit_app():
    global exiting
    if not exiting:
        exiting = True
        print("Exiting application")
        controller.hide_window()
        controller.close_window()
        QApplication.quit()

if __name__ == '__main__':
    print("Starting application")

    load_config(menu_path)

    register_hotkey()

    app = QApplication(sys.argv)
    controller = WindowController()

    shared_memory = QSharedMemory('uuid:f7e9a12d-3b4c-4e5f-9a8b-1c2d3e4f5g6h')
    if not shared_memory.create(1):
        print("Another instance is already running.")
        sys.exit(0)

    tray_icon = QSystemTrayIcon(QIcon("icon.png"), parent=app)
    tray_icon.setToolTip('Launcher')

    tray_menu = QMenu()
    show_action = QAction('Disp')
    show_action.triggered.connect(controller.show_window)
    hide_action = QAction('Hide')
    hide_action.triggered.connect(controller.hide_window)
    exit_action = QAction('Exit')
    exit_action.triggered.connect(exit_app)

    tray_menu.addAction(show_action)
    tray_menu.addAction(hide_action)
    tray_menu.addSeparator()
    tray_menu.addAction(exit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    hotkey_filter = HotkeyEventFilter()
    app.installNativeEventFilter(hotkey_filter)

    app.aboutToQuit.connect(unregister_hotkey)

    try:
        sys.exit(app.exec())
    except Exception as e:
        print(f"Application exited with error: {traceback.format_exc()}")
    finally:
        unregister_hotkey()
