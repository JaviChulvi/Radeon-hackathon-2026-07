"""Quadrilateral validation and perspective-warp geometry."""

from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np

from sponsorskin.schemas import Point


class GeometryError(ValueError):
    """Raised when a placement quadrilateral is not usable."""


def order_points_clockwise(points: Sequence[Point]) -> np.ndarray:
    """Return points in top-left, top-right, bottom-right, bottom-left order."""

    if len(points) != 4:
        raise GeometryError("Exactly four placement points are required")
    coordinates = np.asarray([(point.x, point.y) for point in points], dtype=np.float32)
    if np.unique(coordinates, axis=0).shape[0] != 4:
        raise GeometryError("Placement points must be distinct")

    centroid = coordinates.mean(axis=0)
    angles = np.arctan2(coordinates[:, 1] - centroid[1], coordinates[:, 0] - centroid[0])
    ordered = coordinates[np.argsort(angles)]
    top_left_index = int(np.argmin(ordered.sum(axis=1)))
    return np.roll(ordered, -top_left_index, axis=0)


def validate_quadrilateral(
    points: Sequence[Point],
    *,
    image_size: tuple[int, int],
    minimum_area: float = 64.0,
) -> np.ndarray:
    """Validate bounds, convexity, and usable area for four placement points."""

    width, height = image_size
    ordered = order_points_clockwise(points)
    if np.any(ordered[:, 0] >= width) or np.any(ordered[:, 1] >= height):
        raise GeometryError("Placement points must lie inside the target image")
    contour = ordered.reshape((-1, 1, 2))
    if not cv2.isContourConvex(contour):
        raise GeometryError("Placement quadrilateral must be convex")
    area = float(abs(cv2.contourArea(contour)))
    if area < minimum_area:
        raise GeometryError(f"Placement area must be at least {minimum_area:.0f} pixels")
    return ordered


def perspective_matrix(
    source_size: tuple[int, int],
    destination_points: np.ndarray,
) -> np.ndarray:
    """Compute a perspective transform from a source rectangle to a quadrilateral."""

    width, height = source_size
    source_points = np.asarray(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    return cv2.getPerspectiveTransform(source_points, destination_points.astype(np.float32))
