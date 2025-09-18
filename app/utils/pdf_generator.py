from flask import current_app
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
from datetime import datetime

def generate_logbook_report(logbook_entries, attachee):
    """
    Generate a PDF report for logbook entries
    
    Args:
        logbook_entries: List of LogbookEntry objects
        attachee: User object representing the attachee
    
    Returns:
        Path to the generated PDF file
    """
    # Create a filename for the report
    filename = f"logbook_report_{attachee.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Create the PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Add title
    title_style = styles['Heading1']
    title = Paragraph(f"Logbook Report - {attachee.name}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add attachee information
    info_style = styles['Normal']
    elements.append(Paragraph(f"<b>Attachee:</b> {attachee.name}", info_style))
    
    if hasattr(attachee, 'attachee_profile') and attachee.attachee_profile:
        profile = attachee.attachee_profile
        if profile.organization:
            elements.append(Paragraph(f"<b>Organization:</b> {profile.organization.name}", info_style))
        if profile.department:
            elements.append(Paragraph(f"<b>Department:</b> {profile.department}", info_style))
    
    elements.append(Paragraph(f"<b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d')}", info_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add logbook entries
    elements.append(Paragraph("Logbook Entries", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    for entry in logbook_entries:
        # Entry header
        elements.append(Paragraph(f"<b>Week {entry.week_number}</b> ({entry.start_date} to {entry.end_date})", styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Entry details
        elements.append(Paragraph(f"<b>Tasks:</b> {entry.tasks}", info_style))
        elements.append(Paragraph(f"<b>Skills Gained:</b> {entry.skills_gained}", info_style))
        
        if entry.challenges:
            elements.append(Paragraph(f"<b>Challenges:</b> {entry.challenges}", info_style))
        
        elements.append(Paragraph(f"<b>Hours Worked:</b> {entry.hours_worked}", info_style))
        elements.append(Paragraph(f"<b>Status:</b> {entry.status.value}", info_style))
        
        if entry.grade:
            elements.append(Paragraph(f"<b>Grade:</b> {entry.grade}", info_style))
        
        elements.append(Spacer(1, 0.2*inch))
    
    # Build the PDF
    doc.build(elements)
    
    return filename

def generate_user_report(users, title="User Report"):
    """
    Generate a PDF report for users
    
    Args:
        users: List of User objects
        title: Title of the report
    
    Returns:
        Path to the generated PDF file
    """
    # Create a filename for the report
    filename = f"user_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Create the PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Add title
    title_style = styles['Heading1']
    title_paragraph = Paragraph(title, title_style)
    elements.append(title_paragraph)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add report date
    info_style = styles['Normal']
    elements.append(Paragraph(f"<b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d')}", info_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Create table data
    data = [["Name", "Email", "Role", "Organization", "Created At"]]
    
    for user in users:
        org_name = user.organization.name if user.organization else "N/A"
        data.append([
            user.name,
            user.email,
            user.role.value,
            org_name,
            user.created_at.strftime('%Y-%m-%d')
        ])
    
    # Create table
    table = Table(data, colWidths=[1.5*inch, 2*inch, 1*inch, 1.5*inch, 1*inch])
    
    # Add style to table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build the PDF
    doc.build(elements)
    
    return filename

def generate_organization_report(organizations):
    """
    Generate a PDF report for organizations
    
    Args:
        organizations: List of Organization objects
    
    Returns:
        Path to the generated PDF file
    """
    # Create a filename for the report
    filename = f"organization_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Create the PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Add title
    title_style = styles['Heading1']
    title = Paragraph("Organization Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add report date
    info_style = styles['Normal']
    elements.append(Paragraph(f"<b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d')}", info_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Create table data
    data = [["Name", "Address", "Contact Email", "Number of Users"]]
    
    for org in organizations:
        user_count = len(org.users) if org.users else 0
        data.append([
            org.name,
            org.address or "N/A",
            org.contact_email or "N/A",
            str(user_count)
        ])
    
    # Create table
    table = Table(data, colWidths=[1.5*inch, 2*inch, 2*inch, 1.5*inch])
    
    # Add style to table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build the PDF
    doc.build(elements)
    
    return filename