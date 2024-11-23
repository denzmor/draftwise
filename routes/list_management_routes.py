from flask import Blueprint, jsonify, request

list_management_bp = Blueprint('list_management', __name__)

@list_management_bp.route('/exclusions', methods=['GET', 'POST'])
def manage_exclusions():
    """
    Manage exclusion lists
    """
    try:
        if request.method == 'GET':
            # Retrieve exclusion list
            exclusions = ["Player X", "Player Y"]
            return jsonify(exclusions), 200
        
        elif request.method == 'POST':
            # Add to exclusion list
            new_exclusion = request.json.get('player')
            # Placeholder for adding to list
            return jsonify({"message": f"Added {new_exclusion} to exclusions"}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
