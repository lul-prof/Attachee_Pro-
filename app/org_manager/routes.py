from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app import db
from app.models import User, Organization, AttacheeProfile, LogbookEntry, UserRole, LogbookStatus
from app.org_manager import org_manager
from app.org_manager.forms import AttacheeForm, LogbookReviewForm
from app.utils.decorators import role_required
from datetime import datetime
from sqlalchemy import func

@org_manager.route('/dashboard')
@login_required
@role_required(UserRole.ORG_MANAGER)
def dashboard():
    """Organization manager dashboard route"""
    # Get counts for various metrics
    org_id = current_user.organization_id
    
    # Count users in this organization
    attachee_count = User.query.filter_by(organization_id=org_id, role=UserRole.ATTACHEE).count()
    
    # Count pending logbook entries - specify the join relationship
    pending_logbooks = LogbookEntry.query.join(
        User,
        LogbookEntry.attachee_id == User.id  # Explicitly specify the join condition
    ).filter(
        User.organization_id == org_id,
        LogbookEntry.status == LogbookStatus.SUBMITTED
    ).count()
    
    # Get recent attachees in this organization
    recent_attachees = User.query.filter_by(
        organization_id=org_id, 
        role=UserRole.ATTACHEE
    ).order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent logbook entries pending review - specify the join relationship
    recent_entries = LogbookEntry.query.join(
        User,
        LogbookEntry.attachee_id == User.id  # Explicitly specify the join condition
    ).filter(
        User.organization_id == org_id,
        LogbookEntry.status == LogbookStatus.SUBMITTED
    ).order_by(LogbookEntry.created_at.desc()).limit(5).all()  # Also fixed date to created_at
    
    return render_template('org_manager/dashboard.html',
                          title='Organization Manager Dashboard',
                          attachee_count=attachee_count,
                          pending_logbooks=pending_logbooks,
                          recent_attachees=recent_attachees,
                          recent_entries=recent_entries)

@org_manager.route('/attachees')
@login_required
@role_required(UserRole.ORG_MANAGER)
def attachees():
    """List all attachees in the organization"""
    page = request.args.get('page', 1, type=int)
    org_id = current_user.organization_id
    
    # Get all attachees in this organization
    query = User.query.filter_by(organization_id=org_id, role=UserRole.ATTACHEE)
    
    # Apply search filter if provided
    search_term = request.args.get('search', '')
    if search_term:
        query = query.filter(User.username.ilike(f'%{search_term}%') | 
                            User.email.ilike(f'%{search_term}%'))
    
    # Paginate results
    attachees = query.order_by(User.username).paginate(page=page, per_page=20)
    
    return render_template('org_manager/attachees.html',
                          title='Manage Attachees',
                          attachees=attachees,
                          search_term=search_term)

@org_manager.route('/attachee/<int:attachee_id>')
@login_required
@role_required(UserRole.ORG_MANAGER)
def view_attachee(attachee_id):
    """View attachee details"""
    org_id = current_user.organization_id
    attachee = User.query.filter_by(id=attachee_id, organization_id=org_id, role=UserRole.ATTACHEE).first_or_404()
    profile = AttacheeProfile.query.filter_by(user_id=attachee.id).first()
    
    # Get recent logbook entries
    recent_entries = LogbookEntry.query.filter_by(user_id=attachee.id)\
                                .order_by(LogbookEntry.date.desc()).limit(5).all()
    
    return render_template('org_manager/view_attachee.html',
                          title=f'Attachee: {attachee.username}',
                          attachee=attachee,
                          profile=profile,
                          recent_entries=recent_entries)

@org_manager.route('/logbooks')
@login_required
@role_required(UserRole.ORG_MANAGER)
def logbooks():
    """List all logbooks for review"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'submitted')
    org_id = current_user.organization_id
    
    # Base query for logbook entries in this organization
    query = LogbookEntry.query.join(User).filter(User.organization_id == org_id)
    
    # Apply status filter if provided
    if status_filter != 'all':
        try:
            status = LogbookStatus[status_filter.upper()]
            query = query.filter(LogbookEntry.status == status)
        except (KeyError, AttributeError):
            # Invalid status, ignore filter
            pass
    
    # Order by date and paginate
    entries = query.order_by(LogbookEntry.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('org_manager/logbooks.html',
                          title='Review Logbooks',
                          entries=entries,
                          status_filter=status_filter)

@org_manager.route('/logbook/<int:entry_id>', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ORG_MANAGER)
def review_logbook(entry_id):
    """Review a logbook entry"""
    org_id = current_user.organization_id
    
    # Get the entry and verify it belongs to an attachee in this organization
    entry = LogbookEntry.query.join(User).filter(
        LogbookEntry.id == entry_id,
        User.organization_id == org_id
    ).first_or_404()
    
    attachee = User.query.get_or_404(entry.user_id)
    
    form = LogbookReviewForm()
    if form.validate_on_submit():
        entry.org_feedback = form.feedback.data
        
        if form.status.data == 'approve':
            entry.status = LogbookStatus.ORG_APPROVED
        else:
            entry.status = LogbookStatus.ORG_REJECTED
            
        entry.org_approved_by = current_user.id
        entry.org_approved_at = datetime.now()
        
        db.session.commit()
        flash('Your review has been submitted.', 'success')
        return redirect(url_for('org_manager.logbooks'))
    
    return render_template('org_manager/review_logbook.html',
                          title=f'Review: {entry.title}',
                          entry=entry,
                          attachee=attachee,
                          form=form)

@org_manager.route('/organization')
@login_required
@role_required(UserRole.ORG_MANAGER)
def organization():
    """View organization details"""
    org_id = current_user.organization_id
    organization = Organization.query.get_or_404(org_id)
    
    # Get counts
    attachee_count = User.query.filter_by(organization_id=org_id, role=UserRole.ATTACHEE).count()
    assessor_count = User.query.filter_by(organization_id=org_id, role=UserRole.ASSESSOR).count()
    manager_count = User.query.filter_by(organization_id=org_id, role=UserRole.ORG_MANAGER).count()
    
    return render_template('org_manager/organization.html',
                          title=f'Organization: {organization.name}',
                          organization=organization,
                          attachee_count=attachee_count,
                          assessor_count=assessor_count,
                          manager_count=manager_count)