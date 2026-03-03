#src/homography
import cv2
import numpy as np

class Homography:
    def __init__(self, src_points, dst_points):
        self.matrix, _ = cv2.findHomography(
            np.array(src_points),
            np.array(dst_points)
        )

    def transform_point(self, point):
        point = np.array([[point]], dtype="float32")
        transformed = cv2.perspectiveTransform(point, self.matrix)
        return transformed[0][0]