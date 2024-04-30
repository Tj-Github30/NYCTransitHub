# coding: utf-8
"""
    mta-api-sanity
    ~~~~~~

    Expose the MTA's real-time subway feed as a json api

    :copyright: (c) 2014 by Jon Thornton.
    :license: BSD, see LICENSE for more details.
"""

from mtapi.mtapi import Mtapi
from flask import Flask, jsonify, request, Response, render_template, abort, redirect, url_for
import json
from datetime import datetime
from functools import wraps, reduce
import logging
import os
from flask_socketio import SocketIO
from math import radians, sin, cos, sqrt, atan2
import json
import heapq
from collections import deque
from datetime import datetime


app = Flask(__name__)
app.config.update(
    MAX_TRAINS=10,
    MAX_MINUTES=30,
    CACHE_SECONDS=60,
    THREADED=True
)
socketio = SocketIO(app)

_SETTINGS_ENV_VAR = 'MTAPI_SETTINGS'
_SETTINGS_DEFAULT_PATH = './settings.cfg'
if _SETTINGS_ENV_VAR in os.environ:
    app.config.from_envvar(_SETTINGS_ENV_VAR)
elif os.path.isfile(_SETTINGS_DEFAULT_PATH):
    app.config.from_pyfile(_SETTINGS_DEFAULT_PATH)
else:
    raise Exception('No configuration found! Create a settings.cfg file or set MTAPI_SETTINGS env variable.')

# set debug logging
if app.debug:
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# class CustomJSONEncoder(json.JSONEncoder):
#     def default(self, obj):
#         try:
#             if isinstance(obj, datetime):
#                 return obj.isoformat()
#             iterable = iter(obj)
#         except TypeError:
#             pass
#         else:
#             return list(iterable)
#         return JSONEncoder.default(self, obj)

mta = Mtapi(
    app.config['MTA_KEY'],
    app.config['STATIONS_FILE'],
    max_trains=app.config['MAX_TRAINS'],
    max_minutes=app.config['MAX_MINUTES'],
    expires_seconds=app.config['CACHE_SECONDS'],
    threaded=app.config['THREADED'])


# Load the stations from stations.json
with open('./data/stations_test.json', 'r') as file:
    stations = json.load(file)

def get_routes_for_station(station_id):
    routes = set()  # Initialize an empty set to store unique routes
    
    # Loop through each station object in the station data
    station_data = mta.get_by_id(station_id)
    
    for station_obj in station_data:  
        routes.update(station_obj['routes'])
    return list(routes)

# Update stations with routes
def update_stations_with_routes():
    for station_id, station_data in stations.items():
        ids = station_id.split(',')
        routes = get_routes_for_station(ids)
        station_data['route'] = routes
    # Write the updated station data back to the JSON file
    with open('./data/stations_test.json', 'w') as file:
        json.dump(stations, file)

def create_adjacency_map(stations_data):
    # Extract routes for each station using station names as keys
    stations_routes = {details['name']: details['routes'] for _, details in stations_data.items()}

    # Create an adjacency map where keys are station names and values are sets of adjacent station names
    adjacency_map = {}

    for station_name, routes in stations_routes.items():
        adjacency_map[station_name] = list()
        for other_station_name, other_routes in stations_routes.items():
            if station_name != other_station_name and set(routes).intersection(other_routes):
                adjacency_map[station_name].append(other_station_name)

    return adjacency_map

def find_shortest_path(graph, start, goal):
    queue = deque([[start]])
    
    visited = set()

    while queue:
        path = queue.popleft()
        vertex = path[-1]
        if vertex == goal:
            return path
        elif vertex not in visited:
            visited.add(vertex)
            for current_neighbour in graph.get(vertex, []):
                new_path = list(path)
                new_path.append(current_neighbour)
                queue.append(new_path)
    return "No path found."

def calculate_path(source_name, destination_name):    
    adjacency_map = create_adjacency_map(stations)
    shortest_path = find_shortest_path(adjacency_map, source_name, destination_name)  
    # Print results
    print("Shortest distance from", source_name, "to", destination_name, ":", shortest_path)
    return shortest_path

@app.route('/',methods=['GET'])
def index():
    update_stations_with_routes()
    routes_json = get_routes()  # Assuming routes() returns a JSON string
    routes_data = json.loads(routes_json)  # Parse JSON string into dictionary
    return render_template('index.html', routes=routes_data)

@app.route('/plan-route', methods=['GET'])
def route_planner():
    # Extract station names from station data
    station_names = set([stations[station]['name'] for station in stations])
    return render_template('route_planner.html', stations=station_names)

@app.route('/plan-route', methods=['POST'])
def plan_route():
    source_name = request.form['source']
    destination_name = request.form['destination']
    
    # Call the path function to compute the shortest path
    shortest_path = calculate_path(source_name, destination_name)
    
    # Pass the results to the template
    return render_template('final_route.html', 
                           source=source_name,
                           destination=destination_name,
                           shortest_path=shortest_path)  # Pass shortest_path instead of shortest_distance

