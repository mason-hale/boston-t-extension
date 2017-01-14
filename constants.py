MBTA_YAML_PATH = 'data/mbta.yaml'
DEBUG_GRAPH_PATH = 'tmp/mbta_graph.svg'

TAXI_PICKUP_PATH = 'data/taxi/pickup6.csv'
TAXI_DROPOFF_PATH = 'data/taxi/dropoff6.csv'

TAXI_PICKUP_PATHS = [
    'data/taxi/pickup6.csv',
    'data/taxi/pickup7.csv',
    'data/taxi/pickup8.csv',
    'data/taxi/filtered_pickups_9_12.csv',
    'data/taxi/filtered_pickups_10_12.csv',
    'data/taxi/filtered_pickups_11_12.csv',
]

TAXI_DROPOFF_PATHS = [
    'data/taxi/dropoff6.csv',
    'data/taxi/dropoff7.csv',
    'data/taxi/dropoff8.csv',
    'data/taxi/filtered_dropoffs_9_12.csv',
    'data/taxi/filtered_dropoffs_10_12.csv',
    'data/taxi/filtered_dropoffs_11_12.csv',
]

PREPROCESSED_PATH = 'tmp/trips.csv'
PREPROCESSED_12HR_DATE_FORMAT = "%m/%d/%y %I:%M %p"
PREPROCESSED_24HR_DATE_FORMAT = "%m/%d/%Y %H:%M"
PREPROCESSED_KEYS = {
    'DROPOFF_LAT': 'DROPOFF_LAT',
    'DROPOFF_LONG': 'DROPOFF_LONG',
    'DROPOFF_TIME': 'DROPOFF_TIME',
    'ID': 'ID',
    'PICKUP_LAT': 'PICKUP_LAT',
    'PICKUP_LONG': 'PICKUP_LONG',
    'PICKUP_TIME': 'PICKUP_TIME',

    'DROPLAT': 'DROPOFF_LAT',
    'DROPLONG': 'DROPOFF_LONG',
    'DROPTIME': 'DROPOFF_TIME',
    'PICKUPLAT': 'PICKUP_LAT',
    'PICKUPLONG': 'PICKUP_LONG',
    'PICKUPTIME': 'PICKUP_TIME',
    'TRIP_ID': 'ID',
}
WALKING_SPEED = .083333333  # km/min
T_WAIT_TIME = 5  # min, can be modified but doesn't change the central judgment, T_difs
WALKING_LIMIT = 0.5  # km
MAX_STATIONS_TO_CHECK = 3
INVALID_TRIP = -2  # signifier to not count this trip!
STOP_NO_IMPROVEMENT = (0.0, 0.0, 0.0)
NOT_SEEN = -1  # makes sure we don't recalculate stops already in frontier
MAX_BEAM_SEARCH_ITERATIONS = 15
FRONTIER_SIZE = 10
BRANCH_FACTOR = 6
NEW_GAP = 1.5
SAMPLE_NUM = 10000
