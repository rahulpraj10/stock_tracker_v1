from flask import Flask, render_template, request
import pandas as pd
import requests
import io
import math

app = Flask(__name__)

# Cache configuration
class DataCache:
    def __init__(self):
        self.data = None

cache = DataCache()
DATA_URL = "https://github.com/rahulpraj10/stock_tracker_v1/blob/main/Bhavdata/StockData.pkl?raw=true"

def get_data():
    if cache.data is not None:
         return cache.data

    try:
        response = requests.get(DATA_URL)
        response.raise_for_status()
        df = pd.read_pickle(io.BytesIO(response.content))
        
        # --- Data Cleaning Logic ---
        cols_to_check = [col for col in df.columns if '|' in str(col)]
        
        if cols_to_check:
            clean_dfs = []
            for col in df.columns:
                if '|' in str(col):
                    headers = str(col).split('|')
                    # Clean headers: remove potential whitespace
                    headers = [h.strip() for h in headers]
                    
                    split_data = df[col].astype(str).str.split('|', expand=True)
                    
                    if split_data.shape[1] == len(headers):
                        split_data.columns = headers
                    else:
                        split_data.columns = headers[:split_data.shape[1]]
                        
                    clean_dfs.append(split_data)
                else:
                    clean_dfs.append(df[[col]])
            
            df = pd.concat(clean_dfs, axis=1)
        
        # General whitespace cleanup for ALL column headers
        df.columns = df.columns.astype(str).str.strip()

        cache.data = df
        return df
    except Exception as e:
        print(f"Error loading/parsing data: {e}")
        return pd.DataFrame()

@app.route('/')
def index():
    df = get_data()
    if df.empty:
        return "Error loading data or no data available."

    # Filters
    sc_code_filter = request.args.get('SC_CODE', '').strip()

    filtered_df = df.copy()
    
    # Filter by SC_CODE
    # We look for 'SC_CODE' column. 
    # Since we stripped whitespace in get_data(), it should be 'SC_CODE'.
    if sc_code_filter and 'SC_CODE' in filtered_df.columns:
        # Case insensitive partial match
        filtered_df = filtered_df[filtered_df['SC_CODE'].astype(str).str.contains(sc_code_filter, case=False, na=False)]
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 100
    total_records = len(filtered_df)
    total_pages = math.ceil(total_records / per_page)
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1

    start = (page - 1) * per_page
    end = start + per_page
    
    page_data = filtered_df.iloc[start:end]
    records = page_data.to_dict(orient='records')
    columns = page_data.columns.tolist()

    return render_template(
        'index.html',
        records=records,
        columns=columns,
        current_page=page,
        total_pages=total_pages,
        total_records=total_records,
        sc_code_filter=sc_code_filter
    )

if __name__ == '__main__':
    app.run(debug=True)
