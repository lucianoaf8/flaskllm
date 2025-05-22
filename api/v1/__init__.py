from flask import Blueprint
from .routes import core, auth, calendar, files, conversations, streaming, admin

def create_v1_blueprint() -> Blueprint:
    v1_bp = Blueprint("v1", __name__, url_prefix="/v1")
    
    # Register route blueprints
    v1_bp.register_blueprint(core.bp)
    v1_bp.register_blueprint(auth.bp)
    v1_bp.register_blueprint(calendar.bp)
    v1_bp.register_blueprint(files.bp)
    v1_bp.register_blueprint(conversations.bp)
    v1_bp.register_blueprint(streaming.bp)
    v1_bp.register_blueprint(admin.bp)
    
    return v1_bp