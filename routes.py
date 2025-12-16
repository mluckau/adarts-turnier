from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Tournament, Player, Match
from utils import sort_standings, generate_round_robin_schedule, generate_knockout_schedule, advance_winner
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    tournaments = Tournament.query.order_by(Tournament.date_created.desc()).all()
    
    # Get all unique player names, excluding the dummy player
    known_player_names_query = db.session.query(Player.name).filter(Player.name != "BYE_PLAYER_DUMMY").distinct().all()
    known_player_names = [name[0] for name in known_player_names_query]

    default_tournament_name = f"Turnier vom {datetime.now().strftime('%d.%m.%Y')}"

    return render_template('index.html', tournaments=tournaments, known_player_names=known_player_names, default_tournament_name=default_tournament_name)

@main.route('/create_tournament', methods=['POST'])
def create_tournament():
    tournament_name = request.form.get('tournament_name', 'Neues Turnier')
    tournament_mode = request.form.get('tournament_mode', 'round_robin')
    player_names = request.form['player_names'].splitlines()
    player_names = [name.strip() for name in player_names if name.strip()]

    # Remove duplicates while preserving order
    player_names = list(dict.fromkeys(player_names))

    if len(player_names) < 2:
        return redirect(url_for('main.index')) # Not enough players

    # Handle duplicate tournament names
    original_name = tournament_name
    counter = 1
    while Tournament.query.filter_by(name=tournament_name).first() is not None:
        counter += 1
        tournament_name = f"{original_name} ({counter})"

    # Create new Tournament
    tournament = Tournament(name=tournament_name, mode=tournament_mode)
    db.session.add(tournament)
    db.session.commit() # Commit to get ID

    players = []
    for name in player_names:
        player = Player(name=name, tournament_id=tournament.id)
        db.session.add(player)
        players.append(player)
    db.session.commit()

    if tournament_mode == 'round_robin':
        generate_round_robin_schedule(tournament.id, players)
    elif tournament_mode == 'knockout':
        generate_knockout_schedule(tournament.id, players)
    
    return redirect(url_for('main.tournament_view', tournament_id=tournament.id))

@main.route('/update_score/<int:match_id>', methods=['POST'])
def update_score(match_id):
    match = Match.query.get_or_404(match_id)
    score_player1 = request.form.get('score_player1', type=int)
    score_player2 = request.form.get('score_player2', type=int)

    if score_player1 is not None and score_player2 is not None:
        match.score_player1 = score_player1
        match.score_player2 = score_player2
        match.completed = True
        
        # Advance winner if in knockout mode (or check next_match_id)
        if match.tournament.mode == 'knockout':
            advance_winner(match)
            
        db.session.commit()
    return redirect(url_for('main.tournament_view', tournament_id=match.tournament_id))


@main.route('/reopen_match/<int:match_id>', methods=['POST'])
def reopen_match(match_id):
    match = Match.query.get_or_404(match_id)
    match.completed = False
    # TODO: Handle undoing advancement? 
    # For now, just reopen. The next match might need to be reset manually or logic added.
    # Logic to reset next match:
    if match.tournament.mode == 'knockout' and match.next_match_id:
        next_match = Match.query.get(match.next_match_id)
        if next_match:
            # Reset the slot in next match
            if match.next_match_slot == 1:
                next_match.player1 = None
            elif match.next_match_slot == 2:
                next_match.player2 = None
            # Also reset next match scores/completion if it was started?
            if next_match.completed:
                # Recursive reopen? simpler to just uncomplete it.
                next_match.completed = False
                next_match.score_player1 = 0
                next_match.score_player2 = 0
                # And recursive up the chain...
                # For MVP, just resetting immediate next match player is enough.
            
    db.session.commit()
    return redirect(url_for('main.tournament_view', tournament_id=match.tournament_id))


