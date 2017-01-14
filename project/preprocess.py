#!/bin/env python2

import argparse
import calendar
import csv
import os
import sys
from datetime import datetime

from constants import *


def create_id(trip, pickups_file):
    """ Returns a id stirp unique across all trip data """
    return pickups_file + '-' + trip.get('ID', trip.get('TRIP_ID'))


def parse_time(time_str):
    """ Returns an epoch time for quicker parsing, parsing the date as needed"""
    if time_str[-1] == 'M':
        dt = datetime.strptime(time_str, PREPROCESSED_12HR_DATE_FORMAT)
    else:
        dt = datetime.strptime(time_str, PREPROCESSED_24HR_DATE_FORMAT)
    return calendar.timegm(dt.timetuple())


def cross_check_trips(pickups_file, dropoffs_file):
    """ Makes sure all trips have the same pickup and dropoff """
    trips = {}
    # Load pickups
    print "Reading pickups file: %s" % pickups_file
    with open(pickups_file, 'r') as file:
        reader = csv.DictReader(file)
        for trip in reader:
            id = create_id(trip, pickups_file)
            trips[id] = trip

    # cross reference dropoffs
    matched_trips = set()

    print "Reading dropoffs file: %s" % dropoffs_file
    with open(dropoffs_file, 'r') as file:
        reader = csv.DictReader(file)
        for trip in reader:
            id = create_id(trip, pickups_file)
            if id in trips:
                trips[id].update(trip)
                matched_trips.add(id)

    # Filter out unmatched trips
    real_trips = {}
    for id, trip in trips.iteritems():
        if id in matched_trips:
            real_trip = {}
            for key, value in trip.iteritems():
                if PREPROCESSED_KEYS.has_key(key):
                    real_trip[PREPROCESSED_KEYS[key]] = value

            real_trips[id] = real_trip
            # Load dates as unix time
            real_trip['PICKUP_TIME'] = parse_time(real_trip['PICKUP_TIME'])
            real_trip['DROPOFF_TIME'] = parse_time(real_trip['DROPOFF_TIME'])

    print "Found %d complete trips" % len(real_trips)
    return real_trips


def write_output(output_path, trips, use_stdout=False, clear_file=True):
    """ Writes out trips to a CSV file """
    print "%s to %s" % ('Writing' if clear_file else 'Appending', output_path)
    dir = os.path.dirname(output_path)
    if not os.path.exists(dir):
        os.makedirs(dir)
    if use_stdout:
        writer = csv.DictWriter(sys.stdout, fieldnames=PREPROCESSED_KEYS)
        if clear_file: writer.writeheader()
        writer.writerows(trips.itervalues())
    else:
        with open(output_path, 'wb' if clear_file else 'ab') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=set(PREPROCESSED_KEYS.values()))
            if clear_file: writer.writeheader()
            writer.writerows(trips.itervalues())


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-p", "--pickups", action='append',
                    help="CSV file containing taxi pickups, defaults to all pickup files")
parser.add_argument("-d", "--dropoffs", action='append',
                    help="CSV file containing taxi dropoffs, defaults to all dropoff files")
group = parser.add_mutually_exclusive_group()
group.add_argument("-O", "--stdout", action="store_true", help="If set, prints output to standard out")
group.add_argument("-o", "--output",
                   default=PREPROCESSED_PATH, help="Path of the CSV file to be output")

if __name__ == "__main__":
    args = parser.parse_args()

    # set default arguments
    if not args.pickups:
        args.pickups = TAXI_PICKUP_PATHS
    if not args.dropoffs:
        args.dropoffs = TAXI_DROPOFF_PATHS

    for i, (pickup, dropoff) in enumerate(zip(args.pickups, args.dropoffs)):
        trips = cross_check_trips(pickup, dropoff)
        write_output(
            args.output, trips,
            use_stdout=args.stdout, clear_file=(i == 0),
        )
