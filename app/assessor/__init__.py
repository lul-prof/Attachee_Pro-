from flask import Blueprint

assessor = Blueprint('assessor', __name__, url_prefix='/assessor')

from . import routes