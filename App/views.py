from flask import Blueprint, render_template, url_for, request, flash, redirect
from flask_login import login_required, current_user
from .models import User, Match
from . import db
from datetime import datetime

views = Blueprint('views', __name__)


def calc_elo(player1, player2, winner):
    """
    Update ELO ratings for two players based on the match outcome.
    :param player1: User object for player 1
    :param player2: User object for player 2
    :param winner: 1 if player1 wins, 2 if player2 wins, 0 for a draw
    """
    K = 16  # ELO constant

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
    # Create aliases for User table
    matches = Match.query.options(
        db.joinedload(Match.player1),
        db.joinedload(Match.player2)
    ).order_by(
        Match.date.desc()
    ).limit(50).all()

    return render_template('results.html', matches=matches, user=current_user)


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

        try:
            your_score_int = int(your_score)
            opponent_score_int = int(opponent_score)
        except ValueError:
            flash('Scores must be numbers', 'error')
            return redirect(url_for('views.report'))

        # Fetch the opponent
        opponent = User.query.get(opponent_id)
        if not opponent:
            flash('Invalid opponent selected.', 'error')
            return redirect(url_for('views.report'))

        # Create match record
        new_match = Match(
            player1_id=current_user.id,
            player2_id=opponent.id,
            score1=your_score_int,
            score2=opponent_score_int,
            date=datetime.utcnow()
        )
        db.session.add(new_match)

        # Determine winner and update ELO
        winner = 1 if your_score_int > opponent_score_int else 2
        calc_elo(current_user, opponent, winner)

        db.session.commit()
        flash('Match reported successfully!', 'success')
        return redirect('/results')

    return render_template('report.html', user=current_user, users=users)


@views.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('views.home'))

    users = User.query.all()
    matches = Match.query.options(
        db.joinedload(Match.player1),
        db.joinedload(Match.player2)
    ).order_by(
        Match.date.desc()
    ).limit(50).all()

    return render_template('admin.html', users=users, matches=matches, user=current_user)


@views.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('views.home'))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    return redirect(url_for('views.admin_dashboard'))


@views.route('/admin/delete_match/<int:match_id>', methods=['POST'])
@login_required
def delete_match(match_id):
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('views.home'))

    match = Match.query.get(match_id)
    if match:
        db.session.delete(match)
        db.session.commit()
        flash('Match deleted successfully', 'success')
    return redirect(url_for('views.admin_dashboard'))


@views.route('/admin/update_elo/<int:user_id>', methods=['POST'])
@login_required
def update_elo(user_id):
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('views.home'))

    user = User.query.get(user_id)
    new_elo = request.form.get('elo')
    if user and new_elo:
        try:
            user.elo = int(new_elo)
            db.session.commit()
            flash('ELO updated successfully', 'success')
        except ValueError:
            flash('Invalid ELO value', 'danger')
    return redirect(url_for('views.admin_dashboard'))