from PySide6.QtWidgets import QApplication

from core.app import NEXISApplication


def main():
    app = QApplication([])
    app.setApplicationName("NEXIS")
    engine = NEXISApplication()
    engine.run()
    app.exec()


if __name__ == "__main__":
    main()