@main.route('/tournament/<int:tournament_id>')
def tournament_view(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    matches = Match.query.filter_by(tournament_id=tournament.id).order_by(
        Match.round_number, Match.id).all()
    players = Player.query.filter_by(tournament_id=tournament.id).filter(
        Player.name != "BYE_PLAYER_DUMMY").all()

    # Calculate standings (Round Robin logic mostly, but safe for KO)
    player_stats = {player.id: {'player': player, 'points': 0, 'wins': 0,
                                'losses': 0, 'draws': 0, 'legs_won': 0, 'legs_lost': 0, 'open_matches': 0} for player in players}

    # Helper map to find match between two players quickly
    match_map = {}
    
    for match in matches:
        if match.player1_id and match.player2_id:
            # Store match reference for direct comparison
            p1 = match.player1_id
            p2 = match.player2_id
            match_map[(min(p1, p2), max(p1, p2))] = match
            
            if not match.completed:
                player_stats[match.player1.id]['open_matches'] += 1
                player_stats[match.player2.id]['open_matches'] += 1

        if match.completed and match.player1_id and match.player2_id:  # Exclude byes and future matches
            # Update legs
            player_stats[match.player1.id]['legs_won'] += match.score_player1
            player_stats[match.player1.id]['legs_lost'] += match.score_player2
            player_stats[match.player2.id]['legs_won'] += match.score_player2
            player_stats[match.player2.id]['legs_lost'] += match.score_player1

            if match.score_player1 > match.score_player2:
                # 2 points for a win
                player_stats[match.player1.id]['points'] += 2
                player_stats[match.player1.id]['wins'] += 1
                player_stats[match.player2.id]['losses'] += 1
            elif match.score_player2 > match.score_player1:
                player_stats[match.player2.id]['points'] += 2
                player_stats[match.player2.id]['wins'] += 1
                player_stats[match.player1.id]['losses'] += 1
            else:
                # 1 point for a draw
                player_stats[match.player1.id]['points'] += 1
                player_stats[match.player2.id]['points'] += 1
                player_stats[match.player1.id]['draws'] += 1
                player_stats[match.player2.id]['draws'] += 1
        elif match.completed and (match.player2_id is None or match.player1_id is None):  # Handle byes
            pass

    # Sort standings using utils logic
    if tournament.mode == 'round_robin':
        standings = sort_standings(player_stats, matches)
    else:
        # KO: Rank by specific achievements
        # 1. Winner of Final
        # 2. Loser of Final
        # 3. Winner of 3rd Place Match
        # 4. Loser of 3rd Place Match
        # 5+. Sort by wins
        
        # Identify specific matches
        final_match = None
        third_place_match = None
        
        # Max round number logic is brittle if we just take max(round_number) because 3rd place is also max.
        # But we added is_third_place flag.
        
        # Find max round number
        max_round = 0
        if matches:
            max_round = max(m.round_number for m in matches)
            
        for m in matches:
            if m.round_number == max_round:
                if m.is_third_place:
                    third_place_match = m
                else:
                    final_match = m
        
        # Assign ranks
        ranked_ids = []
        
        if final_match and final_match.completed:
            if final_match.score_player1 > final_match.score_player2:
                ranked_ids.append(final_match.player1_id) # 1st
                ranked_ids.append(final_match.player2_id) # 2nd
            else:
                ranked_ids.append(final_match.player2_id) # 1st
                ranked_ids.append(final_match.player1_id) # 2nd
                
        if third_place_match and third_place_match.completed:
            if third_place_match.score_player1 > third_place_match.score_player2:
                ranked_ids.append(third_place_match.player1_id) # 3rd
                ranked_ids.append(third_place_match.player2_id) # 4th
            else:
                ranked_ids.append(third_place_match.player2_id) # 3rd
                ranked_ids.append(third_place_match.player1_id) # 4th
        
        # Build the final sorted list
        # Start with the specifically ranked players
        ko_standings = []
        for pid in ranked_ids:
            if pid in player_stats:
                ko_standings.append(player_stats[pid])
                
        # Add the rest, sorted by wins
        rest_of_players = [p for pid, p in player_stats.items() if pid not in ranked_ids]
        rest_of_players.sort(key=lambda x: x['wins'], reverse=True)
        
        standings = ko_standings + rest_of_players

    # Group matches by round for display, excluding bye matches
    matches_by_round = {}
    match_counter = 1
    total_matches = 0
    completed_matches = 0
    
    for match in matches:
        # In KO, we show all matches, even placeholders?
        # Yes, for the bracket.
        # But for 'round_robin' view logic, we filtered.
        # Let's keep existing logic for RR.
        
        if tournament.mode == 'round_robin':
            if match.player2_id is not None:  # Exclude matches with a bye
                total_matches += 1
                if match.completed:
                    completed_matches += 1
                    
                match.display_number = match_counter
                match_counter += 1
                if match.round_number not in matches_by_round:
                    matches_by_round[match.round_number] = []
                matches_by_round[match.round_number].append(match)
        else:
            # KO Logic: Include all matches
            total_matches += 1
            if match.completed:
                completed_matches += 1
            match.display_number = match.id # Use ID or something
            if match.round_number not in matches_by_round:
                matches_by_round[match.round_number] = []
            matches_by_round[match.round_number].append(match)

    # Check if all matches are completed
    if tournament.mode == 'round_robin':
        unfinished_matches_count = Match.query.filter_by(
            tournament_id=tournament.id, completed=False).filter(Match.player2_id != None).count()
    else:
        # KO: All matches must be completed
        unfinished_matches_count = Match.query.filter_by(
            tournament_id=tournament.id, completed=False).count()
            
    all_matches_completed = (unfinished_matches_count ==
                             0) and (len(matches) > 0)

    return render_template('tournament.html', tournament=tournament, matches_by_round=matches_by_round, standings=standings, all_matches_completed=all_matches_completed, total_matches=total_matches, completed_matches=completed_matches)

@main.route('/finish_tournament/<int:tournament_id>', methods=['POST'])
def finish_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    # Check if all matches are completed (excluding byes)
    unfinished_matches = Match.query.filter_by(
        tournament_id=tournament.id, completed=False).filter(Match.player2_id != None).count()

    if unfinished_matches == 0:
        tournament.is_finished = True
        db.session.commit()

    return redirect(url_for('main.tournament_view', tournament_id=tournament.id))
