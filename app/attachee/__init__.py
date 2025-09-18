from flask import Blueprint

attachee_bp = Blueprint('attachee', __name__, url_prefix='/attachee')

from . import routes