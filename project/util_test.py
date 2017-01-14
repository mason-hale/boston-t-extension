# Unit tests for util methods

from nose.tools import *
from numpy import float64
from scipy.spatial.ckdtree import cKDTree

from util import *


def test_make_latlng():
    result = make_latlng(0, 1)
    assert type(result[0]) == float64
    assert type(result[1]) == float64
    assert result[0] == 0.
    assert result[1] == 1.


def test_latlng_dist():
    assert type(latlng_dist([42.43156, -71.11124], [42.43156, -71.11124])) == float64
    assert_almost_equal(
        latlng_dist([42.43156, -71.11124], [42.43156, -71.11124]),
        0, places=5,
    )
    assert_almost_equal(
        latlng_dist([42.43156, -71.11124], [42.429276, -71.189149]),
        6.401, places=2,
    )
    assert_almost_equal(
        latlng_dist([42.285924, -71.064219], [42.29279438, -71.06578231]),
        .775, places=3,
    )
    assert_almost_equal(
        latlng_dist([38.898556, -77.037852], [38.897147, -77.043934]),
        0.549, places=3,
    )
    assert_almost_equal(
        latlng_dist([42.43156, -71.11124], [43.43156, -71.11124]),
        111.2, places=1,
    )


def test_closest_stations():
    stations = range(4)
    station_tree = cKDTree(
        np.array([
            [0, 0],
            [0, 1],
            [0, 2],
            [0, 3],
        ])
    )
    station_tree_t = cKDTree(
        np.array([
            [0. * cos_factor, 0],
            [1. * cos_factor, 0],
            [2. * cos_factor, 0],
            [3. * cos_factor, 0],
        ])
    )

    result = closest_stations(stations, station_tree, [0, 3], limit=5)
    assert len(result) == 4
    assert result[0] == (0, 3)
    assert result[1] == (1., 2)
    assert result[2] == (2., 1)
    assert result[3] == (3., 0)

    result = closest_stations(stations, station_tree_t, [3, 0], limit=5)
    assert len(result) == 4
    assert_almost_equal(result[0][0], 0)
    assert_almost_equal(result[1][0], cos_factor)
    assert_almost_equal(result[2][0], 2. * cos_factor)
    assert_almost_equal(result[3][0], 3. * cos_factor)

    result = closest_stations(stations, station_tree, [0, 3], limit=3, max_distance=1.5)
    assert len(result) == 2

    result = closest_stations(stations, station_tree, [4, 3], limit=5)
    assert len(result) == 4
    assert result[0][1] == 3
    assert result[1][1] == 2
    assert result[2][1] == 1
    assert result[3][1] == 0

    result = closest_stations(stations, station_tree, [4, 3], limit=2)
    assert len(result) == 2

    result = closest_stations(stations, station_tree, [4, 3], max_distance=0.1)
    assert len(result) == 0


test_trip = (make_latlng(42.35064, -71.074488), make_latlng(42.35468, -71.059043), '1340113620', '1340114040')
test_trip2 = (make_latlng(42.361785, -71.070493), make_latlng(42.341617, -71.068933), '1339717860', '1339718340')
test_trip3 = (make_latlng(42.362132, -71.017792), make_latlng(42.347163, -71.079702), '1338739260', '1338740340')

new_station1 = ('Wonderland Station', make_latlng(42.414246, -70.992144), -1, -1, -1)
new_station2 = ('Bowdoin Station', make_latlng(42.361457, -71.062129), -1, -1, -1)

invalid_T_old = (INVALID_TRIP, None, None)
T_olds = [
    (9.023499811512, ('Arlington Station', 0.0003409899177539427),
     ('Downtown Crossing Station', 0.00015026688104975255)),
    (9.9532735194938979, ('Arlington Station', 0.00061065985738176785),
     ('East Berkeley Street Station', 0.00027846932684267488)),
    (19.471031258881446, ('Terminal B Stop 1', 8.2882292135137069e-05), ('Back Bay Station', 0.00030532469916985785)),
]


def test_is_trip_relevant():
    assert not is_trip_relevant(test_trip, new_station1, (INVALID_TRIP, None, None))
    assert not is_trip_relevant(test_trip, new_station2, (INVALID_TRIP, None, None))
    assert is_trip_relevant(test_trip, new_station1, T_olds[0], walking_limit=8.7)
    assert not is_trip_relevant(test_trip, new_station1, T_olds[0], walking_limit=8.6)
    assert is_trip_relevant(test_trip, new_station2, T_olds[1], walking_limit=0.8)
    assert not is_trip_relevant(test_trip, new_station2, T_olds[1], walking_limit=0.7)
