from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.models import User, UserRole, VideoSession, LogbookEntry
from app.main import main
from datetime import datetime

@main.route('/')
@main.route('/index')
def index():
    """Landing page route"""
    if current_user.is_authenticated:
        if current_user.role == UserRole.ATTACHEE:
            return redirect(url_for('attachee.dashboard'))
        elif current_user.role == UserRole.ASSESSOR:
            return redirect(url_for('assessor.dashboard'))
        elif current_user.role == UserRole.ORG_MANAGER:
            return redirect(url_for('org_manager.dashboard'))
        elif current_user.role == UserRole.ADMIN:
            return redirect(url_for('admin.dashboard'))
    return render_template('main/index.html', title='Welcome to AttachéPro')

@main.route('/about')
def about():
    """About page route"""
    return render_template('main/about.html', title='About AttachéPro')

@main.route('/contact')
def contact():
    """Contact page route"""
    return render_template('main/contact.html', title='Contact Us')

@main.route('/features')
def features():
    """Features page route"""
    return render_template('main/features.html', title='Features')