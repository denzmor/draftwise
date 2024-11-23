from flask import Blueprint, jsonify, request

player_bp = Blueprint('player', __name__)

@player_bp.route('/', methods=['GET'])
def get_players():
    """
    Retrieve list of players
    """
    try:
        # Placeholder for player retrieval logic
        players = [
            {"id": 1, "name": "Connor McDavid"},
            {"id": 2, "name": "Sidney Crosby"}
        ]
        return jsonify(players), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@player_bp.route('/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """
    Retrieve specific player by ID
    """
    try:
        # Placeholder for player retrieval logic
        player = {"id": player_id, "name": f"Player {player_id}"}
        return jsonify(player), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404
