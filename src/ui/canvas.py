from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                             QGraphicsPixmapItem)
from PyQt6.QtGui import QPixmap, QImage, QPen, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QRectF

class VideoCanvas(QGraphicsView):
    # Signals for drawing
    box_drawn = pyqtSignal(tuple) # Emits (x, y, w, h)
    box_selected = pyqtSignal(int) # Emits index of selected box

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        # Drawing state
        self.is_drawing = False
        self.start_point = None
        self.current_rect_item = None

        # Bounding box management
        self.boxes = [] # List of tuples (x, y, w, h)
        self.rect_items = [] # List of QGraphicsRectItem

        self.setMouseTracking(True)

    def set_image(self, cv_img):
        """Displays OpenCV image."""
        if cv_img is None:
            return

        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width

        # Convert BGR to RGB
        q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)

        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(0, 0, width, height)

    def clear_boxes(self):
        for item in self.rect_items:
            self.scene.removeItem(item)
        self.rect_items.clear()
        self.boxes.clear()

    def draw_boxes(self, boxes):
        """Draws a list of boxes (x, y, w, h)"""
        self.clear_boxes()
        for box in boxes:
            if box is not None:
                x, y, w, h = box
                rect = QGraphicsRectItem(QRectF(x, y, w, h))
                rect.setPen(QPen(QColor("red"), 2))
                self.scene.addItem(rect)
                self.rect_items.append(rect)
                self.boxes.append(box)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we clicked on an existing box to select it
            pos = self.mapToScene(event.pos())
            item = self.scene.itemAt(pos, self.transform())

            if isinstance(item, QGraphicsRectItem):
                index = self.rect_items.index(item)
                self.box_selected.emit(index)
                return

            # Start drawing
            self.is_drawing = True
            self.start_point = pos

            self.current_rect_item = QGraphicsRectItem()
            self.current_rect_item.setPen(QPen(QColor("green"), 2))
            self.scene.addItem(self.current_rect_item)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing and self.current_rect_item:
            current_point = self.mapToScene(event.pos())
            rect = QRectF(self.start_point, current_point).normalized()
            self.current_rect_item.setRect(rect)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False

            if self.current_rect_item:
                rect = self.current_rect_item.rect()
                x, y, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())

                # Minimum size check
                if w > 10 and h > 10:
                    self.current_rect_item.setPen(QPen(QColor("red"), 2))
                    self.rect_items.append(self.current_rect_item)
                    self.boxes.append((x, y, w, h))
                    self.box_drawn.emit((x, y, w, h))
                else:
                    self.scene.removeItem(self.current_rect_item)

                self.current_rect_item = None

        super().mouseReleaseEvent(event)
