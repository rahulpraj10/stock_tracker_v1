import os
import requests
import zipfile
import io
import pandas as pd
from datetime import datetime

def download_and_process_bhavdata():
    # 1. Get current date details
    now = datetime.now()
    yyyy = now.strftime("%Y")
    ddmm = now.strftime("%d%m")
    # Hardcoded for testing
    # yyyy = "2026"
    # ddmm = "0302"
    # 2. Construct the URL
    # URL format: https://www.bseindia.com/BSEDATA/gross/YYYY/SCBSEALLDDMM.zip
    url = f"https://www.bseindia.com/BSEDATA/gross/{yyyy}/SCBSEALL{ddmm}.zip"
    print(f"Target URL: {url}")
    
    # 3. Create Bhavdata directory if it doesn't exist
    output_dir = "Bhavdata"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    else:
        print(f"Directory already exists: {output_dir}")
        
    try:
        # 4. Download the ZIP file
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print("Downloading file...")
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        
        # 5. Extract the ZIP file
        print("Extracting zip file...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(output_dir)
            extracted_files = z.namelist()
            print(f"Extracted files: {extracted_files}")
            
            # 6. Convert details into a pkl file
            final_pkl_path = os.path.join(output_dir, "StockData.pkl")
            
            for file_name in extracted_files:
                if file_name.lower().endswith('.csv') or file_name.lower().endswith('.txt'):
                    file_path = os.path.join(output_dir, file_name)
                    print(f"Processing {file_path} for accumulation...")
                    
                    try:
                        # BSE data is often pipe delimited
                        new_df = pd.read_csv(file_path, sep='|')
                        # Add download date column
                        new_df['DownloadDate'] = now.date()
                    except Exception as e:
                        print(f"Error reading CSV {file_path}: {e}")
                        continue

                    # Accumulate logic
                    if os.path.exists(final_pkl_path):
                        print(f"Found existing {final_pkl_path}, appending data...")
                        try:
                            # Use pandas read_pickle
                            existing_df = pd.read_pickle(final_pkl_path)
                            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                            combined_df.to_pickle(final_pkl_path)
                            print(f"Appended data to {final_pkl_path}. New size: {len(combined_df)} rows.")
                        except Exception as e:
                            print(f"Error reading/writing existing PKL: {e}")
                            print("Saving as new file (overwrite safe fallback)...")
                            new_df.to_pickle(final_pkl_path)
                    else:
                        print(f"Creating new {final_pkl_path}...")
                        new_df.to_pickle(final_pkl_path)
                    
                    # Optional: Delete extracted CSV to keep folder clean?
                    # os.remove(file_path)

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}")
        print("This may happen if the file for the current date does not exist (e.g., weekend or holiday).")
    except Exception as e:
        print(f"An error occurred: {e}")

    # 7. Print contents of the final PKL file
    target_pkl = os.path.join(output_dir, "StockData.pkl")
    if os.path.exists(target_pkl):
        print("\n" + "="*50)
        print(f"Contents of {target_pkl}:")
        try:
            final_df = pd.read_pickle(target_pkl)
            print(f"Total Rows: {len(final_df)}")
            print("\nFirst 5 rows:")
            print(final_df.head())
            print("\nLast 5 rows:")
            print(final_df.tail())
            print("="*50 + "\n")
        except Exception as e:
            print(f"Error reading final PKL for specific display: {e}")


if __name__ == "__main__":
    download_and_process_bhavdata()
