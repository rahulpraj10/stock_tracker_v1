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
        # Check if the dataframe has bad columns (fused with |)
        # Typically if loaded with comma default, we might see one column like "SC_CODE|SC_NAME|..."
        
        cols_to_check = [col for col in df.columns if '|' in str(col)]
        
        if cols_to_check:
            # We have fused columns. Let's assume the first column is the fused one.
            # And 'DownloadDate' might be separate if it was added correctly after read.
            # Or if read_csv faild, everything might be messy.
            
            # Strategy:
            # 1. Identify valid separate columns (like DownloadDate)
            # 2. Identify the fused column.
            # 3. Split the fused column.
            
            clean_dfs = []
            
            for col in df.columns:
                if '|' in str(col):
                    # This is a fused column. Split the column name to get headers.
                    headers = str(col).split('|')
                    
                    # Now split the data in this column
                    # We need to coerce to string first
                    split_data = df[col].astype(str).str.split('|', expand=True)
                    
                    # Assign headers if count matches
                    if split_data.shape[1] == len(headers):
                        split_data.columns = headers
                    else:
                        # shape mismatch, just use generic names or try best effort
                        # Usually it matches if just a delimiter issue
                        split_data.columns = headers[:split_data.shape[1]]
                        
                    clean_dfs.append(split_data)
                else:
                    # Keep valid columns as is
                    clean_dfs.append(df[[col]])
            
            # Reassemble
            df = pd.concat(clean_dfs, axis=1)
            
        # Ensure DownloadDate is datetime for filtering
        if 'DownloadDate' in df.columns:
            df['DownloadDate'] = pd.to_datetime(df['DownloadDate']).dt.date

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
    date_filter = request.args.get('DATE', '').strip()

    filtered_df = df.copy()
    
    # 1. Filter by SC_CODE
    if sc_code_filter and 'SC_CODE' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['SC_CODE'].astype(str).str.contains(sc_code_filter, case=False, na=False)]
    
    # 2. Filter by DATE
    if date_filter and 'DownloadDate' in filtered_df.columns:
        # date_filter format YYYY-MM-DD from HTML input type=date
        try:
            # Check for exact string match or convert. Data is object(date).
            filtered_df = filtered_df[filtered_df['DownloadDate'].astype(str) == date_filter]
        except:
            pass

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
        sc_code_filter=sc_code_filter,
        date_filter=date_filter
    )

if __name__ == '__main__':
    app.run(debug=True)
