from flask import Blueprint, render_template, url_for, request, flash, redirect
from flask_login import login_required, current_user
from .models import User, Match
from . import db

views = Blueprint('views', __name__)


def update_elo(player1, player2, winner):
    """
    Update ELO ratings for two players based on the match outcome.
    :param player1: User object for player 1
    :param player2: User object for player 2
    :param winner: 1 if player1 wins, 2 if player2 wins, 0 for a draw
    """
    K = 32  # ELO constant

    # Expected scores
    expected_player1 = 1 / (1 + 10 ** ((player2.elo - player1.elo) / 400))
    expected_player2 = 1 / (1 + 10 ** ((player1.elo - player2.elo) / 400))

    # Actual scores
    if winner == 1:
        actual_player1 = 1
        actual_player2 = 0
    elif winner == 2:
        actual_player1 = 0
        actual_player2 = 1
    else:  # Draw
        actual_player1 = 0.5
        actual_player2 = 0.5

    # Update ratings
    player1.elo += K * (actual_player1 - expected_player1)
    player2.elo += K * (actual_player2 - expected_player2)

    # Save changes to the database
    db.session.commit()


@views.route('/')
def home():
    users = User.query.order_by(User.elo.desc()).all()
    return render_template('home.html', users=users, user=current_user)


@views.route('/results')
def results():
    matches = Match.query.order_by(Match.date.desc()).all()
    users = User.query.all()
    return render_template('results.html', matches=matches, users=users, user=current_user)


@views.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    users = User.query.filter(User.id != current_user.id)
    if request.method == 'POST':
        opponent_id = request.form.get('opponent')
        your_score = request.form.get('your_score')
        opponent_score = request.form.get('oscore')

        # Validate the input
        if not opponent_id or not your_score or not opponent_score:
            flash('Please fill out all fields.', 'error')
            return redirect(url_for('views.report'))
        elif your_score == opponent_score:
            flash("No draws allowed!", category="error")
            return redirect((url_for('views.report')))

        # Fetch the opponent from the database
        opponent = User.query.get(opponent_id)
        if not opponent:
            flash('Invalid opponent selected.', 'error')
            return redirect(url_for('views.report'))

        # Create a new match record (example logic)
        new_match = Match(
            name1=current_user.name,
            name2=opponent.name,
            score1=your_score,
            score2=opponent_score,
        )
        db.session.add(new_match)
        db.session.commit()
        update_elo(current_user, opponent, [1 if your_score > opponent_score else 2][0])

        flash('Match reported successfully!', 'success')
        return redirect('/report')

    return render_template('report.html', user=current_user, users=users)
