import argparse
import logging
import time

import networkx as nx
import yaml

from constants import *
from util import latlng_dist, make_latlng

logger = logging.getLogger(__name__)

# constants
# taken from: http://www.mbta.com/uploadedfiles/documents/Bluebook%202010.pdf, which lists it in miles
GREEN_RATE = 4 / .584  # time (min) from Copley to Arlington (Green Line) / dist (km)
RED_RATE = 3 / 1.14  # time from Kendall/MIT to Charles/MGH / dist
BLUE_RATE = 2 / 1.01  # time from Airport to Wood Island / dist
ORANGE_RATE = 2 / .41  # time from Ruggles to Mass Ave / dist
# average speed of car in boston (http://infinitemonkeycorps.net/projects/cityspeed/): 33.635 km/hr -> convert to min/km
SILVER_RATE = 1 / (33.635 / 60)


def build_graph(yaml_file):
    # note for later: we'll probably want to get rid of the commuter rail data
    line_dists = []
    overall_start = time.time()
    with open(yaml_file, 'r') as mbta_file:
        mbta_data = yaml.load(mbta_file)

        M = nx.Graph()

        logger.info("%s MBTA lines loaded", len(mbta_data))

    node_ind = 0
    dist_sum = 0.0
    count = 0

    for line in mbta_data:  # MBTA line, that is
        lineName = line['title']
        prev_name = ""
        line_dist = 0

        if "Commuter" in lineName:
            break

        print "Building the " + lineName + "..." + "\n"
        start_time = time.time()

        for station in line['stations']:

            if 'title' not in station:
                continue
            curr_name = station['title']

            if curr_name in M.node:
                M.node[curr_name]['lines'].append(lineName)
            else:
                # print "N_" + str(node_ind) + ": " + s_name
                node_ind += 1
                M.add_node(curr_name, {
                    'lat': station['latitude'],
                    'long': station['longitude'],
                    'latlng': make_latlng(station['latitude'], station['longitude']),
                    'lines': [lineName],
                    'shape': 'rect',
                })

            if prev_name != "":
                prev_node = M.node[prev_name]
                curr_node = M.node[curr_name]
                latlng1 = prev_node['latlng']
                latlng2 = curr_node['latlng']
                dist = latlng_dist(latlng1, latlng2)
                line_dist += dist

                dist_sum += dist
                count += 1

                # default to green, since it has the most stations

                color = line['color']

                min_per_km = GREEN_RATE

                if "Red" in lineName:
                    min_per_km = RED_RATE

                elif "Blue" in lineName:
                    color = '#0000ff'
                    min_per_km = BLUE_RATE

                elif "Orange" in lineName:
                    min_per_km = ORANGE_RATE

                elif "Silver" in lineName:
                    min_per_km = SILVER_RATE

                w = min_per_km * dist

                M.add_edge(prev_name, curr_name, {
                    'color': color,
                    'weight': w,
                    'len': (1 + dist) / 2
                })

                print "Edge: {}({}), {}({}), {}min, {}km".format(prev_name, latlng1, curr_name, latlng2, w, dist)

            prev_name = curr_name

        line_dists.append(line_dist)

        dif = time.time() - start_time
        print "\nBuilt line in " + str(dif) + "s"
        print "\n\n"

    overall_dif = time.time() - overall_start
    print "Imported data and built graph in " + str(overall_dif) + "s\n"

    avg_gap = float(dist_sum / count)
    return M, avg_gap


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-m", "--mbta-yaml",
                    default=MBTA_YAML_PATH, help="YAML file containing MBTA station and line data")
parser.add_argument("-o", "--output",
                    default=DEBUG_GRAPH_PATH, help="Path of the file to be output. Note will overwrite files.\n"
                                                   "Uses the path extension to determine what type of file ot output including: jpg, png, and svg.\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()

    mbta_graph, gap = build_graph(args.mbta_yaml)

    a_graph = nx.nx_agraph.to_agraph(mbta_graph)
    logger.info('Laying out graph')
    a_graph.layout()  # uses neato layout
    logger.info('Printing graph to %s', args.output)
    a_graph.draw(args.output)
