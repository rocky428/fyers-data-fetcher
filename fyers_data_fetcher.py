import json
import logging.config
import numpy as np
import pandas as pd
import logging
import datetime as dt
import os
from fyers_apiv3 import fyersModel
import authentication_handler as auth_hand

API_CRED_FNAME = "api_cred.json"
DATA_PARAMETERS_FNAME = "data_parameters.json"
ACCESS_TOKEN_FNAME = "access_token.txt"

# Data retrieval limits for Fyers API
DATA_LIMIT_DAYS = {"1": 100, "5": 100, "15": 100, "30": 100, "45": 100, "60": 100, "D": 365}

# Paths to save fetched data
SAVE_TO_FOLDER = "downloaded_data"

os.makedirs(SAVE_TO_FOLDER, exist_ok=True)

# Configure logging
logging.config.fileConfig("log.conf")
logger_main = logging.getLogger("main")

def read_json_file(filename: str) -> dict:
    """Read API Crendentials from JSON file.

    Args:
        filename (str): Name of the JSON file containing the API credentials.
    
    Returns:
        dict: A dictionary of API credentials for Fyers.
    """
    try:
        with open(filename, "r") as f:
            credentials = json.load(f)
        logging.info(f"Successfully read {filename}.")
        return credentials
    except Exception as e:
        logging.info(f"Error reading {filename}: {e}")
        raise

def read_data_parameters_file(filename: str) -> dict:
    """Read the paarameters (scrip name, resolution, start date, and end date) required to fetch the historical data from JSON file.
    
    Args:
        filename (str): Name of the JSON file containing the data fetching parameters.
        
    Returns:
        dict: A dictionary of data fetching parameters.
    """
    try:
        with open(filename, "r") as f:
            data_parameters = json.load(f)
        logger_main.info(f"Successfully read {filename}.")
        return data_parameters
    except Exception as e:
        logger_main.info(f"Error reading {filename}: {e}")
        raise

def read_access_token(filename: str) -> str:
    """Read access token from a file.
    
    Args:
        filename (str): Name of the file where the access token is saved.
    
    Returns:
        str: The access token.
    """
    try:
        with open(filename, "r") as f:
            access_token = f.read().strip()
        logger_main.info(f"Successfully read access token from: {filename}.")
        return access_token
    except Exception as e:
        logger_main.error(f"Access token file {filename} missing: {e}")
        raise

def write_access_token(access_token: str, filename: str) -> None:
    """Write access token to a file.
    
    Args:
        access_token (str): The access token to be written to the file.
        filename (str): The filename to write the access token to.
    
    Returns:
        None.
    """
    try:
        with open(filename, "w") as f:
            f.write(access_token)
        logger_main.info(f"Access token written to file: {filename}")
    except Exception as e:
        logger_main.error(f"Error writing access token to file: {e}")
        raise

def get_authentication_link(credentials: dict) -> str:
    """Generate Authentication link.
    
    Args:
        credentials (dict): Dictionary of API credentials.
    
    Returns:
        str: The link which is to be used for Authentication.
    """
    try:
        session = fyersModel.SessionModel(
            client_id=credentials["ClientID"],
            secret_key=credentials["SecretID"],
            redirect_uri=credentials["RedirectURI"],
            response_type=credentials["ResponseType"]
        )
        auth_link = session.generate_authcode()
        logger_main.info(f"Successfully generated Authentication link.")
        return auth_link
    except Exception as e:
        logger_main.error(f"Error generating Authentication link: {e}")
        raise

def extract_auth_code(uri: str) -> str:
    """Extract authentication code from URI.
    
    Args:
        uri (str): The redirected uri after the authentication is done by user on webpage.
    
    Returns:
        str: The extracted auth code from the uri.
    """
    try:
        auth_code = uri.split("auth_code=")[1].split("&")[0]
        logger_main.info(f"Successfully extracted the auth code.")
        return auth_code
    except Exception as e:
        logger_main.error(f"Error extracting auth code: {e}")
        raise

def generate_access_token(credentials: dict, auth_code: str) -> str:
    """Generate access token using auth code.
    
    Args:
        credentials (dict): Dictionary of API credentials.
        auth_code (str): The authentication code to generate the access token.
    
    Returns:
        str: The generated access token.
    """
    try:
        session = fyersModel.SessionModel(
            client_id=credentials["ClientID"],
            secret_key=credentials["SecretID"],
            redirect_uri=credentials["RedirectURI"],
            response_type=credentials["ResponseType"],
            grant_type=credentials["GrantType"]
        )
        session.set_token(auth_code)
        access_token =  session.generate_token()["access_token"]
        logger_main.info(f"Successfully generated access token.")
        return access_token
    except Exception as e:
        logger_main.error(f"Error generating access token: {e}")
        raise

def create_fyers_session(credentials: dict, access_token: str) -> fyersModel.FyersModel:
    """Create an authenticated session with Fyers API.
    
    Args:
        credentials (dict): Dictionary of API credentials.
        access_token (str): The generated access token.
    
    Returns:
        fyersModel.FyersModel: A Fyers API session which can be used to fetch data or other supported API calls.
    """
    try:
        return fyersModel.FyersModel(client_id = credentials["ClientID"], is_async = False, token = access_token, log_path = "")
    except Exception as e:
        logger_main.error(f"Error creating session: {e}")
        raise

