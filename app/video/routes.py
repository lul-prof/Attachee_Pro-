from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from app import db, socketio
from app.models import User, VideoSession, VideoSessionStatus
from app.models import UserRole
from app.video.forms import JoinSessionForm
from app.video import video
from app.utils.decorators import role_required
from datetime import datetime
import uuid
import secrets

@video.route('/join/<string:room_id>')
@login_required
def join_session(room_id):
    # Find the session by room_id
    session = VideoSession.query.filter_by(room_id=room_id).first_or_404()
    
    # Check if user is authorized to join this session
    if current_user.id != session.attachee_id and current_user.id != session.assessor_id:
        flash('You are not authorized to join this video session.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get the other participant
    other_participant_id = session.attachee_id if current_user.id == session.assessor_id else session.assessor_id
    other_participant = User.query.get_or_404(other_participant_id)
    
    return render_template('video/video_room.html',
                          title=f'Video Session: {session.title}',
                          session=session,
                          other_participant=other_participant,
                          room_id=room_id)

@video.route('/session/<int:session_id>')
@login_required
def session_detail(session_id):
    # Find the session
    session = VideoSession.query.filter_by(id=session_id).first_or_404()
    
    # Check if user is authorized to view this session
    if current_user.id != session.attachee_id and current_user.id != session.assessor_id:
        flash('You are not authorized to view this video session.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get the other participant
    other_participant_id = session.attachee_id if current_user.id == session.assessor_id else session.assessor_id
    other_participant = User.query.get_or_404(other_participant_id)
    
    # Check if session has a room_id, if not create one
    if not session.room_id:
        session.room_id = str(uuid.uuid4())
        db.session.commit()
    
    return render_template('video/session_detail.html',
                          title=f'Session: {session.title}',
                          session=session,
                          other_participant=other_participant)

@video.route('/create-room', methods=['POST'])
@login_required
def create_room():
    # This endpoint is for creating ad-hoc rooms
    session_id = request.form.get('session_id')
    
    if session_id:
        # If session_id provided, use that session
        session = VideoSession.query.filter_by(id=session_id).first_or_404()
        
        # Check authorization
        if current_user.id != session.attachee_id and current_user.id != session.assessor_id:
            return jsonify({'error': 'Not authorized'}), 403
        
        # Generate room_id if not exists
        if not session.room_id:
            session.room_id = str(uuid.uuid4())
            db.session.commit()
        
        room_id = session.room_id
    else:
        # Generate a random room ID for ad-hoc meetings
        room_id = str(uuid.uuid4())
    
    return jsonify({'room_id': room_id})