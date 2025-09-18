from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app import db
from app.models import User, AttacheeProfile, Organization, LogbookEntry, FileUpload, VideoSession
from app.models import UserRole, LogbookStatus, VideoSessionStatus
from app.assessor.forms import FeedbackForm, VideoSessionForm, AttacheeSearchForm
from app.assessor import assessor
from app.utils.decorators import role_required
from datetime import datetime, timedelta
from sqlalchemy import or_

@assessor.route('/dashboard')
@login_required
@role_required(UserRole.ASSESSOR)
def dashboard():
    # Get counts for various metrics
    attachee_count = User.query.filter_by(role=UserRole.ATTACHEE).count()
    pending_logbooks = LogbookEntry.query.filter_by(status=LogbookStatus.SUBMITTED).count()
    upcoming_sessions = VideoSession.query.filter_by(
        assessor_id=current_user.id,
        status=VideoSessionStatus.SCHEDULED
    ).filter(VideoSession.start_time >= datetime.now()).count()
    
    # Get recent logbook entries pending review
    recent_entries = LogbookEntry.query.filter_by(status=LogbookStatus.SUBMITTED)\
                                .order_by(LogbookEntry.created_at.desc()).limit(5).all()
    
    # Get upcoming video sessions
    upcoming_video_sessions = VideoSession.query.filter_by(
        assessor_id=current_user.id,
        status=VideoSessionStatus.SCHEDULED
    ).filter(VideoSession.start_time >= datetime.now())\
     .order_by(VideoSession.start_time).limit(5).all()
    
    return render_template('assessor/dashboard.html',
                          title='Assessor Dashboard',
                          attachee_count=attachee_count,
                          pending_logbooks=pending_logbooks,
                          upcoming_sessions=upcoming_sessions,
                          recent_entries=recent_entries,
                          upcoming_video_sessions=upcoming_video_sessions)

@assessor.route('/attachees')
@login_required
@role_required(UserRole.ASSESSOR)
def attachees():
    form = AttacheeSearchForm()
    page = request.args.get('page', 1, type=int)
    
    # Base query for attachees
    query = User.query.filter_by(role=UserRole.ATTACHEE)
    
    # Apply search filter if provided
    search = request.args.get('search', '')
    if search:
        # Join with profile to search by name or organization
        query = query.join(AttacheeProfile).join(Organization, AttacheeProfile.organization_id == Organization.id, isouter=True)\
                    .filter(or_(
                        User.username.contains(search),
                        User.email.contains(search),
                        AttacheeProfile.first_name.contains(search),
                        AttacheeProfile.last_name.contains(search),
                        Organization.name.contains(search)
                    ))
    
    # Paginate results
    attachees = query.paginate(page=page, per_page=10)
    
    return render_template('assessor/attachees.html',
                          title='Manage Attachees',
                          attachees=attachees,
                          form=form,
                          search=search)

@assessor.route('/attachee/<int:attachee_id>')
@login_required
@role_required(UserRole.ASSESSOR)
def view_attachee(attachee_id):
    attachee = User.query.filter_by(id=attachee_id, role=UserRole.ATTACHEE).first_or_404()
    profile = AttacheeProfile.query.filter_by(user_id=attachee_id).first_or_404()
    
    # Get organization if available
    organization = None
    if profile.organization_id:
        organization = Organization.query.get(profile.organization_id)
    
    # Get recent logbook entries
    recent_entries = LogbookEntry.query.filter_by(user_id=attachee_id)\
                                .order_by(LogbookEntry.date.desc()).limit(5).all()
    
    # Get recent file uploads
    recent_uploads = FileUpload.query.filter_by(user_id=attachee_id)\
                              .order_by(FileUpload.upload_date.desc()).limit(5).all()
    
    return render_template('assessor/view_attachee.html',
                          title=f'Attachee: {attachee.username}',
                          attachee=attachee,
                          profile=profile,
                          organization=organization,
                          recent_entries=recent_entries,
                          recent_uploads=recent_uploads)

