from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QSizePolicy
import sys
import subprocess
from blockchain import check_integrity

# Создаем класс ScriptRunner, который наследует QThread и будет запускать скрипт main_video.py в отдельном потоке
class ScriptRunner(QThread):
    log_signal = pyqtSignal(str)

    def run(self):
        try:
            # Запускаем скрипт main_video.py с помощью subprocess.Popen
            with subprocess.Popen([sys.executable, '-Xfrozen_modules=off', 'main_video.py'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True) as process:
                while True:
                    if process.poll() is not None:
                        break
                    
                    output = process.stdout.readline()
                    error = process.stderr.readline()
                    # Отправляем вывод из stdout и stderr в виджет textEdit через сигнал log_signal
                    if output:
                        self.log_signal.emit(f"{output.strip()}\n")
                    if error:
                        self.log_signal.emit(f"{error.strip()}\n")

                    # Завершаем цикл, если нет вывода из stdout и stderr
                    if not output and not error:
                        break
        except Exception as e:
            # Если возникает ошибка, отправляем сообщение об ошибке в виджет textEdit
            self.log_signal.emit(f"Произошла ошибка: {str(e)}\n")

    def stop(self):
        # Останавливаем и завершаем поток, если он все еще работает
        if self.isRunning():
            self.terminate()
            self.wait()
            self.log_signal.emit("Процесс остановлен\n")

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def closeEvent(self, event):
        # Обрабатываем событие закрытия окна и останавливаем поток script_runner
        if hasattr(self, 'script_runner'):
            self.script_runner.stop()
        event.accept()

    def initUI(self):
        # Создаем и настраиваем интерфейс приложения
        self.button = QPushButton("Запустить main_video.py", self)
        self.button.setGeometry(10, 10, 200, 50)
        self.button.clicked.connect(self.run_main)

        self.button_integrity = QPushButton("Проверить целостность", self)
        self.button_integrity.setGeometry(10, 70, 200, 50)
        self.button_integrity.clicked.connect(self.check_integrity) 

        self.textEdit = QTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setGeometry(220, 10, 600, 450)
        self.textEdit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        sys.stdout = self

        self.setGeometry(100, 100, 850, 470)
        self.setWindowTitle('Запуск main_video.py')

    def run_main(self):
        # Запускаем поток script_runner и отключаем кнопки во время выполнения
        self.button.setEnabled(False)
        self.button_integrity.setEnabled(False)
        self.textEdit.clear()
        self.script_runner = ScriptRunner()
        self.script_runner.log_signal.connect(self.write)
        self.script_runner.finished.connect(lambda: self.button.setEnabled(True))
        self.script_runner.finished.connect(lambda: self.button_integrity.setEnabled(True))
        self.script_runner.start()

    def check_integrity(self):
        # Выполняем проверку целостности с помощью функции check_integrity из модуля blockchain
        self.textEdit.clear()
        result = check_integrity()

    def write(self, message):
        # Вставляем полученное сообщение в виджет textEdit
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
