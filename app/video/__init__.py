from flask import Blueprint

video = Blueprint('video', __name__, url_prefix='/video')

from . import routes