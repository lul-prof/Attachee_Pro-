from flask import request, current_app
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio, db
from app.models import VideoSession, User, VideoSessionStatus
from datetime import datetime
import json

# Store active rooms and participants
active_rooms = {}

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False
    print(f"User {current_user.username} connected")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"User {current_user.username if current_user.is_authenticated else 'Anonymous'} disconnected")
    # Clean up any rooms the user was in
    for room_id, participants in list(active_rooms.items()):
        if current_user.id in participants:
            participants.remove(current_user.id)
            # Notify others in the room
            emit('user_left', {'user_id': current_user.id, 'username': current_user.username}, room=room_id)
            # If room is empty, remove it
            if not participants:
                del active_rooms[room_id]

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data.get('room_id')
    if not room_id:
        emit('error', {'message': 'Room ID is required'})
        return
    
    # Check if the session exists and user has permission
    session = VideoSession.query.filter_by(room_id=room_id).first()
    if not session:
        emit('error', {'message': 'Invalid room ID'})
        return
    
    # Check if user is authorized to join this room
    if current_user.id != session.attachee_id and current_user.id != session.assessor_id:
        emit('error', {'message': 'You are not authorized to join this room'})
        return
    
    # Join the room
    join_room(room_id)
    
    # Initialize room if not exists
    if room_id not in active_rooms:
        active_rooms[room_id] = []
    
    # Add user to room participants if not already there
    if current_user.id not in active_rooms[room_id]:
        active_rooms[room_id].append(current_user.id)
    
    # Get other participant info
    other_participant_id = session.attachee_id if current_user.id == session.assessor_id else session.assessor_id
    other_participant = User.query.get(other_participant_id)
    
    # Notify others in the room
    emit('user_joined', {
        'user_id': current_user.id,
        'username': current_user.username,
        'participants': active_rooms[room_id]
    }, room=room_id)
    
    # Send room info to the user
    emit('room_joined', {
        'room_id': room_id,
        'session_title': session.title,
        'other_participant': {
            'id': other_participant.id,
            'username': other_participant.username
        },
        'participants': active_rooms[room_id]
    })

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data.get('room_id')
    if not room_id:
        return
    
    leave_room(room_id)
    
    # Remove user from room participants
    if room_id in active_rooms and current_user.id in active_rooms[room_id]:
        active_rooms[room_id].remove(current_user.id)
        # Notify others in the room
        emit('user_left', {'user_id': current_user.id, 'username': current_user.username}, room=room_id)
        # If room is empty, remove it
        if not active_rooms[room_id]:
            del active_rooms[room_id]

# WebRTC signaling
@socketio.on('offer')
def handle_offer(data):
    room_id = data.get('room_id')
    if not room_id or room_id not in active_rooms:
        return
    
    # Forward the offer to others in the room
    emit('offer', {
        'sdp': data.get('sdp'),
        'user_id': current_user.id
    }, room=room_id, include_self=False)

@socketio.on('answer')
def handle_answer(data):
    room_id = data.get('room_id')
    if not room_id or room_id not in active_rooms:
        return
    
    # Forward the answer to others in the room
    emit('answer', {
        'sdp': data.get('sdp'),
        'user_id': current_user.id
    }, room=room_id, include_self=False)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    room_id = data.get('room_id')
    if not room_id or room_id not in active_rooms:
        return
    
    # Forward the ICE candidate to others in the room
    emit('ice_candidate', {
        'candidate': data.get('candidate'),
        'user_id': current_user.id
    }, room=room_id, include_self=False)

@socketio.on('end_call')
def handle_end_call(data):
    room_id = data.get('room_id')
    if not room_id or room_id not in active_rooms:
        return
    
    # Notify everyone in the room that the call has ended
    emit('call_ended', {'user_id': current_user.id}, room=room_id)
    
    # Update session status if needed
    session = VideoSession.query.filter_by(room_id=room_id).first()
    if session and session.status == VideoSessionStatus.SCHEDULED:
        session.status = VideoSessionStatus.COMPLETED
        session.completed_date = datetime.now()
        db.session.commit()