from flask import render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.models import User, AttacheeProfile, Organization, LogbookEntry, FileUpload, LogbookStatus, VideoSession, VideoSessionStatus
from app.attachee.forms import ProfileForm, LogbookEntryForm, FileUploadForm
from app.attachee import attachee_bp
from app.utils.decorators import role_required
from app.models import UserRole
import os
from datetime import datetime
import uuid

@attachee_bp.route('/dashboard')
@login_required
@role_required(UserRole.ATTACHEE)
def dashboard():
    # Get attachee profile
    profile = AttacheeProfile.query.filter_by(user_id=current_user.id).first()
    
    # Get recent logbook entries
    recent_entries = LogbookEntry.query.filter_by(attachee_id=current_user.id)\
                                .order_by(LogbookEntry.created_at.desc()).limit(5).all()
    
    # Get recent file uploads
    recent_uploads = FileUpload.query.filter_by(attachee_id=current_user.id)\
                              .order_by(FileUpload.uploaded_at.desc()).limit(5).all()
    
    # Get profile completion percentage
    completion = calculate_profile_completion(profile) if profile else 0
    
    # Get upcoming deadlines or notifications
    # This would be expanded in a real application
    
    return render_template('attachee/dashboard.html', 
                           title='Attachee Dashboard',
                           profile=profile,
                           recent_entries=recent_entries,
                           recent_uploads=recent_uploads,
                           completion=completion)

def calculate_profile_completion(profile):
    """Calculate the percentage of profile completion"""
    if not profile:
        return 0
        
    fields = ['university', 'course', 'year_of_study', 'department', 
              'start_date', 'end_date', 'skills', 'bio']
    
    completed = sum(1 for field in fields if getattr(profile, field))
    return int((completed / len(fields)) * 100)

@attachee_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ATTACHEE)
def profile():
    profile = AttacheeProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = AttacheeProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    form = ProfileForm()
    
    if form.validate_on_submit():
        profile.university = form.university.data or 'Not specified'
        profile.course = form.course.data or 'Not specified'
        profile.year_of_study = form.year_of_study.data
        profile.department = form.department.data or 'Not specified'
        profile.start_date = form.start_date.data
        profile.end_date = form.end_date.data
        profile.skills = form.skills.data or 'None listed'
        profile.bio = form.bio.data or 'No bio provided'
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('attachee.profile'))
    
    elif request.method == 'GET':
        form.university.data = profile.university
        form.course.data = profile.course
        form.year_of_study.data = profile.year_of_study
        form.start_date.data = profile.start_date
        form.end_date.data = profile.end_date
        form.bio.data = profile.bio
    
    completion = calculate_profile_completion(profile)
    return render_template('attachee/profile.html', title='My Profile', form=form, completion=completion)

@attachee_bp.route('/logbook')
@login_required
@role_required(UserRole.ATTACHEE)
def logbook():
    page = request.args.get('page', 1, type=int)
    entries = LogbookEntry.query.filter_by(attachee_id=current_user.id)\
                         .order_by(LogbookEntry.created_at.desc())\
                         .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('attachee/logbook.html', 
                           title='My Logbook', 
                           entries=entries)

@attachee_bp.route('/logbook/new', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ATTACHEE)
def new_logbook_entry():
    form = LogbookEntryForm()
    if form.validate_on_submit():
        entry = LogbookEntry(
            attachee_id=current_user.id,
            week_number=form.week_number.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            tasks=form.tasks.data,
            skills_gained=form.skills_gained.data,
            challenges=form.challenges.data or 'None reported',
            hours_worked=form.hours_worked.data,
            status=LogbookStatus.DRAFT
        )
        db.session.add(entry)
        db.session.commit()
        flash('Your logbook entry has been created!', 'success')
        return redirect(url_for('attachee.logbook'))
    
    # Set default values for new entries
    if request.method == 'GET':
        form.start_date.data = datetime.today().date()
        # Calculate next week number
        last_entry = LogbookEntry.query.filter_by(attachee_id=current_user.id)\
                                     .order_by(LogbookEntry.week_number.desc()).first()
        form.week_number.data = (last_entry.week_number + 1) if last_entry else 1
    
    return render_template('attachee/create_logbook.html', 
                           title='New Logbook Entry', 
                           form=form, 
                           legend='New Logbook Entry')

@attachee_bp.route('/logbook/<int:entry_id>')
@login_required
@role_required(UserRole.ATTACHEE)
def view_logbook_entry(entry_id):
    entry = LogbookEntry.query.get_or_404(entry_id)
    if entry.attachee_id != current_user.id:
        flash('You do not have permission to view this entry.', 'danger')
        return redirect(url_for('attachee.logbook'))
    
    return render_template('attachee/view_logbook.html', title=f'Week {entry.week_number}', entry=entry)

