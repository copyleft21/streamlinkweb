import asyncio
import re
from os import urandom

from flask import Flask, Response, flash, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from markupsafe import escape
from requests_futures.sessions import FuturesSession
from wtforms.fields import *
from wtforms.validators import InputRequired
from wtforms.validators import Regexp

app = Flask(__name__)
app.config["SECRET_KEY"] = urandom(32)
Bootstrap(app)


class IndexForm(FlaskForm):
    stream_url = StringField(
        "Stream URL",
        validators=[
            InputRequired(message="You must enter a URL"),
            Regexp(
                "^(https?:\/\/)?twitch.tv/",
                flags=re.IGNORECASE,
                message="Must be a twitch.tv URL",
            ),
        ],
    )
    # Can use some python-twitch stuff to dynamically load the options here maybe.
    quality = SelectField(
        "Stream Quality",
        choices=[("best", "Best"), ("worst", "Worst")],
        validators=[InputRequired(message="You must select a quality")],
    )
    submit = SubmitField("Get stream URL")


@app.route("/", methods=["GET", "POST"])
async def hello():
    form = IndexForm()
    if form.validate_on_submit():
        flash(f"You submitted {form.stream_url.data}")
        return redirect(url_for("hello"))
    return render_template("index.html", form=form)


@app.route("/<int:port>", methods=["GET", "POST"])
async def proxy(port):
    session = FuturesSession()
    resp = session.request(
        method=request.method, url=f"http://localhost:{port}", stream=True
    )
    excluded_headers = [
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    ]
    resp = resp.result()
    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]
    response = Response(
        resp.iter_content(chunk_size=10 * 1024),
        resp.status_code,
        headers,
    )
    return response


if __name__ == "__main__":
    asyncio.run(app.run("localhost", 4449))
