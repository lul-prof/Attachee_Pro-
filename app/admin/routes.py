from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app import db
from app.models import User, Organization, AttacheeProfile, LogbookEntry, VideoSession, UserRole
from app.admin import admin
from app.admin.forms import OrganizationForm, UserForm, UserSearchForm
from app.utils.decorators import role_required
from datetime import datetime
from sqlalchemy import func

@admin.route('/dashboard')
@login_required
@role_required(UserRole.ADMIN)
def dashboard():
    """Admin dashboard route"""
    # Get counts for various metrics
    user_count = User.query.count()
    attachee_count = User.query.filter_by(role=UserRole.ATTACHEE).count()
    assessor_count = User.query.filter_by(role=UserRole.ASSESSOR).count()
    org_manager_count = User.query.filter_by(role=UserRole.ORG_MANAGER).count()
    org_count = Organization.query.count()
    logbook_count = LogbookEntry.query.count()
    video_session_count = VideoSession.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent organizations
    recent_orgs = Organization.query.order_by(Organization.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                          title='Admin Dashboard',
                          user_count=user_count,
                          attachee_count=attachee_count,
                          assessor_count=assessor_count,
                          org_manager_count=org_manager_count,
                          org_count=org_count,
                          logbook_count=logbook_count,
                          video_session_count=video_session_count,
                          recent_users=recent_users,
                          recent_orgs=recent_orgs)

@admin.route('/users')
@login_required
@role_required(UserRole.ADMIN)
def users():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    search_form = UserSearchForm()
    query = User.query
    
    # Apply search filter if provided
    search_term = request.args.get('search', '')
    if search_term:
        search_form.search.data = search_term
        query = query.filter(User.username.ilike(f'%{search_term}%') | 
                            User.email.ilike(f'%{search_term}%'))
    
    # Apply role filter if provided
    role_filter = request.args.get('role', '')
    if role_filter and role_filter in [role.name for role in UserRole]:
        query = query.filter(User.role == UserRole[role_filter])
    
    # Paginate results
    users = query.order_by(User.username).paginate(page=page, per_page=20)
    
    return render_template('admin/users.html',
                          title='Manage Users',
                          users=users,
                          search_form=search_form,
                          current_role=role_filter)

@admin.route('/user/<int:user_id>')
@login_required
@role_required(UserRole.ADMIN)
def view_user(user_id):
    """View user details"""
    user = User.query.get_or_404(user_id)
    profile = None
    if user.role == UserRole.ATTACHEE:
        profile = AttacheeProfile.query.filter_by(user_id=user.id).first()
    
    return render_template('admin/view_user.html',
                          title=f'User: {user.username}',
                          user=user,
                          profile=profile
                        ,UserRole=UserRole)

@admin.route('/user/create', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ADMIN)
def create_user():
    """Create a new user"""
    form = UserForm()
    
    if form.validate_on_submit():
        user = User(username=form.username.data,
                   email=form.email.data,
                   role=UserRole[form.role.data])
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Create attachee profile if needed
        if user.role == UserRole.ATTACHEE:
            profile = AttacheeProfile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()
        
        flash(f'User {user.username} has been created.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/create_user.html',
                          title='Create User',
                          form=form,UserRole=UserRole)