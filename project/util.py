# Helper functions
# All methods here should have tests

import numpy as np
from numpy import sin, cos, radians, arctan2, sqrt  # import from numpy

from constants import WALKING_LIMIT, INVALID_TRIP

# TODO cos_factor check
cos_factor = abs(cos(radians(42.3601)))
R = 6371.  # Earth's radius in kilometers


def make_latlng(lat, lng):
    """ Used to standardize the representation of latitude, longitude coordinates """
    return np.array([lat, lng], dtype=np.float64)


def latlng_dist(loc1, loc2):
    """
        Returns the distacne between two coordinates in kilometers. Takes into account the curvature of the earth.
        Haversine formula - give coordinates as a 2D numpy array of
        (lat_decimal,lon_decimal) pairs
        Taken from https://sites.google.com/site/dlampetest/python/numpy-array-math
    """
    # "unpack" our numpy array, this extracts column wise arrays
    lat1 = loc1[0]
    lon1 = loc1[1]
    lat2 = loc2[0]
    lon2 = loc2[1]
    #
    # convert to radians ##### Completely identical
    lon1 = radians(lon1)
    lat1 = radians(lat1)
    lon2 = radians(lon2)
    lat2 = radians(lat2)
    #
    # haversine formula #### Same, but atan2 named arctan2 in numpy
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (sin(dlat / 2)) ** 2 + cos(lat1) * cos(lat2) * (sin(dlon / 2.0)) ** 2
    c = 2.0 * arctan2(sqrt(a), sqrt(1.0 - a))
    km = R * c
    return km


def closest_stations(stations, station_tree, (lat, lng), max_distance=float('inf'), limit=3):
    """
    Returns closest station according to given parameters
    :type stations: list[station] - mapping index -> station name
    :type station_tree: cKDTree - scipy cKDTree mapping stations to points
    :type (lat, lng): tuple[float64, float64]
    :type max_distance: float - returns stations within this bound
    :type limit: int - max number of stations to return,
     if less than the limit stations are found, retunr that number of stations
    :return iter[tuple[float, station]] - (distance, station name) tuples
    """
    distances, indices = station_tree.query((lat * cos_factor, lng), distance_upper_bound=max_distance, k=limit)
    closest_stations = map(lambda i: stations[i] if i < len(stations) else None, indices)
    return zip(filter(lambda d: d != float('inf'), distances), filter(lambda s: s is not None, closest_stations))


def is_trip_relevant(trip, new_node, t_old, walking_limit=WALKING_LIMIT):
    """ determines whether trip could be impacted by this new stop """
    if t_old[0] == INVALID_TRIP:
        return False

    from_coord, to_coord, t_start, t_stop = trip
    terminal, coord, _, _, _ = new_node

    return latlng_dist(from_coord, coord) <= walking_limit or latlng_dist(to_coord, coord) <= walking_limit
