from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import itertools
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tournament.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_finished = db.Column(db.Boolean, default=False)
    matches = db.relationship(
        'Match', backref='tournament', cascade="all, delete-orphan")
    players = db.relationship(
        'Player', backref='tournament', cascade="all, delete-orphan")

    def __repr__(self):
        return '<Tournament %r>' % self.name


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey(
        'tournament.id'), nullable=False)

    def __repr__(self):
        return '<Player %r>' % self.name


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey(
        'tournament.id'), nullable=False)
    player1_id = db.Column(
        db.Integer, db.ForeignKey('player.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey(
        'player.id'), nullable=True)  # Null for bye
    player1 = db.relationship('Player', foreign_keys=[
                              player1_id], backref='matches_as_player1')
    player2 = db.relationship('Player', foreign_keys=[
                              player2_id], backref='matches_as_player2')
    score_player1 = db.Column(db.Integer, default=0)
    score_player2 = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    round_number = db.Column(db.Integer, nullable=False, default=1)

    def __repr__(self):
        return '<Match %r vs %r (Round %d)>' % (self.player1.name, self.player2.name if self.player2 else 'BYE', self.round_number)


@app.route('/')
def index():
    tournaments = Tournament.query.order_by(
        Tournament.date_created.desc()).all()

    # Get all unique player names, excluding the dummy player
    known_player_names_query = db.session.query(Player.name).filter(
        Player.name != "BYE_PLAYER_DUMMY").distinct().all()
    known_player_names = [name[0] for name in known_player_names_query]

    return render_template('index.html', tournaments=tournaments, known_player_names=known_player_names)


@app.route('/create_tournament', methods=['POST'])
def create_tournament():
    tournament_name = request.form.get('tournament_name', 'Neues Turnier')
    player_names = request.form['player_names'].splitlines()
    player_names = [name.strip() for name in player_names if name.strip()]

    # Remove duplicates while preserving order
    player_names = list(dict.fromkeys(player_names))

    if len(player_names) < 2:
        return redirect(url_for('index'))  # Not enough players

    # Create new Tournament
    tournament = Tournament(name=tournament_name)
    db.session.add(tournament)
    db.session.commit()  # Commit to get ID

    players = []
    for name in player_names:
        player = Player(name=name, tournament_id=tournament.id)
        db.session.add(player)
        players.append(player)
    db.session.commit()

    # Round Robin Match Generation
    num_players = len(players)

    # If odd number of players, add a dummy player for "bye" rounds within this tournament
    if num_players % 2 != 0:
        # This player will not be displayed
        dummy_player = Player(name="BYE_PLAYER_DUMMY",
                              tournament_id=tournament.id)
        db.session.add(dummy_player)
        db.session.commit()
        players.append(dummy_player)
        num_players += 1

    # Generate matches
    schedule = []
    player_indices = list(range(num_players))

    for round_idx in range(num_players - 1):
        round_matches = []
        current_round_num = round_idx + 1
        for i in range(num_players // 2):
            p1_idx = player_indices[i]
            p2_idx = player_indices[num_players - 1 - i]

            p1 = players[p1_idx]
            p2 = players[p2_idx]

            # Only create matches if neither player is the dummy player
            if p1.name != "BYE_PLAYER_DUMMY" and p2.name != "BYE_PLAYER_DUMMY":
                round_matches.append(Match(
                    player1=p1, player2=p2, round_number=current_round_num, tournament_id=tournament.id))
            elif p1.name == "BYE_PLAYER_DUMMY":
                # p2 has a bye
                round_matches.append(Match(
                    player1=p2, player2_id=None, round_number=current_round_num, tournament_id=tournament.id))
            elif p2.name == "BYE_PLAYER_DUMMY":
                # p1 has a bye
                round_matches.append(Match(
                    player1=p1, player2_id=None, round_number=current_round_num, tournament_id=tournament.id))
        schedule.extend(round_matches)

        # Rotate players, keeping the first player fixed
        first_player = player_indices[0]
        rotated_players = player_indices[1:]
        rotated_players = rotated_players[-1:] + rotated_players[:-1]
        player_indices = [first_player] + rotated_players

    for match in schedule:
        db.session.add(match)
    db.session.commit()

    return redirect(url_for('tournament_view', tournament_id=tournament.id))


@app.route('/update_score/<int:match_id>', methods=['POST'])
def update_score(match_id):
    match = Match.query.get_or_404(match_id)
    score_player1 = request.form.get('score_player1', type=int)
    score_player2 = request.form.get('score_player2', type=int)

    if score_player1 is not None and score_player2 is not None:
        match.score_player1 = score_player1
        match.score_player2 = score_player2
        match.completed = True
        db.session.commit()
    return redirect(url_for('tournament_view', tournament_id=match.tournament_id))


@app.route('/reopen_match/<int:match_id>', methods=['POST'])
def reopen_match(match_id):
    match = Match.query.get_or_404(match_id)
    match.completed = False
    db.session.commit()
    return redirect(url_for('tournament_view', tournament_id=match.tournament_id))


@app.route('/tournament/<int:tournament_id>')
def tournament_view(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    matches = Match.query.filter_by(tournament_id=tournament.id).order_by(
        Match.round_number, Match.id).all()
    players = Player.query.filter_by(tournament_id=tournament.id).filter(
        Player.name != "BYE_PLAYER_DUMMY").all()

    # Calculate standings
    player_stats = {player.id: {'player': player, 'points': 0, 'wins': 0,
                                'losses': 0, 'draws': 0, 'legs_won': 0, 'legs_lost': 0} for player in players}

    for match in matches:
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

    # Convert to a list and sort
    standings = list(player_stats.values())
    standings.sort(key=lambda x: (
        x['points'], (x['legs_won'] - x['legs_lost'])), reverse=True)

    # Group matches by round for display, excluding bye matches
    matches_by_round = {}
    for match in matches:
        if match.player2_id is not None:  # Exclude matches with a bye
            if match.round_number not in matches_by_round:
                matches_by_round[match.round_number] = []
            matches_by_round[match.round_number].append(match)

    # Check if all matches are completed (excluding byes) for the finish button
    # Using the same logic as in finish_tournament route
    unfinished_matches_count = Match.query.filter_by(
        tournament_id=tournament.id, completed=False).filter(Match.player2_id != None).count()
    all_matches_completed = (unfinished_matches_count ==
                             0) and (len(matches) > 0)

    return render_template('tournament.html', tournament=tournament, matches_by_round=matches_by_round, standings=standings, all_matches_completed=all_matches_completed)


@app.route('/finish_tournament/<int:tournament_id>', methods=['POST'])
def finish_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    # Check if all matches are completed (excluding byes)
    unfinished_matches = Match.query.filter_by(
        tournament_id=tournament.id, completed=False).filter(Match.player2_id != None).count()

    if unfinished_matches == 0:
        tournament.is_finished = True
        db.session.commit()

    return redirect(url_for('tournament_view', tournament_id=tournament.id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