@assessor.route('/logbooks')
@login_required
@role_required(UserRole.ASSESSOR)
def logbooks():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    # Base query for logbook entries
    query = LogbookEntry.query
    
    # Apply status filter if provided
    if status_filter != 'all':
        try:
            status = LogbookStatus[status_filter.upper()]
            query = query.filter_by(status=status)
        except (KeyError, AttributeError):
            # Invalid status, ignore filter
            pass
    
    # Order by date and paginate
    entries = query.order_by(LogbookEntry.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('assessor/logbooks.html',
                          title='Review Logbooks',
                          entries=entries,
                          status_filter=status_filter)

@assessor.route('/logbook/<int:entry_id>', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ASSESSOR)
def review_logbook(entry_id):
    entry = LogbookEntry.query.get_or_404(entry_id)
    attachee = User.query.get_or_404(entry.user_id)
    
    form = FeedbackForm()
    if form.validate_on_submit():
        entry.assessor_feedback = form.feedback.data
        entry.status = LogbookStatus[form.status.data]
        entry.assessor_approved_by = current_user.id
        entry.assessor_approved_at = datetime.now()
        
        db.session.commit()
        flash('Your feedback has been submitted.', 'success')
        return redirect(url_for('assessor.logbooks'))
    
    return render_template('assessor/review_logbook.html',
                          title=f'Review: {entry.title}',
                          entry=entry,
                          attachee=attachee,
                          form=form)

@assessor.route('/video-sessions')
@login_required
@role_required(UserRole.ASSESSOR)
def video_sessions():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    # Base query for video sessions
    query = VideoSession.query.filter_by(assessor_id=current_user.id)
    
    # Apply status filter if provided
    if status_filter != 'all':
        try:
            status = VideoSessionStatus[status_filter.upper()]
            query = query.filter_by(status=status)
        except (KeyError, AttributeError):
            # Invalid status, ignore filter
            pass
    
    # Order by start_time instead of scheduled_date
    sessions = query.order_by(VideoSession.start_time.desc()).paginate(page=page, per_page=10)
    
    return render_template('assessor/video_sessions.html',
                          title='Video Sessions',
                          sessions=sessions,
                          status_filter=status_filter)

@assessor.route('/schedule-session/<int:attachee_id>', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ASSESSOR)
def schedule_session(attachee_id):
    attachee = User.query.filter_by(id=attachee_id, role=UserRole.ATTACHEE).first_or_404()
    
    form = VideoSessionForm()
    if form.validate_on_submit():
        # Parse date and time
        session_date = form.date.data
        try:
            hours, minutes = map(int, form.time.data.split(':'))
            session_datetime = datetime.combine(session_date, datetime.min.time()) + timedelta(hours=hours, minutes=minutes)
            
            # Create video session using start_time instead of scheduled_date
            session = VideoSession(
                title=form.title.data,
                start_time=session_datetime,
                end_time=session_datetime + timedelta(minutes=int(form.duration.data)),
                description=form.notes.data,
                scheduled_date=session_datetime,
                duration_minutes=int(form.duration.data),
                notes=form.notes.data,
                status=VideoSessionStatus.SCHEDULED,
                assessor_id=current_user.id,
                attachee_id=attachee_id
            )
            
            db.session.add(session)
            db.session.commit()
            
            flash(f'Video session scheduled with {attachee.username}.', 'success')
            return redirect(url_for('assessor.video_sessions'))
        except ValueError:
            flash('Invalid time format. Please use HH:MM format.', 'danger')
    
    return render_template('assessor/schedule_session.html',
                          title=f'Schedule Session with {attachee.username}',
                          attachee=attachee,
                          form=form)

@assessor.route('/video-session/<int:session_id>')
@login_required
@role_required(UserRole.ASSESSOR)
def view_session(session_id):
    session = VideoSession.query.filter_by(id=session_id, assessor_id=current_user.id).first_or_404()
    attachee = User.query.get_or_404(session.attachee_id)
    
    return render_template('assessor/view_session.html',
                          title=f'Session: {session.title}',
                          session=session,
                          attachee=attachee)

@assessor.route('/video-session/<int:session_id>/cancel', methods=['POST'])
@login_required
@role_required(UserRole.ASSESSOR)
def cancel_session(session_id):
    session = VideoSession.query.filter_by(id=session_id, assessor_id=current_user.id).first_or_404()
    
    # Only allow cancellation of scheduled sessions
    if session.status != VideoSessionStatus.SCHEDULED:
        flash('Only scheduled sessions can be cancelled.', 'warning')
        return redirect(url_for('assessor.view_session', session_id=session.id))
    
    session.status = VideoSessionStatus.CANCELLED
    db.session.commit()
    
    flash('The video session has been cancelled.', 'success')
    return redirect(url_for('assessor.video_sessions'))

@assessor.route('/video-session/<int:session_id>/complete', methods=['POST'])
@login_required
@role_required(UserRole.ASSESSOR)
def complete_session(session_id):
    session = VideoSession.query.filter_by(id=session_id, assessor_id=current_user.id).first_or_404()
    
    # Only allow completion of scheduled sessions
    if session.status != VideoSessionStatus.SCHEDULED:
        flash('Only scheduled sessions can be marked as completed.', 'warning')
        return redirect(url_for('assessor.view_session', session_id=session.id))
    
    session.status = VideoSessionStatus.COMPLETED
    session.completed_date = datetime.now()
    db.session.commit()
    
    flash('The video session has been marked as completed.', 'success')
    return redirect(url_for('assessor.video_sessions'))