import heapq
import itertools
import logging
import random

import networkx as nx
from scipy.spatial import cKDTree
from tqdm import tqdm

import mbta_graph
import read_data
from constants import MBTA_YAML_PATH, PREPROCESSED_PATH
from constants import WALKING_SPEED, T_WAIT_TIME, MAX_STATIONS_TO_CHECK, STOP_NO_IMPROVEMENT, NOT_SEEN, \
    MAX_BEAM_SEARCH_ITERATIONS, FRONTIER_SIZE, BRANCH_FACTOR, NEW_GAP, SAMPLE_NUM
from util import *

logger = logging.getLogger(__name__)


def analyze_trip(t_times, stations, station_tree, trip):
    """ Measure time needed for a taxi trip itinerary on the MBTA """
    global zero_count
    from_coords, to_coords, t_start, t_stop = trip
    taxi_time = (float(t_stop) - float(t_start)) / 60.  # converts seconds to minutes
    none_tup = (None, None)

    if taxi_time == 0:
        zero_count += 1
        return INVALID_TRIP, none_tup, none_tup

    logger.info('Analyzing trip %s of %s min', (from_coords, to_coords), taxi_time)
    from_stations = closest_stations(
        stations, station_tree, from_coords,
        max_distance=WALKING_LIMIT, limit=MAX_STATIONS_TO_CHECK)
    to_stations = closest_stations(
        stations, station_tree, to_coords,
        max_distance=WALKING_LIMIT, limit=MAX_STATIONS_TO_CHECK)

    # get the fastest station pair itinerary
    min_trip = (float('inf'), None, None)
    # try all combinations of closest stations
    for from_tup, to_tup in itertools.product(from_stations, to_stations):
        from_dist, from_station = from_tup
        to_dist, to_station = to_tup
        if from_station == to_station:
            continue

        w_from = from_dist * WALKING_SPEED
        t_time = t_times[from_station[0]][to_station[0]]
        w_to = to_dist * WALKING_SPEED

        trip_time = w_from + t_time + w_to + T_WAIT_TIME
        if trip_time < min_trip[0]:
            min_trip = (trip_time, (from_station[0], w_from), (to_station[0], w_to))

    if min_trip[0] == float('inf'):
        logging.debug('No close MBTA stations found')
        return None, none_tup, none_tup
    # compare vs taxi trip time
    logging.debug(min_trip)
    if min_trip[0] > 2 * taxi_time:
        logging.debug('No MBTA trips found closer than double taxi route')
    return min_trip


def eval_node_for_trip(t_times, trip, t_old, new_node, new_gap):
    """ Evaluates the effective of adding a new station using one specific taxi trip """
    terminal, new_station, _, _, _ = new_node
    from_coords, to_coords, t_start, t_stop = trip

    trip_saved = 0

    taxi_time = float(int(t_stop) - int(t_start)) / 60.  # converts seconds to minutes

    dist1 = latlng_dist(from_coords, new_station)
    dist2 = latlng_dist(to_coords, new_station)
    start = False

    if dist1 > WALKING_LIMIT and dist2 > WALKING_LIMIT:
        return STOP_NO_IMPROVEMENT

    if dist1 < dist2:
        start = True

    if start:
        to_station = t_old[2][0]
        to_time = t_old[2][1]
        if to_station == None:
            return STOP_NO_IMPROVEMENT
        w_from = dist1 * WALKING_SPEED
        t_time = new_gap + t_times[terminal][to_station]

        t_new = w_from + t_time + to_time + T_WAIT_TIME

    else:
        from_station = t_old[1][0]
        from_time = t_old[1][1]

        if from_station is None:
            return STOP_NO_IMPROVEMENT
        w_to = dist2 * WALKING_SPEED
        t_time = new_gap + t_times[terminal][from_station]
        t_new = from_time + w_to + t_time + T_WAIT_TIME

    if t_new == float('inf'):
        logger.info("didn't calculate t_new for trip: " + str(trip) + " at stop " + str(new_station))
        return STOP_NO_IMPROVEMENT

    if t_new >= t_old[0]:
        return STOP_NO_IMPROVEMENT

    if t_old[0] is None:
        t_dif = t_new
    else:
        t_dif = t_old[0] - t_new

    taxi_time_saved = 0.0

    # trip can only be saved if previous trip was "necessary"
    # this is why we order by T_difs, a fuller picture of the improvement
    if t_new <= taxi_time < t_old[0]:
        trip_saved = 1
        taxi_time_saved = taxi_time - t_new

    return t_dif, taxi_time_saved, trip_saved


def eval_node_for_trips(G, t_times, trips, T_old, new_node):
    """ Evaluates the effective of adding a new station over all specific taxi trip """
    terminal, new_coord, T_difs, taxi_difs, tot_saved = new_node

    # only evaluate those we haven't seen
    if T_difs != NOT_SEEN:
        return terminal, new_coord, T_difs, taxi_difs, tot_saved

    T_difs = 0.0
    taxi_difs = 0.0
    tot_saved = 0

    # new t-gap distance between the new stop and the old terminal
    new_gap_dist = latlng_dist(new_coord, G.node[terminal]['latlng'])
    rate = mbta_graph.GREEN_RATE

    # grabs first line from line array because it's a terminus--just one line
    lineName = G.node[terminal]['lines'][0]
    if "Red" in lineName:
        rate = mbta_graph.RED_RATE

    elif "Blue" in lineName:
        rate = mbta_graph.BLUE_RATE

    elif "Orange" in lineName:
        rate = mbta_graph.ORANGE_RATE

    elif "Silver" in lineName:
        rate = mbta_graph.SILVER_RATE

    new_gap = rate * new_gap_dist
    count = 0
    for i, trip in enumerate(trips):

        if not is_trip_relevant(trip, new_node, T_old[i]):
            count += 1
            continue
        T_improvement, taxi_dif, saved = eval_node_for_trip(t_times, trip, T_old[i], new_node, new_gap)
        T_difs += T_improvement
        taxi_difs += taxi_dif
        tot_saved += saved

    return terminal, new_coord, T_difs, taxi_difs, tot_saved


