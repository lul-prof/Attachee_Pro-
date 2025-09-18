from flask import current_app
import os
import secrets
from datetime import datetime, timedelta
from app.models import LogbookEntry, VideoSession, User, UserRole

def calculate_profile_completion(profile):
    """
    Calculate the completion percentage of an attachee profile
    
    Args:
        profile: AttacheeProfile object
    
    Returns:
        Completion percentage (0-100)
    """
    if not profile:
        return 0
        
    # Define required fields
    required_fields = [
        profile.first_name,
        profile.last_name,
        profile.phone,
        profile.organization_id,
        profile.department,
        profile.course,
        profile.start_date,
        profile.end_date
    ]
    
    # Count completed fields
    completed = sum(1 for field in required_fields if field)
    
    # Calculate percentage
    return int((completed / len(required_fields)) * 100)

def get_upcoming_deadlines(user, days=7):
    """
    Get upcoming deadlines for a user
    
    Args:
        user: User object
        days: Number of days to look ahead
    
    Returns:
        List of upcoming deadlines (logbook entries, video sessions)
    """
    deadlines = []
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=days)
    
    if user.role == UserRole.ATTACHEE:
        # Get upcoming logbook submissions
        logbook_entries = LogbookEntry.query.filter_by(
            attachee_id=user.id,
            status='DRAFT'
        ).all()
        
        for entry in logbook_entries:
            if entry.end_date <= end_date:
                deadlines.append({
                    'type': 'logbook',
                    'id': entry.id,
                    'title': f'Week {entry.week_number} Logbook',
                    'due_date': entry.end_date
                })
        
        # Get upcoming video sessions
        video_sessions = VideoSession.query.filter_by(
            attachee_id=user.id,
            status='SCHEDULED'
        ).all()
        
        for session in video_sessions:
            session_date = session.start_time.date()
            if today <= session_date <= end_date:
                deadlines.append({
                    'type': 'video_session',
                    'id': session.id,
                    'title': session.title,
                    'due_date': session_date
                })
    
    elif user.role == UserRole.ASSESSOR:
        # Get pending logbook reviews
        logbook_entries = LogbookEntry.query.filter_by(
            status='ORG_APPROVED'
        ).join(User, LogbookEntry.attachee_id == User.id)\
        .filter(User.id.in_([a.id for a in user.supervised_attachees]))\
        .all()
        
        for entry in logbook_entries:
            deadlines.append({
                'type': 'logbook_review',
                'id': entry.id,
                'title': f'Review {entry.attachee.name}\'s Week {entry.week_number} Logbook',
                'due_date': today  # Due immediately
            })
        
        # Get upcoming video sessions
        video_sessions = VideoSession.query.filter_by(
            assessor_id=user.id,
            status='SCHEDULED'
        ).all()
        
        for session in video_sessions:
            session_date = session.start_time.date()
            if today <= session_date <= end_date:
                deadlines.append({
                    'type': 'video_session',
                    'id': session.id,
                    'title': session.title,
                    'due_date': session_date
                })
    
    elif user.role == UserRole.ORG_MANAGER:
        # Get pending logbook reviews for organization
        org_id = user.organization_id
        if org_id:
            logbook_entries = LogbookEntry.query.join(
                User, LogbookEntry.attachee_id == User.id
            ).filter(
                User.organization_id == org_id,
                LogbookEntry.status == 'SUBMITTED'
            ).all()
            
            for entry in logbook_entries:
                deadlines.append({
                    'type': 'logbook_review',
                    'id': entry.id,
                    'title': f'Review {entry.attachee.name}\'s Week {entry.week_number} Logbook',
                    'due_date': today  # Due immediately
                })
    
    # Sort deadlines by due date
    deadlines.sort(key=lambda x: x['due_date'])
    
    return deadlines

def save_file(file, upload_folder=None):
    """
    Save an uploaded file with a secure filename
    
    Args:
        file: File object from request.files
        upload_folder: Optional custom upload folder
    
    Returns:
        Tuple of (saved_filename, original_filename)
    """
    if upload_folder is None:
        upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # Ensure the upload folder exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate a secure filename
    original_filename = file.filename
    filename = secure_filename(original_filename)
    
    # Add a random token to ensure uniqueness
    filename = f"{secrets.token_hex(8)}_{filename}"
    
    # Save the file
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    return filename, original_filename