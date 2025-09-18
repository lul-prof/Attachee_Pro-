from flask import Blueprint

socket_bp = Blueprint('socket', __name__)

from . import events