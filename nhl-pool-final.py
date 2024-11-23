import pandas as pd
import unicodedata
import pulp

# Function to convert columns to numeric
def convert_to_numeric(df, columns):
    for col in columns:
        df[col] = df[col].astype(str).str.replace('[$,]', '', regex=True).str.replace(',', '')
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# Function to normalize and standardize strings
def normalize_string(s):
    if isinstance(s, str):
        s = unicodedata.normalize('NFC', s).replace('\u00A0', ' ').strip().lower()
#        s = unicodedata.normalize('NFC', s).strip().lower()
        return s
    else:
        return s

# Read the exclusion list and must_include list from files
def read_list_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines()]
            return [line for line in lines if line and not line.startswith('#')]
    except FileNotFoundError:
        return []

# Load exclusion and must-include lists
exclusion_list = read_list_from_file('./data/exclusion.txt')
must_include_list = read_list_from_file('./data/must_include.txt')

# Normalize the names
exclusion_list_normalized = [normalize_string(name) for name in exclusion_list]
must_include_list_normalized = [normalize_string(name) for name in must_include_list]

# Load the data from the new Excel file with two sheets
skaters_data = pd.read_excel('./data/players-2024.xlsx', sheet_name='Skaters', header=0)
goalies_data = pd.read_excel('./data/players-2024.xlsx', sheet_name='Goalies', header=0)

# Assign column names based on your data
skaters_columns = ['Index', 'PlayerName', 'Blank', 'Age', 'Pos', 'Shot', 'W(lbs)', 'H(f)', 'UFA Year', 'Draft Year',
                   'Draft Position', 'Agent', 'Status', 'Length', 'Level', 'Cap Hit', 'AAV', 'Base Salary', 'Signing Bonus',
                   'Performance Bonus', 'Total Salary', 'Minor Salary', 'Structure', 'Clauses', 'Start Year',
                   'Signing Age', 'Signing Status', 'Expiry Year', 'Expiry Status', 'Signing Agent', 'GP', 'G', 'A', 'P',
                   'PPG', 'GPG', 'TOI 5x5', 'TOI 5x5/G', '+/-', 'PIM', 'GF%', 'DFF%', 'relDFF%', 'CF%', 'relCF%', 'G60', 'P60']

goalies_columns = ['Index', 'PlayerName', 'Blank','Age', 'Pos', 'Shot', 'W(lbs)', 'H(f)', 'UFA Year', 'Draft Year', 
                   'Draft Position', 'Agent', 'Status', 'Length', 'Level', 'Cap Hit', 'AAV', 'Base Salary', 'Signing Bonus', 
                   'Performance Bonus', 'Total Salary', 'Minor Salary', 'Structure', 'Clauses', 'Start Year', 'Signing Age', 
                   'Signing Status', 'Expiry Year', 'Expiry Status', 'Signing Agent', 'GP', 'SV%', 'GAA', 'SA', 'GA', 
                   'SO', 'W', 'L', 'TOI']

# Assign the column names
skaters_data.columns = skaters_columns
goalies_data.columns = goalies_columns

# Drop unnecessary columns
skaters_data = skaters_data.drop(columns=['Index', 'Blank'])
goalies_data = goalies_data.drop(columns=['Index', 'Blank'])

# Fill NaN in 'Pos' column
skaters_data['Pos'] = skaters_data['Pos'].fillna('')
goalies_data['Pos'] = goalies_data['Pos'].fillna('')

# Normalize player names
skaters_data['PlayerName_normalized'] = skaters_data['PlayerName'].apply(normalize_string)
goalies_data['PlayerName_normalized'] = goalies_data['PlayerName'].apply(normalize_string)

# Exclude players
skaters_data = skaters_data[~skaters_data['PlayerName_normalized'].isin(exclusion_list_normalized)]
goalies_data = goalies_data[~goalies_data['PlayerName_normalized'].isin(exclusion_list_normalized)]

# Convert columns to numeric
skaters_data = convert_to_numeric(skaters_data, ['G', 'A', 'Total Salary', 'P', 'GP'])
goalies_data = convert_to_numeric(goalies_data, ['SO', 'W', 'Total Salary', 'GP'])

