from models import db, Match, Player
import math
import random

def advance_winner(match):
    """
    Advances the winner of a match to the next match in the bracket.
    """
    if not match.completed:
        return
        
    winner = None
    if match.player2 is None:
        # Bye
        winner = match.player1
    elif match.score_player1 > match.score_player2:
        winner = match.player1
    elif match.score_player2 > match.score_player1:
        winner = match.player2
    else:
        # Draw? No draws in KO.
        return

    if match.next_match_id and winner:
        next_match = Match.query.get(match.next_match_id)
        if next_match:
            if match.next_match_slot == 1:
                next_match.player1 = winner
            elif match.next_match_slot == 2:
                next_match.player2 = winner
            db.session.add(next_match) # Mark as modified

def generate_knockout_schedule(tournament_id, players):
    n_players = len(players)
    if n_players < 2:
        return

    bracket_size = 2 ** math.ceil(math.log2(n_players))
    total_rounds = int(math.log2(bracket_size))
    
    rounds = []
    
    # Create matches for each round (empty placeholders initially)
    for r in range(1, total_rounds + 1):
        num_matches = bracket_size // (2 ** r)
        matches_in_r = []
        for _ in range(num_matches):
            # player1_id=None allowed now
            m = Match(tournament_id=tournament_id, round_number=r)
            db.session.add(m)
            matches_in_r.append(m)
        rounds.append(matches_in_r)
        
    db.session.flush() # Generate IDs
    
    # Link matches: Round r matches feed into Round r+1
    # rounds index 0 is Round 1, index 1 is Round 2, etc.
    for r_idx in range(total_rounds - 1): # 0 to N-2
        current_round = rounds[r_idx]
        next_round = rounds[r_idx+1]
        
        for i, match in enumerate(current_round):
            next_match_idx = i // 2
            next_m = next_round[next_match_idx]
            match.next_match_id = next_m.id
            match.next_match_slot = 1 if (i % 2 == 0) else 2
            
    # Assign players to Round 1
    # Distribute Byes:
    # First (N - Byes) matches are P vs P
    # Last Byes matches are P vs Bye
    
    random.shuffle(players)
    player_idx = 0
    round1_matches = rounds[0]
    n_byes = bracket_size - n_players
    
    # Number of matches that will be fully populated (P vs P)
    # Total slots = 2 * len(round1_matches).
    # We have n_players. n_byes.
    # We want to fill matches such that Byes are paired with Players.
    # Every Bye consumes 1 Match (Player vs Bye).
    # Remaining matches are Player vs Player.
    # Check: n_byes <= len(round1_matches)?
    # 5 players, size 8. 4 matches. 3 byes. 3 < 4. Yes.
    # 3 players, size 4. 2 matches. 1 bye. 1 < 2. Yes.
    
    # So we have `n_byes` matches with (P, Bye).
    # And `len(round1_matches) - n_byes` matches with (P, P).
    
    # Optimization: Distribute Byes? usually top/bottom.
    # For now, put Byes at the end of the list so they feed into specific parts of the bracket?
    # Or spread them?
    # If we put them at the end, one half of the bracket might be empty.
    # Better to spread. 
    # But simple logic first.
    
    n_full_matches = len(round1_matches) - n_byes
    
    # Assign players
    for i, match in enumerate(round1_matches):
        if i < n_full_matches:
            # Full match (P vs P)
            match.player1 = players[player_idx]
            match.player2 = players[player_idx + 1]
            player_idx += 2
        else:
            # Bye match (P vs Bye)
            match.player1 = players[player_idx]
            match.player2 = None
            player_idx += 1
            
            # Auto-complete
            match.completed = True
            
    db.session.commit()
    
    # Advance winners for completed matches (Byes)
    # Need to query from DB to ensure relationships are loaded if needed
    r1 = Match.query.filter_by(tournament_id=tournament_id, round_number=1).all()
    for m in r1:
        if m.completed:
            advance_winner(m)
            
    db.session.commit()

