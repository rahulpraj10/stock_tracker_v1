# Stock Data Downloader

This project automates the daily downloading of BSE Bhavdata (stock market data) and accumulates it into a single Pickle file (`StockData.pkl`).

## Features
- **Daily Download**: Automatically downloads the daily Bhavdata zip file from BSE.
- **Accumulation**: Appends new data to `StockData.pkl` to build a historical dataset.
- **Automation**: Runs every weekday at 9:00 PM IST using GitHub Actions.

## Setup
1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run locally:
    ```bash
    python download_bhavdata.py
    ```
3.  Run the Web Viewer:
    ```bash
    python flask_app.py
    ```
    Then open `http://localhost:5000` in your browser.

## GitHub Actions
The workflow is defined in `.github/workflows/daily_download.yml`. It runs automatically on the specified schedule.
