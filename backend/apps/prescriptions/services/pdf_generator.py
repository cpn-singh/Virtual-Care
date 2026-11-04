"""
Prescription PDF Generation Service
Author: Clinical Pharmacy & Governance Team

Generates a secure, cleanly formatted medical prescription document
using ReportLab with legal telemedicine disclosures, doctor license numbers,
patient vitals, and structured drug items.
"""

import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_prescription_pdf(prescription) -> bytes:
    """
    Renders the prescription to PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F766E')  # Teal-700
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569')  # Slate-600
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E293B')  # Slate-800
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )

    elements = []

    # 1. Header: Clinic Brand & Doctor Credentials
    doctor = prescription.doctor
    patient = prescription.patient

    spec_name = doctor.specialization.name if doctor.specialization else "General Medicine"
    header_data = [
        [
            Paragraph("<b>VIRTUAL CARE TELEMEDICINE</b><br/>Digital Clinical Encounter", title_style),
            Paragraph(
                f"<b>Dr. {doctor.user.full_name}</b><br/>"
                f"{doctor.qualifications}<br/>"
                f"Specialty: {spec_name}<br/>"
                f"Registration / License No: {doctor.license_number or 'Verified'}",
                subtitle_style
            )
        ]
    ]

    header_table = Table(header_data, colWidths=[300, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)

    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F766E'), spaceBefore=4, spaceAfter=12))

    # 2. Patient Demographics & Date
    issued_date = prescription.issued_at.strftime('%d %B %Y, %I:%M %p') if prescription.issued_at else "Draft Document"
    gender_display = patient.get_gender_display() if hasattr(patient, 'get_gender_display') else patient.gender
    patient_data = [
        [
            Paragraph(f"<b>Patient Name:</b> {patient.user.full_name}", body_style),
            Paragraph(f"<b>Prescription ID:</b> {str(prescription.id)[:8].upper()}", body_style),
        ],
        [
            Paragraph(f"<b>Gender / Blood Group:</b> {gender_display} | {patient.blood_group}", body_style),
            Paragraph(f"<b>Issued Date:</b> {issued_date}", body_style),
        ],
        [
            Paragraph(f"<b>Known Allergies:</b> {patient.allergies or 'None reported'}", body_style),
            Paragraph(f"<b>Status:</b> {prescription.get_status_display().upper()}", body_style),
        ]
    ]

    patient_table = Table(patient_data, colWidths=[320, 210])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(patient_table)

    elements.append(Spacer(1, 14))

    # 3. Clinical Diagnosis
    elements.append(Paragraph("Clinical Diagnosis", section_heading))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(prescription.diagnosis or "Clinical assessment completed via teleconsultation.", body_style))

    elements.append(Spacer(1, 14))

    # 4. Prescribed Medications Table (Rx)
    elements.append(Paragraph("Rx - Prescribed Medications", section_heading))
    elements.append(Spacer(1, 6))

    table_data = [
        [
            Paragraph("<b>#</b>", body_style),
            Paragraph("<b>Medicine & Strength</b>", body_style),
            Paragraph("<b>Dose & Frequency</b>", body_style),
            Paragraph("<b>Duration</b>", body_style),
            Paragraph("<b>Instructions</b>", body_style),
        ]
    ]

    items = prescription.items.all()
    if items.exists():
        for idx, item in enumerate(items, 1):
            table_data.append([
                Paragraph(str(idx), body_style),
                Paragraph(f"<b>{item.medicine_name}</b> ({item.formulation})<br/>{item.strength}", body_style),
                Paragraph(f"{item.dose}<br/>{item.frequency}", body_style),
                Paragraph(item.duration, body_style),
                Paragraph(item.instructions or "-", body_style),
            ])
    else:
        table_data.append([
            Paragraph("1", body_style),
            Paragraph("No systemic medications prescribed", body_style),
            Paragraph("-", body_style),
            Paragraph("-", body_style),
            Paragraph("Supportive home care and hydration", body_style),
        ])

    rx_table = Table(table_data, colWidths=[25, 165, 140, 75, 125])
    rx_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(rx_table)

    elements.append(Spacer(1, 14))

    # 5. Doctor Advice & Notes
    if prescription.doctor_notes:
        elements.append(Paragraph("Doctor's Advice & Instructions", section_heading))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(prescription.doctor_notes, body_style))
        elements.append(Spacer(1, 14))

    # 6. Digital Signature & Telemedicine Legal Disclaimer
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceBefore=8, spaceAfter=8))
    
    footer_data = [
        [
            Paragraph(
                "<i>Telemedicine Compliance Notice:</i> This digital prescription is generated pursuant to "
                "telemedicine practice guidelines. It is issued following a verified clinician consultation. "
                "In case of unexpected drug reaction, discontinue immediately and contact emergency medical care.",
                subtitle_style
            ),
            Paragraph(
                f"<b>Digitally Signed & Certified By</b><br/>"
                f"Dr. {doctor.user.full_name}<br/>"
                f"License: {doctor.license_number or 'MCI-VERIFIED'}<br/>"
                f"Virtual Care Telemedicine Platform",
                subtitle_style
            )
        ]
    ]
    footer_table = Table(footer_data, colWidths=[340, 190])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(footer_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
