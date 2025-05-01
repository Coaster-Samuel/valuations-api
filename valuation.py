import requests
import json
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Database filename
DATABASE = 'property_data.db'


def create_tables():
    """Create the properties table in the database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Define the schema based on data structure
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY,
            valuer_id INTEGER,
            property_number TEXT,
            parent_valuation REAL,
            project_id INTEGER,
            owner_name TEXT,
            property_type TEXT,
            property_design TEXT,
            construction_stage TEXT,
            year_built INTEGER,
            age REAL,
            eul REAL,
            rel REAL,
            measurements TEXT,
            no_rooms INTEGER,
            no_of_bathrooms INTEGER,
            occupancy INTEGER,
            attributes TEXT,
            title_deeds_available TEXT,
            certificate_of_search_available TEXT,
            encumbrances_available TEXT,
            defects TEXT,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()


def fetch_data(url):
    """Fetches data from the core system API."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None


def insert_data(data):
    """Insert the fetched data into the database."""
    if not data or 'data' not in data:
        print("No data to insert.")
        return
    
    records = data['data']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    for item in records:
        try:
            # Insert with parameterized query for safety
            cursor.execute('''
                INSERT OR REPLACE INTO properties (
                    id, valuer_id, property_number, parent_valuation, project_id,
                    owner_name, property_type, property_design, construction_stage,
                    year_built, age, eul, rel, measurements, no_rooms,
                    no_of_bathrooms, occupancy, attributes, title_deeds_available,
                    certificate_of_search_available, encumbrances_available,
                    defects, description
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                item.get('id'), 
                item.get('valuer_id'), 
                item.get('property_number'),
                item.get('parent_valuation'),
                item.get('project_id'),
                item.get('owner_name'),
                item.get('property_type'),
                item.get('property_design'),
                item.get('construction_stage'),
                int(item.get('year_built')) if item.get('year_built') else None,
                item.get('age'),
                item.get('eul'),
                item.get('rel'),
                item.get('measurements'),
                item.get('no_rooms'),
                item.get('no_of_bathrooms'),
                item.get('occupancy'),
                item.get('attributes'),
                item.get('title_deeds_available'),
                item.get('certificate_of_search_available'),
                item.get('encumbrances_available'),
                item.get('defects'),
                item.get('description')
            ))
        except Exception as e:
            print(f"Error inserting item {item.get('id')}: {e}")
            continue
    conn.commit()
    conn.close()


@app.route('/properties', methods=['GET'])
def get_properties():
    """Expose stored data with optional search/filter parameters."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Example filters: search by owner_name or property_type
    owner_name = request.args.get('owner_name')
    property_type = request.args.get('property_type')

    query = "SELECT * FROM properties WHERE 1=1"
    params = []

    if owner_name:
        query += " AND owner_name LIKE ?"
        params.append(f"%{owner_name}%")
    if property_type:
        query += " AND property_type LIKE ?"
        params.append(f"%{property_type}%")
    
    cursor.execute(query, params)
    rows = cursor.fetchall()

    # Map data to JSON
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in rows]

    conn.close()
    return jsonify(results)


if __name__ == '__main__':
    create_tables()  # Create tables on startup
    # Fetch data from external API and store it in DB
    data = fetch_data("https://staging.valuationsafrica.mw/api/v2/properties")
    if data:
        insert_data(data)
    # Run the API server
    app.run(debug=True, port=5000)
