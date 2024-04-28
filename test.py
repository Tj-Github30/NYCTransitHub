from math import radians, sin, cos, sqrt, atan2
import json
import heapq

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




# Read station data from JSON file 
with open('data/stations_test.json', 'r') as f:
    station_data = json.load(f)
threshold_distance = 1.0  
adjacency_map = build_adjacency_map(station_data, threshold_distance)
#print(adjacency_map)
start_node = '140'
end_node = '110'
shortest_distance = dijkstra(adjacency_map, start_node, end_node)
shortest_distance, path, route = dijkstra(adjacency_map, start_node, end_node)
# Print the adjacency map for debugging
# print("Adjacency Map:")
# for station, neighbors in adjacency_map.items():
#     print(station, "->", neighbors)
print("Shortest distance from", start_node, "to", end_node, ":", shortest_distance)
print("Path:", path)
print("Route: ", route)
