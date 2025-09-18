from flask import Blueprint

org_manager = Blueprint('org_manager', __name__, url_prefix='/org_manager')

from . import routes