# coding: utf-8
"""
    mta-api-sanity
    ~~~~~~

    Expose the MTA's real-time subway feed as a json api

    :copyright: (c) 2014 by Jon Thornton.
    :license: BSD, see LICENSE for more details.
"""

from mtapi.mtapi import Mtapi
from flask import Flask, jsonify, request, Response, render_template, abort, redirect
import json
from datetime import datetime
from functools import wraps, reduce
import logging
import os
from flask_socketio import SocketIO
from math import radians, sin, cos, sqrt, atan2
import json
import heapq

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

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)

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

def dijkstra(adjacency_map, start, end):
    # Initialize distances, routes, and previous nodes
    distances = {node: float('inf') for node in adjacency_map}
    routes = {node: None for node in adjacency_map}
    prev = {node: None for node in adjacency_map}
    distances[start] = 0
    
    # Initialize priority queue
    pq = [(0, start, None)]  # Include start route as None
    
    while pq:
        # Get node with smallest distance
        curr_distance, curr_node, curr_route = heapq.heappop(pq)

        # If node already visited, skip
        if curr_distance > distances[curr_node]:
            continue

        # Update route for the current node
        routes[curr_node] = curr_route

        # If destination reached, reconstruct path and return
        if curr_node == end:
            path = []
            route = []
            while curr_node is not None:
                path.append(curr_node)
                route.append(routes[curr_node])  # Append current route
                curr_node = prev[curr_node]  # Update current node
            path.reverse()
            route.reverse()
            return round(distances[end], 2), path, route
        
        # Visit neighbors
        for neighbor, route, weight in adjacency_map[curr_node]:
            distance = curr_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                prev[neighbor] = curr_node
                heapq.heappush(pq, (distance, neighbor, route))  # Include current route
    
    # If destination not reachable
    return float('inf'), [], []






def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in kilometers

    # Convert latitude and longitude from degrees to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    # Calculate the differences between latitudes and longitudes
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Calculate the distance using Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return round(distance, 2)

def build_adjacency_map(station_data, threshold_distance):
    adjacency_map = {}

    for station_id1, station1 in station_data.items():
        adjacent_stations = []
        for station_id2, station2 in station_data.items():
            if station_id1 != station_id2:
                distance = calculate_distance(station1['location'][0], station1['location'][1],
                                              station2['location'][0], station2['location'][1])
                if distance <= threshold_distance:
                    for route in station1['routes']:  # Include routes from station1
                        adjacent_stations.append((station_id2, route, distance))
        adjacency_map[station_id1] = adjacent_stations

    return adjacency_map



def calculate_path(source_name, destination_name):
    
    # Find IDs of source and destination stations
    source_id = None
    destination_id = None
    for station_id, station in stations.items():
        if station['name'] == source_name:
            source_id = station_id
            # print("Source id: ", source_id)
        elif station['name'] == destination_name:
            destination_id = station_id
            # print("Dest id: ", destination_id)
    
    if source_id is None or destination_id is None:
        print("Source or destination station not found.")
        return None, None, None  # Return None if source or destination not found
    
    threshold_distance = 1.0  
    adjacency_map = build_adjacency_map(stations, threshold_distance)


    # Compute shortest path
    shortest_distance, path, route = dijkstra(adjacency_map, source_id, destination_id)
    
    # Print results
    print("Shortest distance from", source_id, "to", destination_id, ":", shortest_distance)
    print("Path:", path)
    print("Route: ", route)
    return shortest_distance, path, route

# Route handler for /plan-route endpoint
@app.route('/plan-route', methods=['POST'])
def plan_route():
    source_name = request.form['source']
    destination_name = request.form['destination']
    
    # Call the path function to compute the shortest path
    shortest_distance, path_result, route_result = calculate_path(source_name, destination_name)
    
    # Pass the results to the template
    return render_template('final_route.html', 
                           source=source_name,
                           destination=destination_name,
                           shortest_distance=shortest_distance,
                           path=path_result,
                           route=route_result,
                           stations=stations)


@app.route('/',methods=['GET'])
def index():
    update_stations_with_routes()
    routes_json = get_routes()  # Assuming routes() returns a JSON string
    routes_data = json.loads(routes_json)  # Parse JSON string into dictionary
    return render_template('index.html', routes=routes_data)

@app.route('/plan-route', methods=['GET'])
def route_planner():
    # Extract station names from station data
    station_names = [stations[station]['name'] for station in stations]
    print(station_names)
    return render_template('route_planner.html', stations=station_names)

@app.route('/by-location', methods=['GET'])
def by_location():
    try:
        location = (float(request.args['lat']), float(request.args['lon']))
    except KeyError as e:
        print(e)
        return render_template('error.html', error='Missing lat/lon parameter')

    data = mta.get_by_point(location, 5)
    return render_template('bylocation.html', data=data, updated=mta.last_update())

@app.route('/by-route/<route>', methods=['GET'])
def by_route(route):

    if route.islower():
        return redirect(request.host_url + 'by-route/' + route.upper(), code=301)

    try:
        data = mta.get_by_route(route)
        return render_template('byRoute.html', data=data, updated=mta.last_update(), route=route)
    except KeyError:
        return render_template('error.html', error='Station not found')

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


def _envelope_reduce(a, b):
    if a['last_update'] and b['last_update']:
        return a if a['last_update'] < b['last_update'] else b
    elif a['last_update']:
        return a
    else:
        return b

def _make_envelope(data):
    time = None
    if data:
        time = reduce(_envelope_reduce, data)['last_update']

    return {
        'data': data,
        'updated': time
    }

if __name__ == '__main__':
    app.run(use_reloader=False)
