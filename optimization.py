import os
import pandas as pd
import unicodedata
import pulp


def normalize_string(s):
    """
    Normalize and standardize strings.
    """
    if isinstance(s, str):
        s = unicodedata.normalize('NFC', s).replace('\u00A0', ' ').strip().lower()
        return s
    return s


def read_list_from_file(filename):
    """
    Read a list of items from a file, ignoring lines that are empty or start with '#'.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines()]
            return [line for line in lines if line and not line.startswith('#')]
    except FileNotFoundError:
        return []


def convert_to_numeric(df, columns):
    """
    Convert specified DataFrame columns to numeric, handling missing or invalid values.
    """
    for col in columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace('[$,]', '', regex=True)
            .str.replace(',', '')
        )
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df


def optimize_nhl_pool(exclusion_file=None, must_include_file=None):
    """
    Perform optimization using user-specific exclusion and must_include files.
    :param exclusion_file: Path to the user's exclusion.txt
    :param must_include_file: Path to the user's must_include.txt
    :return: Selected attackers, defensemen, goalies, total_salary, total_score
    """
    # Ensure exclusion and must_include files exist
    for file_path in [exclusion_file, must_include_file]:
        if file_path and not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                pass  # Create an empty file if it doesn't exist

    # Load exclusion and must_include lists
    exclusion_list = read_list_from_file(exclusion_file) if exclusion_file else []
    must_include_list = read_list_from_file(must_include_file) if must_include_file else []

    # Load player data
    skaters_data = pd.read_excel('./data/players-2024.xlsx', sheet_name='Skaters', header=0)
    goalies_data = pd.read_excel('./data/players-2024.xlsx', sheet_name='Goalies', header=0)

    # Normalize exclusion and must_include lists
    exclusion_list_normalized = [normalize_string(name) for name in exclusion_list]
    must_include_list_normalized = [normalize_string(name) for name in must_include_list]

    # Define column names
    skaters_columns = [
        'Index', 'PlayerName', 'Blank', 'Age', 'Pos', 'Shot', 'W(lbs)', 'H(f)',
        'UFA Year', 'Draft Year', 'Draft Position', 'Agent', 'Status', 'Length',
        'Level', 'Cap Hit', 'AAV', 'Base Salary', 'Signing Bonus', 'Performance Bonus',
        'Total Salary', 'Minor Salary', 'Structure', 'Clauses', 'Start Year',
        'Signing Age', 'Signing Status', 'Expiry Year', 'Expiry Status',
        'Signing Agent', 'GP', 'G', 'A', 'P', 'PPG', 'GPG', 'TOI 5x5',
        'TOI 5x5/G', '+/-', 'PIM', 'GF%', 'DFF%', 'relDFF%', 'CF%',
        'relCF%', 'G60', 'P60'
    ]

    goalies_columns = [
        'Index', 'PlayerName', 'Blank', 'Age', 'Pos', 'Shot', 'W(lbs)', 'H(f)',
        'UFA Year', 'Draft Year', 'Draft Position', 'Agent', 'Status', 'Length',
        'Level', 'Cap Hit', 'AAV', 'Base Salary', 'Signing Bonus', 'Performance Bonus',
        'Total Salary', 'Minor Salary', 'Structure', 'Clauses', 'Start Year',
        'Signing Age', 'Signing Status', 'Expiry Year', 'Expiry Status',
        'Signing Agent', 'GP', 'SV%', 'GAA', 'SA', 'GA', 'SO', 'W', 'L', 'TOI'
    ]

    # Assign column names
    skaters_data.columns = skaters_columns
    goalies_data.columns = goalies_columns

    # Drop unnecessary columns
    skaters_data = skaters_data.drop(columns=['Blank'], errors='ignore')
    goalies_data = goalies_data.drop(columns=['Blank'], errors='ignore')

    # Normalize player names
    skaters_data['PlayerName_normalized'] = skaters_data['PlayerName'].apply(normalize_string)
    goalies_data['PlayerName_normalized'] = goalies_data['PlayerName'].apply(normalize_string)

    # Filter out excluded players
    skaters_data = skaters_data[~skaters_data['PlayerName_normalized'].isin(exclusion_list_normalized)]
    goalies_data = goalies_data[~goalies_data['PlayerName_normalized'].isin(exclusion_list_normalized)]

    # Convert columns to numeric
    skaters_data = convert_to_numeric(skaters_data, ['G', 'A', 'Total Salary'])
    goalies_data = convert_to_numeric(goalies_data, ['W', 'SO', 'Total Salary'])

    # Calculate scores
    skaters_data['Score'] = 0
    skaters_data.loc[skaters_data['Pos'].str.contains('D'), 'Score'] = (2 * skaters_data['G'] + skaters_data['A'])
    skaters_data.loc[skaters_data['Pos'].str.contains('C|L|R'), 'Score'] = (skaters_data['G'] + skaters_data['A'])
    goalies_data['Score'] = (goalies_data['SO'] * 3) + (goalies_data['W'] * 2)

    # Separate positions
    attackers = skaters_data[skaters_data['Pos'].str.contains('C|L|R')]
    defensemen = skaters_data[skaters_data['Pos'].str.contains('D')]

    # Must-include players
    attackers_must_include = attackers[attackers['PlayerName_normalized'].isin(must_include_list_normalized)]
    defensemen_must_include = defensemen[defensemen['PlayerName_normalized'].isin(must_include_list_normalized)]
    goalies_must_include = goalies_data[goalies_data['PlayerName_normalized'].isin(must_include_list_normalized)]

    # Remove must-includes from main data
    attackers = attackers[~attackers['PlayerName_normalized'].isin(must_include_list_normalized)]
    defensemen = defensemen[~defensemen['PlayerName_normalized'].isin(must_include_list_normalized)]
    goalies_data = goalies_data[~goalies_data['PlayerName_normalized'].isin(must_include_list_normalized)]

    # Reset indices
    attackers.reset_index(drop=True, inplace=True)
    defensemen.reset_index(drop=True, inplace=True)
    goalies_data.reset_index(drop=True, inplace=True)

    # Decision variables
    attackers_vars = {idx: pulp.LpVariable(f"attacker_{idx}", cat='Binary') for idx in attackers.index}
    defensemen_vars = {idx: pulp.LpVariable(f"defenseman_{idx}", cat='Binary') for idx in defensemen.index}
    goalies_vars = {idx: pulp.LpVariable(f"goalie_{idx}", cat='Binary') for idx in goalies_data.index}

    # ILP problem
    prob = pulp.LpProblem("NHL_Pool_Selection", pulp.LpMaximize)

    # Objective function
    prob += (
        pulp.lpSum([attackers.at[idx, 'Score'] * var for idx, var in attackers_vars.items()]) +
        pulp.lpSum([defensemen.at[idx, 'Score'] * var for idx, var in defensemen_vars.items()]) +
        pulp.lpSum([goalies_data.at[idx, 'Score'] * var for idx, var in goalies_vars.items()]) +
        attackers_must_include['Score'].sum() +
        defensemen_must_include['Score'].sum() +
        goalies_must_include['Score'].sum()
    ), "Total_Score"

    # Salary cap constraint
    prob += (
        pulp.lpSum([attackers.at[idx, 'Total Salary'] * var for idx, var in attackers_vars.items()]) +
        pulp.lpSum([defensemen.at[idx, 'Total Salary'] * var for idx, var in defensemen_vars.items()]) +
        pulp.lpSum([goalies_data.at[idx, 'Total Salary'] * var for idx, var in goalies_vars.items()]) +
        attackers_must_include['Total Salary'].sum() +
        defensemen_must_include['Total Salary'].sum() +
        goalies_must_include['Total Salary'].sum()
        <= 88_000_000
    ), "Total_Salary_Cap"

    # Position constraints
    prob += pulp.lpSum(attackers_vars.values()) + len(attackers_must_include) == 9, "Total_Attackers"
    prob += pulp.lpSum(defensemen_vars.values()) + len(defensemen_must_include) == 4, "Total_Defensemen"
    prob += pulp.lpSum(goalies_vars.values()) + len(goalies_must_include) == 2, "Total_Goalies"

    # Solve the problem
    solver = pulp.PULP_CBC_CMD(msg=0)
    prob.solve(solver)

    if prob.status != pulp.LpStatusOptimal:
        return None, None, None, 0, 0

    # Extract selected players
    selected_attackers = attackers.loc[[idx for idx, var in attackers_vars.items() if var.varValue == 1]]
    selected_defensemen = defensemen.loc[[idx for idx, var in defensemen_vars.items() if var.varValue == 1]]
    selected_goalies = goalies_data.loc[[idx for idx, var in goalies_vars.items() if var.varValue == 1]]

    # Combine must-includes
    selected_attackers = pd.concat([attackers_must_include, selected_attackers], ignore_index=True)
    selected_defensemen = pd.concat([defensemen_must_include, selected_defensemen], ignore_index=True)
    selected_goalies = pd.concat([goalies_must_include, selected_goalies], ignore_index=True)

    total_salary = (
        selected_attackers['Total Salary'].sum() +
        selected_defensemen['Total Salary'].sum() +
        selected_goalies['Total Salary'].sum()
    )

    total_score = (
        selected_attackers['Score'].sum() +
        selected_defensemen['Score'].sum() +
        selected_goalies['Score'].sum()
    )

    return selected_attackers, selected_defensemen, selected_goalies, total_salary, total_score

