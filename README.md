# Historical Market Data Fetcher using Fyers API

## Overview
This script fetches historical market data from the Fyers API using user-provided API credentials, access tokens, and data parameters. The data is retrieved in OHLC format and saved as a CSV file for further analysis.

## Features
- Reads API credentials from a JSON file
- Authenticates with the Fyers API and generates an access token
- Fetches historical data based on user-specified parameters
- Handles API limits by breaking requests into manageable date ranges
- Saves fetched data as a CSV file

## Prerequisites
Before running the script, ensure you have the following:
- Python 3.x installed
- Required dependencies installed (see Installation section)
- A valid Fyers API account with API credentials

## Installation

1. Clone the repository or download the script.
2. Navigate to the cloned respository using:
   ```sh
   cd fyers-data-fetcher
   ```
3. Create a virtual environment and activate it using:
   ```sh
   python3 -m venv .fyers_venv
   source .fyers_venv/bin/activate
   ```
5. Now install the required dependencies in the created **fyers_venv** using pip:
    ```sh
    pip install numpy pandas fyers-apiv3
    ```
6. Create the following necessary files in the project directory:
    - `api_cred.json` (containing API credentials)
    - `data_parameters.json` (containing historical data fetch parameters)
    - `access_token.txt` (optional, stores the access token)

## Configuration
### `api_cred.json`
This file should store your Fyers API credentials in the following format:
```json
{
    "ClientID": "your_app_id",
    "SecretID": "your_secret_id",
    "RedirectURI": "your_redirect_uri",
    "ResponseType": "code",
    "State":"fyers",
    "GrantType": "authorization_code"
}
```

### `data_parameters.json`
Specify the market data request parameters:
```json
{
    "ScriptName": "NSE:RELIANCE-EQ",
    "Resolution": "D",
    "StartDate": "01-01-2023",
    "EndDate": "31-12-2023"
}
```

## Usage

1. Run the script:
    ```sh
    python ./fyers_data_fetcher.py
    ```
2. If you have an access token, enter 'y' when prompted, otherwise enter 'n'.
3. If authentication is required, follow the on-screen instructions to generate an authentication link, authorize it in a browser, and provide the redirected URI.
4. The script will fetch the requested historical data and save it as a CSV file in the `downloaded_data` folder.

## Output
The script will generate a CSV file in the format:
```
{Symbol}_{Resolution}_{StartDate}_to_{EndDate}.csv
```
For example:
```
RELIANCE_EQ_D_01-01-2023_to_31-12-2023.csv
```

## Logging
The script logs important steps and errors in the console for easy debugging. The Fyers API also creates log files.

## License
This project is licensed under the MIT License.

## Author
Developed by Brian Pinto
