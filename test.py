

# def save_adjacency_map_to_file(adjacency_map, filename):
    # with open(filename, 'w') as file:
    #     for station, connections in adjacency_map.items():
    #         # Convert the set of connections to a comma-separated string
    #         connections_str = ', '.join(connections)
    #         # Write station and its connections to the file
    #         file.write(f"{station}: {connections_str}\n")

import json
from collections import deque

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
                print(queue)
    return "No path found."
    

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



def load_adjacency_map_from_string(data):
    adjacency_map = {}
    # lines = data.splitlines()  # This splits the string into lines, simulating reading lines from a file
    for line in data:
        parts = line.strip().split(': ')
        if len(parts) == 2:
            station, connected_stations = parts
            adjacency_map[station] = set(connected_stations.split(', '))
        elif len(parts) == 1 and parts[0]:  # Non-empty line with just a station name
            adjacency_map[parts[0]] = set()  # Add station with no connections
    return adjacency_map


# Usage
# Ensure to load the JSON file into a dictionary
with open('data/stations_test.json', 'r') as file:
    stations_data = json.load(file)


# Create the adjacency map
adjacency_map = create_adjacency_map(stations_data)

map = load_adjacency_map_from_string(adjacency_map)

# filename = 'data/abcd.txt'
# save_adjacency_map_to_file(adjacency_map, filename)


# Print the adjacency map for debugging
print("Adjacency Map:")
for station, neighbors in adjacency_map.items():
    if(station=='Jay St-MetroTech'):
        print(station, "->", neighbors)

# Example usage:
start_station = "Jay St-MetroTech"
end_station = "Dyckman St"
shortest_path = find_shortest_path(adjacency_map, start_station, end_station)
print("Shortest path:", shortest_path)

stations_name_for_print = set()
for _,details in stations_data.items():
   stations_name_for_print.add(details['name'])

print("ALL STATIONS LIST",stations_name_for_print)