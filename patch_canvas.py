import re

with open('src/ui/canvas.py', 'r') as f:
    content = f.read()

autoscale_old = """            elif self.drawing_mode == "autoscale" and self.cv_img is not None:
                # Use floodfill to find an object from a clicked point
                x, y = int(pos.x()), int(pos.y())
                if 0 <= x < self.cv_img.shape[1] and 0 <= y < self.cv_img.shape[0]:
                    # Blur slightly to help grouping colors
                    blurred = cv2.GaussianBlur(self.cv_img, (5, 5), 0)
                    mask = np.zeros((blurred.shape[0] + 2, blurred.shape[1] + 2), np.uint8)

                    # Tighten tolerance so it doesn't flood the whole screen
                    lo_diff, up_diff = (5, 5, 5), (5, 5, 5)
                    cv2.floodFill(blurred, mask, (x, y), (255, 255, 255), lo_diff, up_diff, flags=cv2.FLOODFILL_MASK_ONLY | (255 << 8))

                    # Find bounding box of mask
                    coords = cv2.findNonZero(mask[1:-1, 1:-1])
                    if coords is not None:
                        bx, by, bw, bh = cv2.boundingRect(coords)
                        # Reject if it captured almost the entire frame (likely a failed floodfill)
                        img_area = self.cv_img.shape[0] * self.cv_img.shape[1]
                        box_area = bw * bh
                        if bw > 10 and bh > 10 and box_area < (img_area * 0.9):
                            self.box_drawn.emit((bx, by, bw, bh))"""

autoscale_new = """            elif self.drawing_mode == "autoscale" and self.cv_img is not None:
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
                            self.box_drawn.emit((bx, by, bw, bh))"""

content = content.replace(autoscale_old, autoscale_new)

with open('src/ui/canvas.py', 'w') as f:
    f.write(content)
