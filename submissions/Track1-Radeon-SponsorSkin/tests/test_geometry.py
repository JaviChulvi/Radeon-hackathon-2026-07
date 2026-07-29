from __future__ import annotations

import numpy as np
import pytest

from sponsorskin.geometry import GeometryError, order_points_clockwise, validate_quadrilateral
from sponsorskin.schemas import Point


def test_points_are_normalized_to_expected_corner_order() -> None:
    points = [
        Point(x=90, y=80),
        Point(x=10, y=10),
        Point(x=10, y=90),
        Point(x=100, y=20),
    ]

    ordered = order_points_clockwise(points)

    np.testing.assert_array_equal(
        ordered,
        np.asarray([[10, 10], [100, 20], [90, 80], [10, 90]], dtype=np.float32),
    )


def test_duplicate_points_are_rejected() -> None:
    duplicate = Point(x=10, y=10)
    with pytest.raises(GeometryError, match="distinct"):
        order_points_clockwise([duplicate, duplicate, Point(x=20, y=20), Point(x=20, y=10)])


def test_out_of_bounds_points_are_rejected() -> None:
    with pytest.raises(GeometryError, match="inside"):
        validate_quadrilateral(
            [
                Point(x=0, y=0),
                Point(x=110, y=0),
                Point(x=90, y=90),
                Point(x=0, y=90),
            ],
            image_size=(100, 100),
        )
