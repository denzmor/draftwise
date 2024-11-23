

from flask import Flask, render_template, request, redirect, url_for, flash, current_app, session
import pandas as pd
import unicodedata
import os
from optimization import optimize_nhl_pool  # Import the optimization function
from config import Config
from utils import read_list_from_file, remove_from_list_file  # Import the necessary functions
from utils import get_user_file_path



app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = 'alla8002'  # Replace with a secure random key for production

# Load credentials from a .txt file
CREDENTIALS_FILE = './data/credentials.txt'

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as file:
            credentials = {}
            for line in file:
                username, password = line.strip().split(':')
                credentials[username] = password
            return credentials
    return {}

credentials = load_credentials()

# Middleware to protect routes
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in credentials and credentials[username] == password:
            session['username'] = username
            flash("You have successfully logged in.", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "danger")
    else:
        # Clear any flash messages carried over
        session.pop('_flashes', None)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# Function to normalize and standardize strings
def normalize_string(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFC', s).replace('\u00A0', ' ').strip().lower()
    return s

# Load player data from the Excel file
def load_player_data():
    # Load the data from the Excel file
    skaters_data = pd.read_excel('data/players-2024.xlsx', sheet_name='Skaters')
    goalies_data = pd.read_excel('data/players-2024.xlsx', sheet_name='Goalies')

    # Assign column names based on your data
    skaters_columns = ['Index', 'PlayerName', 'Blank', 'Age', 'Pos', 'Shot', 'W(lbs)', 'H(f)',
                       'UFA Year', 'Draft Year', 'Draft Position', 'Agent', 'Status', 'Length',
                       'Level', 'Cap Hit', 'AAV', 'Base Salary', 'Signing Bonus', 'Performance Bonus',
                       'Total Salary', 'Minor Salary', 'Structure', 'Clauses', 'Start Year',
                       'Signing Age', 'Signing Status', 'Expiry Year', 'Expiry Status',
                       'Signing Agent', 'GP', 'G', 'A', 'P', 'PPG', 'GPG', 'TOI 5x5',
                       'TOI 5x5/G', '+/-', 'PIM', 'GF%', 'DFF%', 'relDFF%', 'CF%',
                       'relCF%', 'G60', 'P60']

    goalies_columns = ['Index', 'PlayerName', 'Blank', 'Age', 'Pos', 'Shot', 'W(lbs)', 'H(f)',
                       'UFA Year', 'Draft Year', 'Draft Position', 'Agent', 'Status', 'Length',
                       'Level', 'Cap Hit', 'AAV', 'Base Salary', 'Signing Bonus', 'Performance Bonus',
                       'Total Salary', 'Minor Salary', 'Structure', 'Clauses', 'Start Year',
                       'Signing Age', 'Signing Status', 'Expiry Year', 'Expiry Status',
                       'Signing Agent', 'GP', 'SV%', 'GAA', 'SA', 'GA', 'SO', 'W', 'L', 'TOI']

    # Assign the column names
    skaters_data.columns = skaters_columns
    goalies_data.columns = goalies_columns

    # Drop unnecessary columns
    skaters_data = skaters_data.drop(columns=['Blank'], errors='ignore')
    goalies_data = goalies_data.drop(columns=['Blank'], errors='ignore')

    # Fill NaN in 'Pos' column
    skaters_data['Pos'] = skaters_data['Pos'].fillna('')
    goalies_data['Pos'] = goalies_data['Pos'].fillna('')

    # Normalize player names
    skaters_data['PlayerName_normalized'] = skaters_data['PlayerName'].apply(normalize_string)
    goalies_data['PlayerName_normalized'] = goalies_data['PlayerName'].apply(normalize_string)

    return pd.concat([skaters_data, goalies_data], ignore_index=True)

# Load player data when the application starts
player_data = load_player_data()

from flask import render_template, redirect, url_for, flash

@app.route('/list_exclusions', methods=['GET'])
@login_required
def list_exclusions():
    username = session['username']  # Get the logged-in username
    exclusion_file = get_user_file_path(username, "exclusion.txt")

    if os.path.exists(exclusion_file):
        with open(exclusion_file, 'r') as f:
            exclusion_list = f.read().splitlines()
    else:
        exclusion_list = []

    return render_template('list_exclusions.html', exclusion_list=exclusion_list)

@app.route('/list_must_include', methods=['GET'])
@login_required
def list_must_include():
    username = session['username']  # Get the logged-in username
    must_include_file = get_user_file_path(username, "must_include.txt")

    # Read the must_include file for the user
    if os.path.exists(must_include_file):
        with open(must_include_file, 'r') as f:
            must_include_list = f.read().splitlines()
    else:
        must_include_list = []  # Return an empty list if the file doesn't exist

    return render_template('list_must_include.html', must_include_list=must_include_list)

@app.route('/remove_exclusion', methods=['POST'])
@login_required
def remove_exclusion():
    username = session['username']  # Get the logged-in username
    exclusion_file = get_user_file_path(username, "exclusion.txt")
    player_name = request.form.get('player')

    # Remove the player from the exclusion file
    if os.path.exists(exclusion_file):
        with open(exclusion_file, 'r') as f:
            lines = f.readlines()
        with open(exclusion_file, 'w') as f:
            for line in lines:
                if line.strip() != player_name.strip():
                    f.write(line)

    flash(f'Removed {player_name} from exclusion list', 'success')
    return redirect(url_for('list_exclusions'))

@app.route('/remove_must_include', methods=['POST'])
@login_required
def remove_must_include():
    username = session['username']  # Get the logged-in username
    must_include_file = get_user_file_path(username, "must_include.txt")
    player_name = request.form.get('player')

    # Remove the player from the must_include file
    if os.path.exists(must_include_file):
        with open(must_include_file, 'r') as f:
            lines = f.readlines()
        with open(must_include_file, 'w') as f:
            for line in lines:
                if line.strip() != player_name.strip():
                    f.write(line)

    flash(f'Removed {player_name} from must include list', 'success')
    return redirect(url_for('list_must_include'))


@app.route('/')
@login_required
def index():
    return render_template('index.html', total_salary=None, total_score=None,
                           selected_attackers=None, selected_defensemen=None,
                           selected_goalies=None)


#@app.route('/optimize', methods=['POST'])
#def optimize():
#    selected_attackers, selected_defensemen, selected_goalies, total_salary, total_score = optimize_nhl_pool()

    # Check if any of the returned values are None
#    if selected_attackers is None or selected_defensemen is None or selected_goalies is None:
#        return render_template('index.html', total_salary=None, total_score=None,
#                               selected_attackers=None, selected_defensemen=None,
#                               selected_goalies=None, error="Optimization failed or salary cap exceeded.")

    # Render the optimization results in a new template
#    return render_template('optimization_results.html',
#                           total_salary=total_salary,
#                           total_score=total_score,
#                           selected_attackers=selected_attackers.to_dict(orient='records'),
#                           selected_defensemen=selected_defensemen.to_dict(orient='records'),
#                           selected_goalies=selected_goalies.to_dict(orient='records'))

@app.route('/optimize', methods=['POST'])
@login_required
def optimize():
    username = session['username']  # Get the logged-in username

    # Generate user-specific file paths
    exclusion_file = get_user_file_path(username, "exclusion.txt")
    must_include_file = get_user_file_path(username, "must_include.txt")

    # Call the optimization function with user-specific files
    selected_attackers, selected_defensemen, selected_goalies, total_salary, total_score = optimize_nhl_pool(
        exclusion_file=exclusion_file,
        must_include_file=must_include_file
    )

    if selected_attackers is None or selected_defensemen is None or selected_goalies is None:
        return render_template('index.html', total_salary=None, total_score=None,
                               selected_attackers=None, selected_defensemen=None,
                               selected_goalies=None, error="Optimization failed or salary cap exceeded.")

    return render_template('index.html',
                           total_salary=total_salary,
                           total_score=total_score,
                           selected_attackers=selected_attackers.to_dict(orient='records'),
                           selected_defensemen=selected_defensemen.to_dict(orient='records'),
                           selected_goalies=selected_goalies.to_dict(orient='records'))


@app.route('/search', methods=['POST'])
@login_required
def search():
    # Handle GET request to display the search form
    keyword = request.form.get('keyword')
    results = perform_player_search(keyword)

    return render_template('search_results.html', results=results)

def perform_player_search(keyword):
    # Normalize the keyword for searching
    keyword = normalize_string(keyword)

    # Drop NaN values from PlayerName_normalized
    filtered_players = player_data.dropna(subset=['PlayerName_normalized'])

    # Filter players based on the keyword
    filtered_players = filtered_players[filtered_players['PlayerName_normalized'].str.contains(keyword, case=False, na=False)]

    return filtered_players.to_dict(orient='records')

def reformat_player_name(player_name):
    # Replace non-breaking spaces with regular spaces and strip surrounding whitespace
    player_name = player_name.replace("\u00A0", " ").strip()
    # Reformat "LastName, FirstName" to "FirstName LastName"
    parts = player_name.split(", ")
    if len(parts) == 2:
        return f"{parts[1]} {parts[0]}"  # Swap and remove the comma
    return player_name  # Return original name if not in expected format

@app.route('/check_player/<player_name>', methods=['GET', 'POST'])
@login_required
def check_player(player_name):
    username = session['username']  # Get the logged-in username
    exclusion_file = get_user_file_path(username, "exclusion.txt")
    must_include_file = get_user_file_path(username, "must_include.txt")

    player_name_normalized = normalize_string(player_name)

    # Check if the player is in exclusion.txt or must_include.txt
    in_exclusion = False
    in_must_include = False

    if os.path.exists(exclusion_file):
        with open(exclusion_file, 'r') as f:
            exclusions = f.read().splitlines()
            in_exclusion = player_name_normalized in [normalize_string(name) for name in exclusions]

    if os.path.exists(must_include_file):
        with open(must_include_file, 'r') as f:
            must_includes = f.read().splitlines()
            in_must_include = player_name_normalized in [normalize_string(name) for name in must_includes]

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'remove_exclusion' and in_exclusion:
            # Remove from exclusion.txt
            with open(exclusion_file, 'r') as f:
                lines = f.readlines()
            with open(exclusion_file, 'w') as f:
                for line in lines:
                    if normalize_string(line.strip()) != player_name_normalized:
                        f.write(line)
            return render_template('message.html', message=f"{player_name} has been removed from exclusion.")

        if action == 'remove_must_include' and in_must_include:
            # Remove from must_include.txt
            with open(must_include_file, 'r') as f:
                lines = f.readlines()
            with open(must_include_file, 'w') as f:
                for line in lines:
                    if normalize_string(line.strip()) != player_name_normalized:
                        f.write(line)
            return render_template('message.html', message=f"{player_name} has been removed from must include.")

        if action == 'add_exclusion':
            with open(exclusion_file, 'a') as f:
                f.write(player_name + '\n')
            return render_template('message.html', message=f"{player_name} has been added to exclusion.")

        if action == 'add_must_include':
            with open(must_include_file, 'a') as f:
                f.write(player_name + '\n')
            return render_template('message.html', message=f"{player_name} has been added to must include.")

        return redirect(url_for('search'))


    # Reformat player name specifically for the connector
    player_name_for_connector = reformat_player_name(player_name)
    print(f"Original player_name: {player_name}")
    print(f"Normalized player_name: {player_name.replace('\u00A0', ' ').strip()}")
    print(f"Reformatted player_name_for_connector: {player_name_for_connector}")

    return render_template('check_player.html',
                           player_name=player_name,
                           player_name_for_connector=player_name_for_connector,  # Pass reformatted name only for connector
                           in_exclusion=in_exclusion,
                           in_must_include=in_must_include)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
