import os
import subprocess
import sys
import threading
from enum import Enum

from PyQt5.QtCore import pyqtSlot, Qt, QEvent, QSize
from PyQt5 import QtWidgets
from PyQt5.QtGui import QImage, QPixmap, QTransform, QIcon
from PyQt5.QtWidgets import QTreeWidgetItem, QMenu, QListWidgetItem, QMessageBox
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import sessionmaker

from PyUI.ViewerGUI import Ui_MainWindow
from models import engine, collection, Path, UploadedFile
from log_config import setup_logger

logger = setup_logger(__name__, "./logs/main.log")


class Mode(Enum):
    FILE_BROWSER = 1
    QUERY_BROWSER = 2


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.folder_paths = []
        self.queried_images = []
        self.selected_image: QTreeWidgetItem | QListWidgetItem | None = None
        self.selected_image_metadata = {
            "current_image_pixmap": QPixmap(),
            "current_image_path": "",
            "col": -1
        }
        self.rotate_times = 0
        self.mode = Mode.FILE_BROWSER
        self.uploadFolder.clicked.connect(self.get_folder)
        self.thumbnailView.itemClicked.connect(self.get_image_thumbnail)
        self.rotateButton.clicked.connect(self.rotate_image)
        self.previousButton.setShortcut(Qt.Key_Left)
        self.previousButton.clicked.connect(self.left_nav)
        self.nextButton.setShortcut(Qt.Key_Right)
        self.nextButton.clicked.connect(self.right_nav)
        self.sendMessage.clicked.connect(self.text_prompt)
        self.imageUpload.clicked.connect(self.image_prompt)

        self.context_menu = QMenu(self)
        self.context_menu.addAction("Open Current Image",
                                    lambda: self.os_opener(self.selected_image_metadata["current_image_path"]))
        self.context_menu.addAction("Open Current Image Folder",
                                    lambda: self.os_opener(
                                        os.path.dirname(self.selected_image_metadata["current_image_path"])))
        self.data_init()

    def data_init(self):
        result = session.query(Path).all()
        for path in result:
            self.load_images(path.path)

    @staticmethod
    def os_opener(path):
        if sys.platform == "win32":
            os.startfile(path)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, path])

    @pyqtSlot(QTreeWidgetItem, int)
    def get_image_file(self, it: QTreeWidgetItem, col: int):
        if it.parent() is None:
            return
        self.mode = Mode.FILE_BROWSER
        filename = os.path.join(it.parent().text(col), it.text(col))
        image = QImage(filename)
        self.selected_image = it
        self.selected_image_metadata["col"] = col
        self.selected_image_metadata["current_image_pixmap"] = QPixmap.fromImage(image)
        self.selected_image_metadata["current_image_path"] = filename
        self.viewImage.setPixmap(self.selected_image_metadata["current_image_pixmap"].scaled(
            self.viewImage.width(), self.viewImage.height(),
            Qt.KeepAspectRatio))
        self.rotate_times = 0
        self.viewImage.installEventFilter(self)

    @pyqtSlot(QListWidgetItem)
    def get_image_thumbnail(self, it: QListWidgetItem):
        if not self.queried_images:
            return
        self.mode = Mode.QUERY_BROWSER
        filename = self.queried_images[self.thumbnailView.indexFromItem(it).row()]
        image = QImage(filename)
        self.selected_image = it
        self.selected_image_metadata["current_image_pixmap"] = QPixmap.fromImage(image)
        self.selected_image_metadata["current_image_path"] = filename
        self.viewImage.setPixmap(self.selected_image_metadata["current_image_pixmap"].scaled(
            self.viewImage.width(), self.viewImage.height(),
            Qt.KeepAspectRatio))
        self.rotate_times = 0
        self.viewImage.installEventFilter(self)

    def get_folder(self):
        file = str(QtWidgets.QFileDialog.getExistingDirectory(None, "Select Folder"))
        if file != "":
            try:
                uploaded_path = Path(path=file)
                session.add(uploaded_path)
                session.commit()
            except IntegrityError:
                session.rollback()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Path already exists")
                msg.setWindowTitle("Path Exists")
                msg.exec_()
                return
            threading.Thread(target=self.embed_images, args=(file,)).start()
            self.load_images(file)

    @staticmethod
    def embed_images(folder_path):
        logger.info("Embedding images in the folder...")
        file_ids = []
        uris = []
        metadata = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.normpath(os.path.join(root, file))
                uploaded_path = UploadedFile(filename=file, dirpath=file_path)
                session.add(uploaded_path)
                session.commit()
                if file.lower().endswith((".jpg", ".jpeg", ".png")):
                    file_ids.append(str(uploaded_path.id))
                    uris.append(file_path)
                    metadata.append({'path': file_path})
        collection.add(
            ids=file_ids,
            uris=uris,
            metadatas=metadata
        )
        logger.info("Successfully embedded images")

    def load_images(self, folder_path):
        self.folder_paths.append(folder_path)
        folder_item = QTreeWidgetItem([folder_path])
        self.file_tree_constructor(folder_path, folder_item)
        self.folderView.addTopLevelItem(folder_item)
        self.folderView.itemClicked.connect(self.get_image_file)

    def file_tree_constructor(self, folder_path, parent: QTreeWidgetItem):
        try:
            items = os.listdir(folder_path)
        except OSError as e:
            logger.error(f"Error accessing {folder_path}: {e}")
            return
        dirs = [d for d in items if os.path.isdir(os.path.join(folder_path, d))]
        files = [f for f in items if os.path.isfile(os.path.join(folder_path, f))]
        for directory in dirs:
            folder_item = QTreeWidgetItem([os.path.join(folder_path, directory)])
            parent.addChild(folder_item)
            self.file_tree_constructor(os.path.join(folder_path, directory), folder_item)
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                parent.addChild(QTreeWidgetItem([file]))

    def rotate_image(self):
        rotated_image = self.viewImage.pixmap().transformed(QTransform().rotate(90), Qt.SmoothTransformation)
        if self.rotate_times == 3:
            self.rotate_times = 0
        else:
            self.rotate_times += 1
        self.viewImage.setPixmap(rotated_image)

    def left_nav(self):
        if self.selected_image is None:
            return
        if self.mode == Mode.FILE_BROWSER:
            parent = self.selected_image.parent()
            next_index = parent.child(parent.indexOfChild(self.selected_image) - 1)
            if next_index is not None:
                self.selected_image.setSelected(False)
                next_index.setSelected(True)
                self.folderView.itemClicked.emit(next_index, self.selected_image_metadata["col"])
        elif self.mode == Mode.QUERY_BROWSER:
            current_image = self.thumbnailView.indexFromItem(self.selected_image).row()
            next_image = self.thumbnailView.item(current_image - 1)
            if next_image is not None:
                self.selected_image.setSelected(False)
                next_image.setSelected(True)
                self.thumbnailView.itemClicked.emit(next_image)

    def right_nav(self):
        if self.selected_image is None:
            return
        if self.mode == Mode.FILE_BROWSER:
            parent = self.selected_image.parent()
            next_index = parent.child(parent.indexOfChild(self.selected_image) + 1)
            if next_index is not None:
                self.selected_image.setSelected(False)
                next_index.setSelected(True)
                self.folderView.itemClicked.emit(next_index, self.selected_image_metadata["col"])
        elif self.mode == Mode.QUERY_BROWSER:
            current_image = self.thumbnailView.indexFromItem(self.selected_image).row()
            next_image = self.thumbnailView.item(current_image + 1)
            if next_image is not None:
                self.selected_image.setSelected(False)
                next_image.setSelected(True)
                self.thumbnailView.itemClicked.emit(next_image)

    def text_prompt(self):
        prompt_text = self.promptText.toPlainText()
        result = collection.query(
            query_texts=prompt_text
        )
        self.queried_images = []
        for metadata in result['metadatas'][0]:
            self.queried_images.append(os.path.normpath(metadata['path']))
        self.thumbnail_constructor()
        self.promptText.clear()

    def image_prompt(self):
        file = QtWidgets.QFileDialog.getOpenFileName(None, "Select Image", filter="Images (*.jpg *.jpeg *.png)")
        if file[0] != "":
            result = collection.query(
                query_uris=[os.path.normpath(file[0])]
            )
            self.queried_images = []
            for metadata in result['metadatas'][0]:
                self.queried_images.append(os.path.normpath(metadata['path']))
            self.thumbnail_constructor()

    def thumbnail_constructor(self):
        self.thumbnailView.clear()
        self.mode = Mode.QUERY_BROWSER
        for path in self.queried_images:
            image = QIcon(path)
            item = QListWidgetItem(image, None)
            self.thumbnailView.addItem(item)

    def eventFilter(self, widget, event):
        if event.type() == QEvent.Resize and widget is self.viewImage:
            self.viewImage.setPixmap(self.selected_image_metadata["current_image_pixmap"].scaled(
                self.viewImage.width(), self.viewImage.height(),
                Qt.KeepAspectRatio).transformed(QTransform().rotate(90 * self.rotate_times), Qt.SmoothTransformation))
            return True
        return super(MainWindow, self).eventFilter(widget, event)

    def contextMenuEvent(self, event):
        if self.selected_image_metadata["current_image_path"] == "":
            return
        self.context_menu.exec(event.globalPos())


if __name__ == "__main__":
    Session = sessionmaker(bind=engine)
    session = Session()
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
