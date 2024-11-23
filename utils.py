import os
import json
import logging
import pandas as pd
import unicodedata
import pulp

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

# Base directory for user-specific data
USER_DATA_DIR = "./data/users"

def get_user_file_path(username, file_name):
    """
    Generate a file path for the given user's file.
    :param username: The logged-in username
    :param file_name: "exclusion.txt" or "must_include.txt"
    :return: Full file path as a string
    """
    # Create a directory for the user if it doesn't exist
    user_dir = os.path.join(USER_DATA_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    # Return the file path within the user's directory
    return os.path.join(user_dir, file_name)


def normalize_string(s):
    """
    Normalize and standardize strings for consistent comparison.
    
    Args:
        s (str): Input string to normalize
    
    Returns:
        str: Normalized lowercase string
    """
    if not isinstance(s, str):
        return s
    
    # Normalize Unicode, remove non-breaking spaces, strip whitespace, convert to lowercase
    return (unicodedata.normalize('NFC', str(s))
            .replace('\u00A0', ' ')
            .strip()
            .lower())

def read_list_from_file(filename):
    """
    Read a list from a file, handling different potential formats.
    
    Args:
        filename (str): Path to the file to read
    
    Returns:
        list: List of items read from the file
    """
    try:
        if not os.path.exists(filename):
            logging.warning(f"File not found: {filename}")
            return []

        with open(filename, 'r', encoding='utf-8') as file:
            # Skip comment lines and empty lines
            lines = [
                line.strip() for line in file 
                if line.strip() and not line.strip().startswith('#')
            ]
            
            # Normalize each line
            return [normalize_string(line) for line in lines]
    
    except Exception as e:
        logging.error(f"Error reading file {filename}: {e}")
        return []

def write_to_list_file(filename, item):
    """
    Add an item to a list file, avoiding duplicates.
    
    Args:
        filename (str): Path to the file
        item (str): Item to add to the list
    """
    try:
        # Read existing items
        existing_items = read_list_from_file(filename)
        
        # Normalize the new item
        normalized_item = normalize_string(item)
        
        # Check for duplicates
        if normalized_item not in existing_items:
            with open(filename, 'a', encoding='utf-8') as file:
                file.write(f"{item}\n")
            logging.info(f"Added {item} to {filename}")
        else:
            logging.warning(f"{item} already exists in {filename}")
    
    except Exception as e:
        logging.error(f"Error writing to {filename}: {e}")

def remove_from_list_file(filename, item):
    """
    Remove an item from a list file.
    
    Args:
        filename (str): Path to the file
        item (str): Item to remove from the list
    """
    try:
        # Read existing items
        existing_items = read_list_from_file(filename)
        
        # Normalize the item to remove
        normalized_item = normalize_string(item)
        
        # Filter out the item
        updated_items = [
            existing for existing in existing_items 
            if normalize_string(existing) != normalized_item
        ]
        
        # Write back to file
        with open(filename, 'w', encoding='utf-8') as file:
            for updated_item in updated_items:
                file.write(f"{updated_item}\n")
        
        logging.info(f"Removed {item} from {filename}")
    
    except Exception as e:
        logging.error(f"Error removing from {filename}: {e}")

def load_player_data(config):
    """
    Load player data from Excel files.
    
    Args:
        config (dict): Configuration dictionary with file paths
    
    Returns:
        tuple: DataFrames for skaters and goalies
    """
    try:
        # Load skaters and goalies data
        skaters_data = pd.read_excel(config['SKATERS_FILE'], sheet_name='Skaters', header=0)
        goalies_data = pd.read_excel(config['GOALIES_FILE'], sheet_name='Goalies', header=0)
        
        # Normalize player names
        skaters_data['PlayerName_normalized'] = skaters_data['PlayerName'].apply(normalize_string)
        goalies_data['PlayerName_normalized'] = goalies_data['PlayerName'].apply(normalize_string)
        
        return skaters_data, goalies_data
    
    except Exception as e:
        logging.error(f"Error loading player data: {e}")
        raise

def perform_player_search(keyword, list_type=None):
    """
    Perform a search across player databases.
    
    Args:
        keyword (str): Search term
        list_type (str, optional): List type to filter
    
    Returns:
        list: List of matching players
    """
    try:
        # Load player data
        skaters_data, goalies_data = load_player_data(current_app.config)
        
        # Combine datasets
        all_players = pd.concat([skaters_data, goalies_data], ignore_index=True)
        
        # Normalize keyword
        normalized_keyword = normalize_string(keyword)
        
        # Filter players
        filtered_players = all_players[
            all_players['PlayerName_normalized'].str.contains(normalized_keyword, case=False)
        ]
        
        # Convert to list of dictionaries for easy JSON serialization
        results = filtered_players.to_dict('records')
        
        return results
    
    except Exception as e:
        logging.error(f"Search error: {e}")
        return []

def optimize_nhl_pool(config):
    """
    Optimize NHL pool selection based on predefined constraints.
    
    Args:
        config (dict): Configuration dictionary
    
    Returns:
        tuple: Total score, total salary, and selected players
    """
    try:
        # Load player data and lists
        skaters_data, goalies_data = load_player_data(config)
        exclusion_list = read_list_from_file(config['EXCLUSION_FILE'])
        must_include_list = read_list_from_file(config['MUST_INCLUDE_FILE'])
        
        # Optimization logic (similar to previous implementation)
        # ... (implement the full optimization logic here)
        
        total_score = 0
        total_salary = 0
        selected_players = []
        
        return total_score, total_salary, selected_players
    
    except Exception as e:
        logging.error(f"Optimization error: {e}")
        raise

# Utility function for converting columns to numeric
def convert_to_numeric(df, columns):
    """
    Convert specified columns to numeric, handling various formats.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        columns (list): Columns to convert
    
    Returns:
        pd.DataFrame: DataFrame with converted columns
    """
    for col in columns:
        df[col] = (df[col].astype(str)
                   .str.replace('[$,]', '', regex=True)
                   .str.replace(',', ''))
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df