def format_historical_prices(candle_data: np.ndarray) -> pd.DataFrame:
    """Format historical prices into a DataFrame.
    
    Args:
        candle_data (np.ndarray): The OHLC data of shape (N,5), where N is the size of the time-series.
    
    Returns:
        pd.DataFrame: The numpy array formatted and returned as a dataframe.
    """
    df = pd.DataFrame(candle_data, columns=["date_time", "open", "high", "low", "close", "volume"])
    df["date_time"] = pd.to_datetime(df["date_time"], unit="s")
    df["date_time"] = df["date_time"].dt.tz_localize('utc').dt.tz_convert('Asia/Kolkata')
    df["date_time"] = df["date_time"].dt.tz_localize(None)
    df["date_time"] = df["date_time"].dt.floor("min")
    df["volume"] = df["volume"].astype(int)
    return df

def get_date_ranges(start_date: str, end_date: str, resolution: str) -> list:
    """Split date range into chunks based on API limits.
    
    Args:
        start_date (str): The start date for fetching the historical data in the format dd-mm-YYYY.
        end_date (str): The end date for fetching the historical data in the format dd-mm-YYYY.
        resolution (str): The resolution of the data to be fetched ex "D" for 1-day, "1" for 1-min etc.
    
    Returns:
        List[Tuple[datetime, datetime]]: A list of tuples which includes start date and end date for each chunk.
    """
    start_dt = dt.datetime.strptime(start_date, "%d-%m-%Y").date()
    end_dt = dt.datetime.strptime(end_date, "%d-%m-%Y").date()
    delta = dt.timedelta(days=DATA_LIMIT_DAYS.get(resolution, 100))
    date_ranges = []
    while start_dt < end_dt:
        next_dt = min(start_dt + delta, end_dt)
        date_ranges.append((start_dt.strftime("%Y-%m-%d"), next_dt.strftime("%Y-%m-%d")))
        start_dt = next_dt + dt.timedelta(days=1)
    return date_ranges

def fetch_historical_data(session: fyersModel.FyersModel, symbol: str, resolution: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch historical market data from Fyers API.
    
    Args:
        session (fyersModel.FyersModel): An API access authenticated FyersModel.
        symbol (str): The symbol for which the historical data is to be fetched.
        resolution (str): The resolution of the data to be fetched ex "D" for 1-day, "1" for 1-min etc.
        start_date (str): The start date for fetching the historical data in the format dd-mm-YYYY.
        end_date (str): The end date for fetching the historical data in the format dd-mm-YYYY.

    Returns:
        pd.DataFrame: A dataframe of OHLC data of the requested symbol, at the requested resolution for the period requested. 
    """
    date_ranges = get_date_ranges(start_date, end_date, resolution)
    all_data = []
    try:
        for start, end in date_ranges:
            response = session.history({"symbol": symbol, "resolution": resolution, "date_format": "1", "range_from": start, "range_to": end})
            if response["candles"]:
                all_data.append(np.array(response["candles"]))
                logger_main.info(f"Fetched data: {start} to {end}")
            else:
                raise Exception(f"Data not available for {start} to {end}")
        return format_historical_prices(np.vstack(all_data)) if all_data else pd.DataFrame()
    except Exception as e:
        logger_main.error(f"Error fetching historical data: {e}")
        raise

def save_data_to_csv(df: pd.DataFrame, filename: str) -> None:
    """Save DataFrame to CSV.

    Args:
        df (pd.DataFrame): The dataframe to be saved.
    
    Returns:
        None
    """
    try:
        df.to_csv(os.path.join(SAVE_TO_FOLDER, filename), index=False)
        logger_main.info(f"Data saved: {os.path.join(SAVE_TO_FOLDER, filename)}")
    except Exception as e:
        logger_main.error(f"Error saving data: {e}")
        raise

def main():
    """The main method which is used to fetch the historical data."""
    credentials = read_json_file(API_CRED_FNAME)
    data_parameters = read_data_parameters_file(DATA_PARAMETERS_FNAME)
    response = input("Do you have an access token? (y/n): ")
    if response == "y":
        access_token = read_access_token(ACCESS_TOKEN_FNAME)
    else:
        auth_link = get_authentication_link(credentials)
        logger_main.info(f"Open the following link in your browser and authenticate: {auth_link}")
        port = int(credentials["RedirectURI"].split(":")[-1])
        auth_code = auth_hand.run_local_server(port) # start a local server and keep listening for redirection
        access_token = generate_access_token(credentials, auth_code)
        write_access_token(access_token, ACCESS_TOKEN_FNAME)
    session = create_fyers_session(credentials, access_token)
    df = fetch_historical_data(session, data_parameters["ScriptName"], data_parameters["Resolution"], data_parameters["StartDate"], data_parameters["EndDate"])
    if not df.empty:
        filename = f"{data_parameters['ScriptName'].split(':')[1]}_{data_parameters['Resolution']}_{data_parameters['StartDate']}_to_{data_parameters['EndDate']}.csv"
        save_data_to_csv(df, filename)
    else:
        logger_main.warning("No data retrieved.")

if __name__ == "__main__":
    main()
