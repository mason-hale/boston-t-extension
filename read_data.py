#!/bin/env python2

# Reads preprocessed data

import csv
import fileinput
import logging

from tqdm import tqdm

from constants import *
from util import make_latlng

logger = logging.getLogger(__name__)


def parse_row(row):
    """ given a dict from the csv.DictReader, returns a ruple of parsed data """
    dropoff = make_latlng(row['DROPOFF_LAT'], row['DROPOFF_LONG'])
    pickup = make_latlng(row['PICKUP_LAT'], row['PICKUP_LONG'])
    dropoff_time = row['DROPOFF_TIME']
    pickup_time = row['PICKUP_TIME']

    return (pickup, dropoff, pickup_time, dropoff_time)


def read_csv(input_stream):
    reader = csv.DictReader(input_stream)
    # make sure file is in the right format
    assert set(reader.fieldnames) == set(PREPROCESSED_KEYS.values())
    # read in taxi trip rows, tqdm wrapper producess progress bar
    iterator = tqdm(reader, desc='loading trip input', unit=' trips', mininterval=0.2)
    return map(parse_row, iterator)


if __name__ == "__main__":
    """ Debug CLI to test file reading. """
    logging.basicConfig(level=logging.INFO)
    input_stream = fileinput.input(mode='rb', openhook=fileinput.hook_compressed)
    trips = read_csv(input_stream)
    logger.info('File read with %s trips', len(trips))
