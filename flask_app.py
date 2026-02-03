from flask import Flask, render_template, request
import pandas as pd
import requests
import io
import math

app = Flask(__name__)

# Cache configuration - simple in-memory cache
class DataCache:
    def __init__(self):
        self.data = None
        self.expiry = None

cache = DataCache()
DATA_URL = "https://github.com/rahulpraj10/stock_tracker_v1/blob/main/Bhavdata/StockData.pkl?raw=true"

def get_data():
    # For simplicity, we fetch every time or we can implement primitive caching
    # Since it's a demo/lite app, fetching fresh or creating a simple singleton is fine.
    # We'll use a singleton pattern for now to avoid re-downloading on every page turn
    if cache.data is not None:
         return cache.data

    try:
        response = requests.get(DATA_URL)
        response.raise_for_status()
        df = pd.read_pickle(io.BytesIO(response.content))
        cache.data = df
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame() # Empty DF on failure

@app.route('/')
def index():
    df = get_data()
    if df.empty:
        return "Error loading data or no data available."

    # Filtering
    # We support filtering by SC_CODE and SC_NAME as examples
    sc_code_filter = request.args.get('SC_CODE', '').strip()
    sc_name_filter = request.args.get('SC_NAME', '').strip()

    filtered_df = df.copy()
    
    if sc_code_filter:
        # Exact match or contains? Let's do string contains for flexibility, assuming Code is numeric but treated as str for search
        filtered_df = filtered_df[filtered_df['SC_CODE'].astype(str).str.contains(sc_code_filter, case=False, na=False)]
    
    if sc_name_filter:
        filtered_df = filtered_df[filtered_df['SC_NAME'].str.contains(sc_name_filter, case=False, na=False)]

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 100
    total_records = len(filtered_df)
    total_pages = math.ceil(total_records / per_page)
    
    # Bound page
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1

    start = (page - 1) * per_page
    end = start + per_page
    
    # Get page data
    page_data = filtered_df.iloc[start:end]
    
    # Convert to dict for template
    records = page_data.to_dict(orient='records')
    columns = page_data.columns.tolist()

    return render_template(
        'index.html',
        records=records,
        columns=columns,
        current_page=page,
        total_pages=total_pages,
        total_records=total_records,
        sc_code_filter=sc_code_filter,
        sc_name_filter=sc_name_filter
    )

if __name__ == '__main__':
    app.run(debug=True)