def generate_round_robin_schedule(tournament_id, players):
    num_players = len(players)
    
    # If odd number of players, add a dummy player for "bye" rounds
    if num_players % 2 != 0:
        dummy_player = Player(name="BYE_PLAYER_DUMMY", tournament_id=tournament_id)
        db.session.add(dummy_player)
        db.session.commit()
        players.append(dummy_player)
        num_players += 1

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
                round_matches.append(Match(player1=p1, player2=p2, round_number=current_round_num, tournament_id=tournament_id))
            elif p1.name == "BYE_PLAYER_DUMMY":
                # p2 has a bye
                round_matches.append(Match(player1=p2, player2_id=None, round_number=current_round_num, tournament_id=tournament_id))
            elif p2.name == "BYE_PLAYER_DUMMY":
                # p1 has a bye
                round_matches.append(Match(player1=p1, player2_id=None, round_number=current_round_num, tournament_id=tournament_id))
        schedule.extend(round_matches)

        # Rotate players, keeping the first player fixed
        first_player = player_indices[0]
        rotated_players = player_indices[1:]
        rotated_players = rotated_players[-1:] + rotated_players[:-1]
        player_indices = [first_player] + rotated_players
    
    for match in schedule:
        db.session.add(match)
    db.session.commit()

def calculate_mini_league(matches, tied_players_ids):
    """
    Calculates stats considering ONLY matches between the players in tied_players_ids.
    Returns a dict: {player_id: {'mini_points': x, 'mini_diff': y, 'mini_legs_won': z}}
    """
    mini_stats = {pid: {'mini_points': 0, 'mini_diff': 0, 'mini_legs_won': 0} for pid in tied_players_ids}
    
    for match in matches:
        if match.completed and match.player1_id in tied_players_ids and match.player2_id in tied_players_ids:
            p1 = match.player1_id
            p2 = match.player2_id
            
            s1 = match.score_player1
            s2 = match.score_player2
            
            # Update Mini Legs
            mini_stats[p1]['mini_legs_won'] += s1
            mini_stats[p1]['mini_diff'] += (s1 - s2)
            
            mini_stats[p2]['mini_legs_won'] += s2
            mini_stats[p2]['mini_diff'] += (s2 - s1)
            
            # Update Mini Points
            if s1 > s2:
                mini_stats[p1]['mini_points'] += 2
            elif s2 > s1:
                mini_stats[p2]['mini_points'] += 2
            else:
                mini_stats[p1]['mini_points'] += 1
                mini_stats[p2]['mini_points'] += 1
    return mini_stats

def sort_standings(player_stats, matches):
    # 1. Initial sort by Total Points
    # We group players by points to identify ties.
    standings = list(player_stats.values())
    # Primary sort key: Points (desc)
    # Secondary sort key (temporary): Overall Leg Diff (desc) just to have a stable starting point
    standings.sort(key=lambda x: (x['points'], x['legs_won'] - x['legs_lost']), reverse=True)
    
    final_standings = []
    
    # Process groups of players with the same points
    import itertools
    for points, group in itertools.groupby(standings, key=lambda x: x['points']):
        group_list = list(group)
        
        if len(group_list) < 2:
            # No tie, just add to final standings
            final_standings.extend(group_list)
        else:
            # Tie detected! Apply Mini-League logic.
            tied_ids = {p['player'].id for p in group_list}
            mini_results = calculate_mini_league(matches, tied_ids)
            
            # Sort the tied group based on specific criteria hierarchy
            def tie_breaker_key(p_stat):
                pid = p_stat['player'].id
                mini = mini_results[pid]
                
                # Criteria 1: Mini-League Points (desc)
                c1 = mini['mini_points']
                
                # Criteria 2: Mini-League Leg Difference (desc)
                c2 = mini['mini_diff']
                
                # Criteria 3: Overall Leg Difference (desc) - Fallback to global stats
                c3 = p_stat['legs_won'] - p_stat['legs_lost']
                
                # Criteria 4: Overall Legs Won (desc)
                c4 = p_stat['legs_won']
                
                return (c1, c2, c3, c4)
            
            group_list.sort(key=tie_breaker_key, reverse=True)
            final_standings.extend(group_list)
            
    return final_standings
