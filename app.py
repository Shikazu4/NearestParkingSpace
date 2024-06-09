from flask import Flask, request, jsonify, send_from_directory
import json
from geopy.distance import geodesic
from pyproj import Transformer
from shapely.geometry import shape, MultiPolygon, Point
import logging

app = Flask(__name__, static_url_path='')

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load the formatted parking areas geoJSON data
with open('parking_areas.geojson') as f:
    parking_data = json.load(f)

#transformer to convert from the projected coordinate system (EPSG:2966) to WGS84 (EPSG:4326)
transformer = Transformer.from_crs("epsg:2966", "epsg:4326")

def transform_coordinates(coords):
    lon, lat = transformer.transform(coords[0], coords[1])
    return [lon, lat]

def find_nearest_parking(lat, lon):
    user_location = (lat, lon)
    nearest_parkings = []

    for feature in parking_data['features']:
        geom = shape(feature['geometry'])
        if isinstance(geom, MultiPolygon):
            parking_location = transform_coordinates(geom.centroid.coords[0])
        else:
            parking_location = transform_coordinates(geom.coords[0])
                
        distance = geodesic(user_location, parking_location).meters
        nearest_parkings.append({
            'name': feature['properties'].get('name', 'Unnamed Parking'),
            'spaces': feature['properties'].get('spaces', 'Unknown'),
            'distance': distance,
            'coordinates': parking_location  # Leaflet [lat, lon]
        })

    nearest_parkings.sort(key=lambda x: x['distance'])
    return nearest_parkings[:5]  # Return the 5 nearest parking spaces

@app.route('/')
def serve_index():
    return send_from_directory('', 'index.html')

@app.route('/nearest_parking', methods=['GET'])
def nearest_parking():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        logging.debug(f'Received request for nearest parking with lat: {lat}, lon: {lon}')
        nearest_parkings = find_nearest_parking(lat, lon)
        logging.debug(f'Nearest parking results: {nearest_parkings}')
        return jsonify(nearest_parkings)
    except Exception as e:
        logging.error(f'Error processing request: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