@attachee_bp.route('/logbook/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ATTACHEE)
def edit_logbook_entry(entry_id):
    entry = LogbookEntry.query.get_or_404(entry_id)
    if entry.attachee_id != current_user.id:
        flash('You do not have permission to edit this entry.', 'danger')
        return redirect(url_for('attachee.logbook'))
    
    # Don't allow editing of approved or rejected entries
    if entry.status not in [LogbookStatus.DRAFT]:
        flash('You can only edit draft entries.', 'warning')
        return redirect(url_for('attachee.view_logbook_entry', entry_id=entry.id))
    
    form = LogbookEntryForm()
    if form.validate_on_submit():
        entry.week_number = form.week_number.data
        entry.start_date = form.start_date.data
        entry.end_date = form.end_date.data
        entry.tasks = form.tasks.data
        entry.skills_gained = form.skills_gained.data
        entry.challenges = form.challenges.data or 'None reported'
        entry.hours_worked = form.hours_worked.data
        # Keep status as DRAFT when editing
        entry.status = LogbookStatus.DRAFT
        db.session.commit()
        flash('Your logbook entry has been updated!', 'success')
        return redirect(url_for('attachee.view_logbook_entry', entry_id=entry.id))
    
    elif request.method == 'GET':
        form.week_number.data = entry.week_number
        form.start_date.data = entry.start_date
        form.end_date.data = entry.end_date
        form.tasks.data = entry.tasks
        form.skills_gained.data = entry.skills_gained
        form.challenges.data = entry.challenges
        form.hours_worked.data = entry.hours_worked
    
    return render_template('attachee/create_logbook.html', 
                           title='Edit Logbook Entry', 
                           form=form, 
                           legend='Edit Logbook Entry')

@attachee_bp.route('/logbook/<int:entry_id>/submit', methods=['POST'])
@login_required
@role_required(UserRole.ATTACHEE)
def submit_logbook_entry(entry_id):
    entry = LogbookEntry.query.get_or_404(entry_id)
    if entry.attachee_id != current_user.id:
        flash('You do not have permission to submit this entry.', 'danger')
        return redirect(url_for('attachee.logbook'))
    
    if entry.status != LogbookStatus.DRAFT:
        flash('Only draft entries can be submitted.', 'warning')
        return redirect(url_for('attachee.view_logbook_entry', entry_id=entry.id))
    
    entry.status = LogbookStatus.SUBMITTED
    db.session.commit()
    flash('Your logbook entry has been submitted for review!', 'success')
    return redirect(url_for('attachee.logbook'))

@attachee_bp.route('/files')
@login_required
@role_required(UserRole.ATTACHEE)
def files():
    page = request.args.get('page', 1, type=int)
    files = FileUpload.query.filter_by(attachee_id=current_user.id)\
                      .order_by(FileUpload.uploaded_at.desc())\
                      .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('attachee/files.html', 
                           title='My Files', 
                           files=files)

@attachee_bp.route('/files/upload', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ATTACHEE)
def upload_file():
    form = FileUploadForm()
    if form.validate_on_submit():
        if form.file.data:
            # Generate a unique filename
            original_filename = secure_filename(form.file.data.filename)
            file_ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            
            # Ensure upload directory exists
            upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # Save the file
            file_path = os.path.join(upload_dir, unique_filename)
            form.file.data.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create database entry
            file_upload = FileUpload(
                attachee_id=current_user.id,
                filename=unique_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_type=form.file_type.data or 'other',
                file_size=file_size,
                description=form.description.data or 'No description provided'
            )
            db.session.add(file_upload)
            db.session.commit()
            
            flash('Your file has been uploaded!', 'success')
            return redirect(url_for('attachee.files'))
        else:
            flash('Please select a file to upload.', 'warning')
    
    return render_template('attachee/upload_file.html', 
                           title='Upload File', 
                           form=form)

@attachee_bp.route('/files/<int:file_id>')
@login_required
@role_required(UserRole.ATTACHEE)
def download_file(file_id):
    file = FileUpload.query.get_or_404(file_id)
    if file.attachee_id != current_user.id:
        flash('You do not have permission to download this file.', 'danger')
        return redirect(url_for('attachee.files'))
    
    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return send_from_directory(
        upload_dir,
        file.filename,
        as_attachment=True,
        download_name=file.original_filename
    )

@attachee_bp.route('/files/<int:file_id>/delete', methods=['POST'])
@login_required
@role_required(UserRole.ATTACHEE)
def delete_file(file_id):
    file = FileUpload.query.get_or_404(file_id)
    if file.attachee_id != current_user.id:
        flash('You do not have permission to delete this file.', 'danger')
        return redirect(url_for('attachee.files'))
    
    # Delete the file from the filesystem
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {e}")
    
    # Delete the database entry
    db.session.delete(file)
    db.session.commit()
    
    flash('Your file has been deleted!', 'success')
    return redirect(url_for('attachee.files'))

@attachee_bp.route('/video-sessions')
@login_required
@role_required(UserRole.ATTACHEE)
def video_sessions():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    # Base query for video sessions
    query = VideoSession.query.filter_by(attachee_id=current_user.id)
    
    # Apply status filter if provided
    if status_filter != 'all':
        try:
            status = VideoSessionStatus[status_filter.upper()]
            query = query.filter_by(status=status)
        except (KeyError, AttributeError):
            # Invalid status, ignore filter
            pass
    
    # Order by start time and paginate
    sessions = query.order_by(VideoSession.start_time.desc()).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('attachee/video_sessions.html',
                          title='My Video Sessions',
                          sessions=sessions,
                          status_filter=status_filter)

@attachee_bp.route('/video-session/<int:session_id>')
@login_required
@role_required(UserRole.ATTACHEE)
def view_session(session_id):
    session = VideoSession.query.filter_by(id=session_id, attachee_id=current_user.id).first_or_404()
    assessor = User.query.get_or_404(session.assessor_id)
    
    return render_template('attachee/view_session.html',
                          title=f'Session: {session.title}',
                          session=session,
                          assessor=assessor)

@attachee_bp.route('/notifications')
@login_required
@role_required(UserRole.ATTACHEE)
def notifications():
    page = request.args.get('page', 1, type=int)
    notifications = current_user.notifications.order_by(
        db.desc('created_at')).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('attachee/notifications.html',
                          title='My Notifications',
                          notifications=notifications)

@attachee_bp.route('/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
@role_required(UserRole.ATTACHEE)
def mark_notification_read(notification_id):
    notification = current_user.notifications.filter_by(id=notification_id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return redirect(url_for('attachee.notifications'))