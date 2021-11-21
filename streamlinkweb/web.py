import logging
import re
from os import urandom
from urllib.parse import urlparse

from flask import (
    Flask,
    Markup,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from requests_futures.sessions import FuturesSession
from wtforms.fields import *
from wtforms.validators import InputRequired, Regexp

from streamlink import initialize_streamlink

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    proxy_twitch = BooleanField("Use Proxy")
    submit = SubmitField("Get stream URL")


@app.route("/", methods=["GET", "POST"])
async def hello():
    form = IndexForm()
    if form.validate_on_submit():
        res = await initialize_streamlink(
            streamurl=form.stream_url.data,
            quality=form.quality.data,
            proxy=form.proxy_twitch.data,
        )
        if form.proxy_twitch.data:
            my_url = urlparse(request.url)
            vlc_url = "{}://{}{}/{}".format(
                my_url.scheme,
                my_url.hostname,
                f":{my_url.port}" if my_url.port not in [80, 443, None] else "",
                res,
            )
            flash(Markup(f"Open this URL in VLC: <a href={vlc_url}>{vlc_url}</a>."))
        else:
            flash(
                Markup(f"Open this URL in VLC: <a href={res}>twitch stream link</a>.")
            )
        return redirect(url_for("hello"))
    return render_template("index.html", form=form)


@app.route("/<int:port>", methods=["GET", "POST"])
async def proxy(port):
    logger.info("Received request for port %s", port)
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
    logger.info("STatus code is %s", resp.status_code)
    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]
    response = Response(
        response=resp.iter_content(chunk_size=10 * 1024),
        status=resp.status_code,
        headers=headers,
    )
    return response