def get_random_successor(G, old_node):
    terminal, latlng, _, _, _ = old_node
    # type a possible successor
    # This function is random and non deterministic so every run will yield a different result
    RADIUS = 0.01  # TODO make constant, units are unscaled degrees of lat/lng
    terminal_latlng = G.node[terminal]['latlng']

    # do while succ_latlng within terminal
    while True:
        # randomly pick
        theta = random.uniform(0, 2 * np.pi)
        r = random.uniform(RADIUS / 2., RADIUS)
        succ_latlng = make_latlng(
            # todo use cos_scale factor
            latlng[0] + r * cos(theta),
            latlng[1] + r * sin(theta),
        )
        # TODO: pass this as parameter so doesn't have to be recalculate in eval_node_for_trips (optimization)
        gap_dist = latlng_dist(terminal_latlng, succ_latlng)
        allowed_gap = NEW_GAP
        # change gap size for inner-city terminals so as to not cross T lines
        if "Bowdoin" in terminal or "Dudley" in terminal or "Design" in terminal:
            allowed_gap = 0.5

        if gap_dist <= allowed_gap:
            # Allows us to pick another random point if the current one is invalid
            break
    return terminal, succ_latlng, NOT_SEEN, NOT_SEEN, NOT_SEEN


def beam_search(G, t_times, T_old, trips, frontier):
    for _ in xrange(MAX_BEAM_SEARCH_ITERATIONS):
        last_frontier = str(frontier)

        # generate successors
        # TODO make this faster (We calculate frontier (eval_node_for_trips) twice)
        new_frontier = list(frontier)  # we want to consider the existing nodes as well
        for node in frontier:
            succs = [get_random_successor(G, node) for _ in xrange(BRANCH_FACTOR)]
            new_frontier.extend(succs)

        eval_frontier = []

        # evaluate nodes in the frontier
        for node in new_frontier:
            eval_frontier.append(eval_node_for_trips(G, t_times, trips, T_old, node))

        # compute new frontier
        # prune to get FRONTIER_SIZE smallest succs
        frontier = heapq.nlargest(
            FRONTIER_SIZE, eval_frontier,
            key=lambda tup: tup[2],
            # key=lambda new_node: eval_node_for_trips(G, t_times, stations, station_tree, trips, T_old, new_node),
        )
        if str(frontier) == last_frontier:
            # we are done if the best frontier does not change
            break

    return frontier


def main():
    global zero_count
    zero_count = 0
    logging.basicConfig(level=logging.WARN)

    # Load MBTA graph and taxi trips
    graph, avg_gap = mbta_graph.build_graph(MBTA_YAML_PATH)
    logger.debug(avg_gap)
    with open(PREPROCESSED_PATH, 'rb') as trips_stream:
        raw_trips = read_data.read_csv(trips_stream)

    random.shuffle(raw_trips)
    trips = raw_trips[:SAMPLE_NUM]

    T_old = []
    t_times = nx.shortest_path_length(graph, weight='weight')
    stations = graph.nodes(data=True)

    coords = np.array(map(lambda (name, data): data['latlng'], stations))
    logger.debug(coords)

    coords[:, 0] *= cos_factor
    station_tree = cKDTree(coords)  # creates the kd-tree for fast station lookup

    # calc T_old, initial hypothetical T times for taxi trips
    for trip in tqdm(trips, unit=' trips'):
        result = analyze_trip(t_times, stations, station_tree, trip)
        T_old.append(result)

    # logger.warn("There were " + str(zero_count) + " trips that took 0 time.")

    terminals = filter(
        lambda (name, data): graph.degree(nbunch=name) == 1,  # get all nodes of degree 1 (defn of terminus)
        graph.nodes_iter(data=True)
    )

    print "\n"
    print "Number of trips to be analyzed: " + str(SAMPLE_NUM)

    # frontier set for beam search, start frontier at the terminals, and consider successors
    # create node from terminal
    # frontier is a list of node: (terminal, latlng, T_difs, taxi_time_saved, tot_saved)
    frontier = map(lambda (name, data): (name, data['latlng'], NOT_SEEN, NOT_SEEN, NOT_SEEN), terminals)

    print "Running the overall beam search...\n"
    final_frontier = beam_search(graph, t_times, T_old, trips, frontier)

    print "The best stops for the overall beam search are: "
    for i, stop in enumerate(final_frontier):
        print str(i + 1) + ". Near terminal " + stop[0] + ", location " + str(stop[1]) + " saves " + str(
            stop[2]) + "min of T time"

    frontiers = []  # allows us to run once per terminal
    print "\n"
    for term in frontier:
        term_list = [term]
        frontiers.append(term_list)

    final_frontiers = []
    print "Running the by-terminal beam search\n"
    for front in frontiers:
        final_front = beam_search(graph, t_times, T_old, trips, front)
        final_frontiers.append(final_front)

    for f in final_frontiers:
        print "The best three locations for " + f[0][0] + " are: "
        print "1. " + str(f[0][1]) + ", saving " + str(f[0][2]) + " T time"
        print "2. " + str(f[1][1]) + ", saving " + str(f[1][2]) + " T time"
        print "3. " + str(f[2][1]) + ", saving " + str(f[2][2]) + " T time\n\n"


if __name__ == "__main__":
    main()
