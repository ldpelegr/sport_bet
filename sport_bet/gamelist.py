from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from sport_bet.auth import login_required
from sport_bet.db import get_db

bp = Blueprint("gamelist", __name__)


@bp.route("/")
def index():
    """Show all the games, most recent first."""
    db = get_db()
    games = db.execute(
        "SELECT p.id, title, body, tipoff, author_id, username"
        " FROM game p JOIN user u ON p.author_id = u.id"
        " ORDER BY tipoff DESC"
    ).fetchall()
    return render_template("gamelist/index.html", games=games)


def get_game(id, check_author=True):
    """Get a game and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of game to get
    :param check_author: require the current user to be the author
    :return: the game with author information
    :raise 404: if a game with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    game = (
        get_db()
        .execute(
            "SELECT p.id, title, body, tipoff, author_id, username"
            " FROM game p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if game is None:
        abort(404, f"Game id {id} doesn't exist.")

    if check_author and g.user["admin"] == 0:
        abort(403)

    return game


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new game for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        tipoff = request.form["tipoff"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO game (title, tipoff, body, author_id) VALUES (?, ?, ?, ?)",
                (title, tipoff, body, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("gamelist.index"))

    return render_template("gamelist/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a game if the current user is the author."""
    game = get_game(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        tipoff = request.form["tipoff"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE game SET title = ?, body = ?, tipoff = ? WHERE id = ?", (title, body, tipoff, id)
            )
            db.commit()
            return redirect(url_for("gamelist.index"))

    return render_template("gamelist/update.html", game=game)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a game.

    Ensures that the game exists and that the logged in user is the
    author of the game.
    """
    get_game(id)
    db = get_db()
    db.execute("DELETE FROM game WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("gamelist.index"))
