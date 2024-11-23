from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from utils import (
    read_list_from_file, 
    write_to_list_file, 
    remove_from_list_file, 
    optimize_nhl_pool,
    perform_player_search
)
import logging

routes = Blueprint('main', __name__)

@routes.route('/', methods=['GET'])
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error rendering index: {e}")
        flash('An unexpected error occurred', 'error')
        return render_template('error.html'), 500

@routes.route('/search', methods=['GET', 'POST'])
def search_players():
    if request.method == 'POST':
        try:
            keyword = request.form.get('keyword', '').strip()
            list_type = request.form.get('list_type')

            if not keyword:
                flash('Please enter a search keyword', 'warning')
                return redirect(url_for('main.search_players'))

            search_results = perform_player_search(keyword, list_type)

            if not search_results:
                flash('No players found matching your search', 'info')

            return render_template('search.html', 
                                   results=search_results, 
                                   keyword=keyword)
        except Exception as e:
            logging.error(f"Search error: {e}")
            flash('An error occurred during search', 'error')
            return redirect(url_for('main.search_players'))

    return render_template('search.html')

@routes.route('/lists', methods=['GET'])
def view_lists():
    try:
        exclusion_list = read_list_from_file(current_app.config['EXCLUSION_FILE'])
        must_include_list = read_list_from_file(current_app.config['MUST_INCLUDE_FILE'])
        
        return render_template('lists.html', 
                               exclusion_list=exclusion_list, 
                               must_include_list=must_include_list)
    except FileNotFoundError:
        flash('List files not found', 'error')
        return render_template('lists.html', 
                               exclusion_list=[], 
                               must_include_list=[])
    except Exception as e:
        logging.error(f"Error reading lists: {e}")
        flash('An unexpected error occurred', 'error')
        return render_template('lists.html', 
                               exclusion_list=[], 
                               must_include_list=[])

@routes.route('/run_optimization', methods=['POST'])
def run_optimization():
    try:
        total_score, total_salary, selected_players = optimize_nhl_pool(current_app.config)
        
        return jsonify({
            'success': True,
            'total_score': total_score,
            'total_salary': total_salary,
            'selected_players': selected_players
        }), 200
    except Exception as e:
        logging.error(f"Optimization error: {e}")
        return jsonify({
            'success': False,
            'message': 'Optimization failed',
            'error': str(e)
        }), 500

@routes.route('/add_player', methods=['POST'])
def add_player():
    try:
        player_name = request.json.get('player')
        list_type = request.json.get('list_type')

        if not player_name or not list_type:
            return jsonify({'success': False, 'message': 'Invalid input'}), 400

        write_to_list_file(current_app.config[f'{list_type.upper()}_FILE'], player_name)
        
        return jsonify({
            'success': True, 
            'message': f'Player {player_name} added to {list_type} list'
        }), 200
    except Exception as e:
        logging.error(f"Add player error: {e}")
        return jsonify({
            'success': False, 
            'message': 'Failed to add player'
        }), 500

@routes.route('/remove_player', methods=['POST'])
def remove_player():
    try:
        player_name = request.json.get('player')
        list_type = request.json.get('list_type')

        if not player_name or not list_type:
            return jsonify({'success': False, 'message': 'Invalid input'}), 400

        remove_from_list_file(current_app.config[f'{list_type.upper()}_FILE'], player_name)
        
        return jsonify({
            'success': True, 
            'message': f'Player {player_name} removed from {list_type} list'
        }), 200
    except Exception as e:
        logging.error(f"Remove player error: {e}")
        return jsonify({
            'success': False, 
            'message': 'Failed to remove player'
        }), 500
