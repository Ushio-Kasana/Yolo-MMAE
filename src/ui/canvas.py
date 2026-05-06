# YOLO-MMAE - Video Annotator & Auto-Tracker
# Copyright (C) 2026  Ushio-Kasana
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                             QGraphicsPixmapItem, QGraphicsTextItem, QGraphicsPolygonItem)
from PyQt6.QtGui import QPixmap, QImage, QPen, QColor, QFont, QPolygonF
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
import cv2
import numpy as np

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

        self.cv_img = None

        # Drawing state
        self.drawing_mode = "rectangle" # "rectangle", "polygon", "autoscale"
        self.is_drawing = False
        self.is_resizing = False
        self.resize_edge = None
        self.start_point = None
        self.current_rect_item = None

        # Polygon drawing state
        self.polygon_points = []
        self.current_polygon_item = None

        # Bounding box management
        self.boxes = [] # List of tuples (x, y, w, h)
        self.rect_items = [] # List of QGraphicsRectItem
        self.text_items = [] # List of QGraphicsTextItem
        self.selected_index = None

        # Suggestions state
        self.suggestion_items = []

        self.setMouseTracking(True)

    def set_mode(self, mode):
        self.drawing_mode = mode
        self.is_drawing = False
        self.polygon_points.clear()
        if self.current_polygon_item:
            self.scene.removeItem(self.current_polygon_item)
            self.current_polygon_item = None

    def set_image(self, cv_img):
        """Displays OpenCV image."""
        if cv_img is None:
            return

        self.cv_img = cv_img
        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width

        # Convert BGR to RGB
        q_img = QImage(cv_img.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)

        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(0, 0, width, height)
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scene.sceneRect().isValid():
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def clear_boxes(self):
        for item in self.rect_items:
            self.scene.removeItem(item)
        for item in self.text_items:
            self.scene.removeItem(item)
        for item in self.suggestion_items:
            self.scene.removeItem(item)
        self.rect_items.clear()
        self.text_items.clear()
        self.suggestion_items.clear()
        self.boxes.clear()
        self.selected_index = None

    def draw_suggestions(self, suggestions, categories_map=None):
        """Draws suggested tracking boxes (cyan, dashed border)."""
        for s in suggestions:
            if s and s.get('box'):
                x, y, w, h = s['box']
                rect = QGraphicsRectItem(QRectF(x, y, w, h))
                pen = QPen(QColor("cyan"), 2, Qt.PenStyle.DashLine)
                rect.setPen(pen)
                self.scene.addItem(rect)
                self.suggestion_items.append(rect)

                # Draw text label if provided
                if categories_map is not None:
                    class_name = categories_map.get(s.get('class_id', 0), "Unknown")
                    text = QGraphicsTextItem(class_name)
                    text.setDefaultTextColor(QColor("cyan"))
                    text.setFont(QFont("Arial", 10, QFont.Weight.Bold))

                    text_bg = QGraphicsRectItem()
                    text_bg.setBrush(QColor(0, 0, 0, 150))
                    text_bg.setPen(QPen(Qt.PenStyle.NoPen))

                    text.setPos(x, y - 20 if y >= 20 else 0)
                    text_rect = text.boundingRect()
                    text_bg.setRect(text.x(), text.y(), text_rect.width(), text_rect.height())

                    text_bg.setZValue(1)
                    text.setZValue(2)

                    self.scene.addItem(text_bg)
                    self.scene.addItem(text)
                    self.suggestion_items.append(text_bg)
                    self.suggestion_items.append(text)

    def get_selected_box_index(self):
        return self.selected_index

    def clear_selection(self):
        if self.selected_index is not None and self.selected_index < len(self.rect_items):
            self.rect_items[self.selected_index].setPen(QPen(QColor("red"), 2))
        self.selected_index = None

    def draw_boxes(self, annotations, categories_map):
        """Draws a list of annotations (dicts with 'box' and 'class_id')"""
        self.clear_boxes()
        for ann in annotations:
            if ann and ann.get('box'):
                x, y, w, h = ann['box']
                rect = QGraphicsRectItem(QRectF(x, y, w, h))
                rect.setPen(QPen(QColor("red"), 2))
                self.scene.addItem(rect)
                self.rect_items.append(rect)
                self.boxes.append((x, y, w, h))

                # Draw text label above box
                class_name = categories_map.get(ann.get('class_id', 0), "Unknown")
                text = QGraphicsTextItem(class_name)
                text.setDefaultTextColor(QColor("white"))
                text.setFont(QFont("Arial", 10, QFont.Weight.Bold))

                # Create a semi-transparent black background for the text
                text_bg = QGraphicsRectItem()
                text_bg.setBrush(QColor(0, 0, 0, 150))
                text_bg.setPen(QPen(Qt.PenStyle.NoPen))

                # Position text just above the box
                text.setPos(x, y - 20 if y >= 20 else 0)

                # Size the background to the text
                text_rect = text.boundingRect()
                text_bg.setRect(text.x(), text.y(), text_rect.width(), text_rect.height())

                # Ensure the background is behind the text but above the image
                text_bg.setZValue(1)
                text.setZValue(2)

                # Group text items logically with rect by just adding them
                self.scene.addItem(text_bg)
                self.scene.addItem(text)

                # Store them together so they can be cleared
                self.text_items.append(text_bg)
                self.text_items.append(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())

            # Handle resizing if a box is currently selected
            if self.selected_index is not None and self.selected_index < len(self.rect_items):
                rect_item = self.rect_items[self.selected_index]
                rect = rect_item.rect()

                # Check distance to edges (tolerance of 10 pixels)
                t = 10
                is_left = abs(pos.x() - rect.left()) < t
                is_right = abs(pos.x() - rect.right()) < t
                is_top = abs(pos.y() - rect.top()) < t
                is_bottom = abs(pos.y() - rect.bottom()) < t

                if is_left or is_right or is_top or is_bottom:
                    self.is_resizing = True
                    self.resize_edge = (is_left, is_right, is_top, is_bottom)
                    return

            # Check if we clicked on an existing box to select it
            item = self.scene.itemAt(pos, self.transform())

            if isinstance(item, QGraphicsRectItem) and item in self.rect_items:
                self.clear_selection()
                index = self.rect_items.index(item)
                self.selected_index = index
                item.setPen(QPen(QColor("yellow"), 3)) # Highlight selected box
                self.box_selected.emit(index)
                return

            # If we clicked elsewhere, clear selection and start drawing
            self.clear_selection()

            if self.drawing_mode == "rectangle":
                self.is_drawing = True
                self.start_point = pos

                self.current_rect_item = QGraphicsRectItem()
                self.current_rect_item.setPen(QPen(QColor("green"), 2))
                self.scene.addItem(self.current_rect_item)

            elif self.drawing_mode == "polygon":
                self.polygon_points.append(pos)
                if not self.current_polygon_item:
                    self.current_polygon_item = QGraphicsPolygonItem()
                    self.current_polygon_item.setPen(QPen(QColor("green"), 2))
                    self.scene.addItem(self.current_polygon_item)

                poly = QPolygonF(self.polygon_points)
                self.current_polygon_item.setPolygon(poly)

            elif self.drawing_mode == "autoscale" and self.cv_img is not None:
                x, y = int(pos.x()), int(pos.y())
                if 0 <= x < self.cv_img.shape[1] and 0 <= y < self.cv_img.shape[0]:
                    # Use a combination of blur, Canny edge detection, and floodfill for better auto-scaling
                    blurred = cv2.bilateralFilter(self.cv_img, 9, 75, 75) # Preserve edges better than Gaussian

                    # Create an edge mask
                    edges = cv2.Canny(blurred, 50, 150)
                    edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)

                    mask = np.zeros((self.cv_img.shape[0] + 2, self.cv_img.shape[1] + 2), np.uint8)

                    # Apply edges to mask to stop floodfill at boundaries
                    mask[1:-1, 1:-1] = edges

                    # Tolerances
                    lo_diff, up_diff = (20, 20, 20), (20, 20, 20)

                    # Perform floodfill
                    cv2.floodFill(blurred, mask, (x, y), (255, 255, 255), lo_diff, up_diff, flags=cv2.FLOODFILL_MASK_ONLY | (255 << 8))

                    # Clean up the mask
                    filled_mask = mask[1:-1, 1:-1]
                    # We only care about the region we actually filled, not the edge boundaries we seeded it with
                    filled_mask = cv2.bitwise_and(filled_mask, cv2.bitwise_not(edges))

                    kernel = np.ones((5,5), np.uint8)
                    filled_mask = cv2.morphologyEx(filled_mask, cv2.MORPH_CLOSE, kernel)
                    filled_mask = cv2.morphologyEx(filled_mask, cv2.MORPH_OPEN, kernel)

                    coords = cv2.findNonZero(filled_mask)
                    if coords is not None:
                        bx, by, bw, bh = cv2.boundingRect(coords)
                        img_area = self.cv_img.shape[0] * self.cv_img.shape[1]
                        box_area = bw * bh
                        if bw > 10 and bh > 10 and box_area < (img_area * 0.95):
                            self.box_drawn.emit((bx, by, bw, bh))

        elif event.button() == Qt.MouseButton.RightButton and self.drawing_mode == "polygon":
            # Finish polygon
            if len(self.polygon_points) >= 3:
                poly = QPolygonF(self.polygon_points)
                rect = poly.boundingRect()
                x, y, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())

                if w > 10 and h > 10:
                    self.box_drawn.emit((x, y, w, h))

            # Clean up temporary polygon drawing
            if self.current_polygon_item:
                self.scene.removeItem(self.current_polygon_item)
                self.current_polygon_item = None
            self.polygon_points.clear()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing and self.selected_index is not None:
            current_point = self.mapToScene(event.pos())
            rect_item = self.rect_items[self.selected_index]
            rect = rect_item.rect()

            is_left, is_right, is_top, is_bottom = self.resize_edge

            new_left = current_point.x() if is_left else rect.left()
            new_right = current_point.x() if is_right else rect.right()
            new_top = current_point.y() if is_top else rect.top()
            new_bottom = current_point.y() if is_bottom else rect.bottom()

            # Ensure boundaries don't cross
            if new_left > new_right: new_left, new_right = new_right, new_left
            if new_top > new_bottom: new_top, new_bottom = new_bottom, new_top

            new_rect = QRectF(QPointF(new_left, new_top), QPointF(new_right, new_bottom))
            rect_item.setRect(new_rect)

        elif self.is_drawing and self.current_rect_item and self.drawing_mode == "rectangle":
            current_point = self.mapToScene(event.pos())
            rect = QRectF(self.start_point, current_point).normalized()
            self.current_rect_item.setRect(rect)

        elif self.drawing_mode == "polygon" and self.polygon_points and self.current_polygon_item:
            # Show live preview of next polygon edge
            current_point = self.mapToScene(event.pos())
            temp_points = self.polygon_points + [current_point]
            poly = QPolygonF(temp_points)
            self.current_polygon_item.setPolygon(poly)

        super().mouseMoveEvent(event)

    # Signal for when a box has finished resizing
    box_resized = pyqtSignal(int, tuple) # Emits (index, (x, y, w, h))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_resizing:
            self.is_resizing = False
            if self.selected_index is not None and self.selected_index < len(self.rect_items):
                rect = self.rect_items[self.selected_index].rect()
                x, y, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
                self.boxes[self.selected_index] = (x, y, w, h)
                self.box_resized.emit(self.selected_index, (x, y, w, h))

        elif event.button() == Qt.MouseButton.LeftButton and self.is_drawing and self.drawing_mode == "rectangle":
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