@app.route('/by-location', methods=['GET'])
def by_location():
    try:
        lat = float(request.args['lat'])
        lon = float(request.args['lon'])
    except KeyError as e:
        return render_template('error.html', error='Missing lat/lon parameter')
    except ValueError as e:
        return render_template('error.html', error='Invalid lat/lon values')

    data = mta.get_by_point((lat, lon), 5)
    updated = mta.last_update()
        # Calculate the remaining minutes for each train
    for station in data:
        for direction in ['N', 'S']:  # Handling both directions
            if direction in station:
                for train in station[direction]:
                    # Check if train['time'] is already a datetime object
                    if isinstance(train['time'], datetime):
                        train_time = train['time']
                    elif isinstance(train['time'], str):
                        train_time = datetime.fromisoformat(train['time'])
                    else:
                        continue  # Skip or handle unexpected data type
                    
                    remaining_minutes = int((train_time - updated).total_seconds() / 60)
                    train['remaining_minutes'] = remaining_minutes
    return render_template('bylocation.html', data=data, updated=mta.last_update())

@app.route('/find-station', methods=['GET'])
def find_station():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
    except TypeError:
        return render_template('error.html', error="Invalid or missing latitude/longitude.")
    except ValueError:
        return render_template('error.html', error="Invalid latitude or longitude format.")

    nearest_station, distance = find_nearest_station(lat, lon)
    station_lat = None
    station_lon = None
    print(nearest_station)
    for station_id, station_info in stations.items():
        if station_info['name'] == nearest_station['name']:
            station_lat = float(station_info['location'][0])
            station_lon = float(station_info['location'][1])
            break
    print(station_lat,station_lon)
    data = mta.get_by_point((station_lat,station_lon ), 5)
    updated = mta.last_update()
        # Calculate the remaining minutes for each train
    for station in data:
        for direction in ['N', 'S']:  # Handling both directions
            if direction in station:
                for train in station[direction]:
                    # Check if train['time'] is already a datetime object
                    if isinstance(train['time'], datetime):
                        train_time = train['time']
                    elif isinstance(train['time'], str):
                        train_time = datetime.fromisoformat(train['time'])
                    else:
                        continue  # Skip or handle unexpected data type
                    
                    remaining_minutes = int((train_time - updated).total_seconds() / 60)
                    train['remaining_minutes'] = remaining_minutes

    return render_template('nearestStation.html', data=data, station=nearest_station,lat=lat,lon=lon ,distance=distance)

@app.route('/by-route/<route>', methods=['GET'])
def by_route(route):
    if route.islower():
        return redirect(request.host_url + 'by-route/' + route.upper(), code=301)

    try:
        data = mta.get_by_route(route)
        updated = mta.last_update()
        
        # Convert updated to datetime if it's a string
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)

        # Calculate the remaining minutes for each train
        for station in data:
            for direction in ['N', 'S']:  # Handling both directions
                if direction in station:
                    for train in station[direction]:
                        # Check if train['time'] is already a datetime object
                        if isinstance(train['time'], datetime):
                            train_time = train['time']
                        elif isinstance(train['time'], str):
                            train_time = datetime.fromisoformat(train['time'])
                        else:
                            continue  # Skip or handle unexpected data type
                        
                        remaining_minutes = int((train_time - updated).total_seconds() / 60)
                        train['remaining_minutes'] = remaining_minutes

        return render_template('byRoute.html', data=data, updated=updated, route=route)
    except KeyError:
        return render_template('error.html', error='Station not found')

@app.route('/by-stations', methods=['GET', 'POST'])
def by_stations():
     # Extract station names from station data
    station_names = set([stations[station]['name'] for station in stations])
    if request.method == 'POST':
        station_name = request.form['station_name']
        # Search for the station by name and fetch the location
        for station_id, station_info in stations.items():
            if station_info['name'].lower() == station_name.lower():  # Case insensitive match
                location = station_info['location']
                lat, lon = location
                return redirect(url_for('by_location', lat=lat, lon=lon))
            
        # return f"Search result for: {station_name}"
    return render_template('by_stations.html', stations=station_names)


@app.route('/by-id/<id_string>', methods=['GET'])
def by_index(id_string):
    ids = id_string.split(',')
    try:
        data = mta.get_by_id(ids)
        return render_template('byId.html', data=data)
    except KeyError as e:
        return render_template('error.html', error='Station not found')

@app.route('/routes', methods=['GET'])
def get_routes():
    routes_data = sorted(mta.get_routes())
    return json.dumps(routes_data)



def find_nearest_station(lat, lon):
    min_distance = None
    nearest_station = None
    for station_id, station_info in stations.items():
        station_lat, station_lon = station_info['location']
        dist = calculate_distance(lat, lon, station_lat, station_lon)
        if min_distance is None or dist < min_distance:
            min_distance = dist
            nearest_station = station_info

    return nearest_station, min_distance

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 3959  # Earth radius in miles
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    a = sin(dLat/2) * sin(dLat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2) * sin(dLon/2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    return distance 


# WebSocket event handlers

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# # WebSocket event handler to start data refresh
# @socketio.on('start_refresh')
# def start_refresh():
#     while True:
#         emit_updated_data()
#         time.sleep(60)  # Refresh data every 60 seconds
        

# Run the Flask application with SocketIO
if __name__ == '__main__':
    socketio.run(app, debug=True)

