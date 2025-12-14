from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Tournament, Player, Match
from utils import sort_standings, generate_round_robin_schedule
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
        db.session.commit()
    return redirect(url_for('main.tournament_view', tournament_id=match.tournament_id))


@main.route('/reopen_match/<int:match_id>', methods=['POST'])
def reopen_match(match_id):
    match = Match.query.get_or_404(match_id)
    match.completed = False
    db.session.commit()
    return redirect(url_for('main.tournament_view', tournament_id=match.tournament_id))


@main.route('/tournament/<int:tournament_id>')
def tournament_view(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    matches = Match.query.filter_by(tournament_id=tournament.id).order_by(
        Match.round_number, Match.id).all()
    players = Player.query.filter_by(tournament_id=tournament.id).filter(
        Player.name != "BYE_PLAYER_DUMMY").all()

    # Calculate standings
    player_stats = {player.id: {'player': player, 'points': 0, 'wins': 0,
                                'losses': 0, 'draws': 0, 'legs_won': 0, 'legs_lost': 0} for player in players}

    # Helper map to find match between two players quickly
    match_map = {}

    for match in matches:
        if match.player2_id is not None:
            # Store match reference for direct comparison
            p1 = match.player1_id
            p2 = match.player2_id
            match_map[(min(p1, p2), max(p1, p2))] = match

        if match.completed and match.player2_id is not None:  # Exclude byes
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
        elif match.completed and match.player2_id is None:  # Handle byes
            pass

    # Sort standings using utils logic
    standings = sort_standings(player_stats, matches)

    # Group matches by round for display, excluding bye matches
    matches_by_round = {}
    for match in matches:
        if match.player2_id is not None:  # Exclude matches with a bye
            if match.round_number not in matches_by_round:
                matches_by_round[match.round_number] = []
            matches_by_round[match.round_number].append(match)

    # Check if all matches are completed (excluding byes) for the finish button
    unfinished_matches_count = Match.query.filter_by(
        tournament_id=tournament.id, completed=False).filter(Match.player2_id != None).count()
    all_matches_completed = (unfinished_matches_count ==
                             0) and (len(matches) > 0)

    return render_template('tournament.html', tournament=tournament, matches_by_round=matches_by_round, standings=standings, all_matches_completed=all_matches_completed)


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
