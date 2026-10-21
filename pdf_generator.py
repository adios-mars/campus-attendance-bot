import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_attendance_pdf(
    course_name: str,
    course_code: str,
    instructor_name: str,
    department: str,
    year_semester: str,
    date_str: str,
    time_str: str,
    attendance_rows: list,
    output_filename: str = "attendance_report.pdf"
):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=15,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#111827"),
        fontName="Helvetica-Bold"
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#4B5563"),
        fontName="Helvetica"
    )
    
    
    story.append(Paragraph("DIRE DAWA UNIVERSITY", title_style))
    story.append(Paragraph(f"DEPARTMENT OF {department.upper()}", subtitle_style))
    story.append(Paragraph("OFFICIAL ATTENDANCE DOSSIER", subtitle_style))
    story.append(Spacer(1, 12))
    
    
    total_enrolled = len(attendance_rows)
    total_present = sum(1 for row in attendance_rows if row[2] == "PRESENT")
    total_absent = total_enrolled - total_present
    
    meta_data = [
        [
            Paragraph(f"<b>Course:</b> {course_name} ({course_code})", styles['Normal']),
            Paragraph(f"<b>Academic Term:</b> {year_semester}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Instructor:</b> {instructor_name}", styles['Normal']),
            Paragraph(f"<b>Date:</b> {date_str} at {time_str}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Tally:</b> {total_present} Present / {total_absent} Absent", styles['Normal']),
            Paragraph(f"<b>Total Enrolled:</b> {total_enrolled} Students", styles['Normal'])
        ]
    ]
    
    meta_table = Table(meta_data, colWidths=[3.6 * inch, 3.6 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#D1D5DB")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))
    
   
    table_data = [
        ["No.", "Student ID", "Full Legal Name", "Status", "Verification Method"]
    ]
    
    for idx, (stu_id, name, status, method) in enumerate(attendance_rows, 1):
        table_data.append([str(idx), stu_id, name, status, method])
        
    col_widths = [0.5 * inch, 1.4 * inch, 2.7 * inch, 1.1 * inch, 1.5 * inch]
    roster_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    roster_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F2937")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ])
    
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            roster_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F9FAFB"))
        status = table_data[i][3]
        if status == "PRESENT":
            roster_style.add('TEXTCOLOR', (3, i), (3, i), colors.HexColor("#065F46"))
            roster_style.add('FONTNAME', (3, i), (3, i), 'Helvetica-Bold')
        else:
            roster_style.add('TEXTCOLOR', (3, i), (3, i), colors.HexColor("#991B1B"))
            roster_style.add('FONTNAME', (3, i), (3, i), 'Helvetica-Bold')
            
    roster_table.setStyle(roster_style)
    story.append(roster_table)
    story.append(Spacer(1, 20))
    
    
    sig_data = [
        [
            Paragraph("<b>Instructor Signature:</b> ___________________________", styles['Normal']),
            Paragraph("<b>Department Approval:</b> ___________________________", styles['Normal'])
        ],
        [
            Paragraph("<b>Date:</b> ___________________________", styles['Normal']),
            Paragraph("<b>Date:</b> ___________________________", styles['Normal'])
        ]
    ]
    sig_table = Table(sig_data, colWidths=[3.6 * inch, 3.6 * inch])
    sig_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    return output_filename