# Calculate scores
skaters_data['Score'] = 0
skaters_data.loc[skaters_data['Pos'].str.contains('D'), 'Score'] = (2 * skaters_data['G'] + skaters_data['A'])
skaters_data.loc[skaters_data['Pos'].str.contains('C|L|R'), 'Score'] = (skaters_data['G'] + skaters_data['A'])

goalies_data['Score'] = (goalies_data['SO'] * 3) + (goalies_data['W'] * 2)

# Ensure 'Score' column is numeric
skaters_data['Score'] = pd.to_numeric(skaters_data['Score'], errors='coerce').fillna(0)
goalies_data['Score'] = pd.to_numeric(goalies_data['Score'], errors='coerce').fillna(0)

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

# Salary cap constraint (using 'Total Salary')
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

# Check the status
if prob.status != pulp.LpStatusOptimal:
    print("Warning: Could not find an optimal solution.")
else:
    print("Optimal solution found.")

# Extract selected players
selected_attackers_indices = [idx for idx, var in attackers_vars.items() if var.varValue == 1]
selected_defensemen_indices = [idx for idx, var in defensemen_vars.items() if var.varValue == 1]
selected_goalies_indices = [idx for idx, var in goalies_vars.items() if var.varValue == 1]

selected_attackers_additional = attackers.loc[selected_attackers_indices]
selected_defensemen_additional = defensemen.loc[selected_defensemen_indices]
selected_goalies_additional = goalies_data.loc[selected_goalies_indices]

# Combine with must-includes
selected_attackers = pd.concat([attackers_must_include, selected_attackers_additional], ignore_index=True)
selected_defensemen = pd.concat([defensemen_must_include, selected_defensemen_additional], ignore_index=True)
selected_goalies = pd.concat([goalies_must_include, selected_goalies_additional], ignore_index=True)

# Total salary and score
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

# Final salary cap check
if total_salary > 88_000_000:
    print("Warning: Total salary exceeds the budget after optimization!")

# Display results
print("\nTotal Salary: ${:,.2f}".format(total_salary))
print("Total Score:", total_score)

# Sort and display selected players
selected_attackers = selected_attackers.sort_values(by='Score', ascending=False)
selected_defensemen = selected_defensemen.sort_values(by='Score', ascending=False)
selected_goalies = selected_goalies.sort_values(by='Score', ascending=False)

print("\nSelected Attackers (Total: {}):".format(len(selected_attackers)))
print(selected_attackers[['PlayerName', 'Pos', 'P', 'Score', 'Total Salary', 'GP']])

print("\nSelected Defensemen (Total: {}):".format(len(selected_defensemen)))
print(selected_defensemen[['PlayerName', 'Pos', 'P', 'Score', 'Total Salary', 'GP']])

print("\nSelected Goalies (Total: {}):".format(len(selected_goalies)))
print(selected_goalies[['PlayerName', 'Pos', 'W', 'SO', 'Score', 'Total Salary', 'GP']])

# Filter out players under 22 years old who are not in the exclusion list
under_22_attackers = attackers[(attackers['Age'] < 26) & (attackers['Total Salary'] < 1500000) & (~attackers['PlayerName_normalized'].isin(exclusion_list_normalized))]
under_22_defensemen = defensemen[(defensemen['Age'] < 26) & (~defensemen['PlayerName_normalized'].isin(exclusion_list_normalized))]

# Sort by score and take the top 20
top_20_attackers_under_22 = under_22_attackers.sort_values(by='Score', ascending=False).head(20)
top_20_defensemen_under_22 = under_22_defensemen.sort_values(by='Score', ascending=False).head(20)

# Display the results
print("\nTop 20 Attackers Under 26:")
print(top_20_attackers_under_22[['PlayerName', 'Age', 'Pos', 'Score', 'Total Salary', 'GP']])

print("\nTop 20 Defensemen Under 26:")
print(top_20_defensemen_under_22[['PlayerName', 'Age', 'Pos', 'Score', 'Total Salary', 'GP']])



