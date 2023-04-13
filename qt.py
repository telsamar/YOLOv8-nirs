from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QSizePolicy
import sys
import subprocess
from blockchain import check_integrity

class ScriptRunner(QThread):
    log_signal = pyqtSignal(str)

    def run(self):
        with subprocess.Popen(['python', 'main_video.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True) as process:
            while True:
                output = process.stdout.readline()
                error = process.stderr.readline()

                if output:
                    self.log_signal.emit(f"{output.strip()}\n")
                if error:
                    self.log_signal.emit(f"{error.strip()}\n")

                if not output and not error:
                    break

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        button = QPushButton("Запустить main_video.py", self)
        button.setGeometry(10, 10, 200, 50)
        button.clicked.connect(self.run_main)

        button_integrity = QPushButton("Проверить целостность", self)
        button_integrity.setGeometry(10, 70, 200, 50)
        button_integrity.clicked.connect(self.check_integrity) 

        self.textEdit = QTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setGeometry(220, 10, 600, 450)
        self.textEdit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        sys.stdout = self

        self.setGeometry(100, 100, 850, 470)
        self.setWindowTitle('Запуск main_video.py')

    def run_main(self):
        self.textEdit.clear()
        self.script_runner = ScriptRunner()
        self.script_runner.log_signal.connect(self.write)
        self.script_runner.start()

    def check_integrity(self):
        self.textEdit.clear()
        result = check_integrity()

    def write(self, message):
        self.textEdit.insertPlainText(message)

    def flush(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()

    print("Запуск приложения...")
    sys.stdout.flush()

    window.show()
    sys.exit(app.exec())
