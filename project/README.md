# Data Sources

MBTA data taken from http://erikdemaine.org/maps/mbta/mbta.yaml

Taxi data taken from https://data.cityofboston.gov/Transportation/Boston-Taxi-Data/ypqb-henq
  - Taxi data has since been unzipped and deduped.


# Install
```sh
brew install graphviz
pip install -r requirements.txt
```

# Preprocess all data
```sh
python preprocess.py
```

# Run
```sh
python main.py
```