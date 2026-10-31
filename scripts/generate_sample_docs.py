"""
Script to generate 8 fictional demo college PDF documents using ReportLab.
All documents are clearly marked as 'FICTIONAL DEMO DOCUMENT FOR SMART COLLEGE ASSISTANT AI'.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_docs")
os.makedirs(DOCS_DIR, exist_ok=True)

def build_pdf(filename, title, sections):
    filepath = os.path.join(DOCS_DIR, filename)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=8
    )
    
    notice_style = ParagraphStyle(
        'DocNotice',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#dc2626'),
        alignment=1,
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0d9488'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )

    story = []
    
    story.append(Paragraph(title, title_style))
    story.append(Paragraph("[FICTIONAL DEMO DOCUMENT FOR SMART COLLEGE ASSISTANT AI - APEX INSTITUTE OF TECHNOLOGY]", notice_style))
    story.append(Spacer(1, 10))
    
    for section_title, content in sections:
        if section_title:
            story.append(Paragraph(section_title, h1_style))
        if isinstance(content, list):
            for item in content:
                if isinstance(item, list): # Table rows
                    t = Table(item, colWidths=[150, 380])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (-1,-1), 9),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                        ('TOPPADDING', (0,0), (-1,-1), 4),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 8))
                else:
                    story.append(Paragraph(f"• {item}", body_style))
        else:
            story.append(Paragraph(content, body_style))
        story.append(Spacer(1, 6))
        
    doc.build(story)
    print(f"Generated: {filepath}")

def main():
    # 1. College Handbook
    build_pdf("College_Handbook.pdf", "Apex Institute of Technology - Student Handbook & Regulations", [
        ("1. Institution Overview", "Apex Institute of Technology (AIT) was established in 2004 as an autonomous engineering institution offering undergraduate and postgraduate programs in computer science, information technology, electronics, electrical, mechanical, and civil engineering. The campus is accredited by NAAC with an 'A+' grade and NBA approved."),
        ("2. Academic Regulations & Credit System", [
            "A student must earn a minimum of 160 credits over 8 semesters to qualify for the award of B.Tech degree.",
            "Each semester consists of a minimum of 90 working days or 450 instructional hours.",
            "Continuous Internal Evaluation (CIE) carries 40% weightage, and Semester End Examination (SEE) carries 60% weightage.",
            "Grading Scale: O (Outstanding, 10 points: 90-100%), A+ (Excellent, 9 points: 80-89%), A (Very Good, 8 points: 70-79%), B+ (Good, 7 points: 60-69%), B (Above Average, 6 points: 55-59%), C (Pass, 5 points: 50-54%), F (Fail, 0 points: Below 50%).",
            "Minimum Cumulative Grade Point Average (CGPA) required for graduation is 6.00."
        ]),
        ("3. Attendance Regulations & Condonation", [
            "Students are required to maintain a minimum attendance of 75% in every registered theory and laboratory course.",
            "Condonation of shortage of attendance between 65% and 74% may be granted by the Academic Council solely on valid medical grounds or official representation of the college in university/national competitions.",
            "Medical certificates must be submitted to the Head of Department within three working days of resuming classes.",
            "A non-refundable condonation fee of Rs. 1,500 per subject applies upon Academic Council approval.",
            "Students with attendance below 65% are strictly detained and must repeat the course in the subsequent academic year."
        ]),
        ("4. Code of Conduct & Anti-Ragging Policy", [
            "Ragging in any form is strictly banned on campus, hostels, and college transport as per Supreme Court directives.",
            "Anti-Ragging Helpline: Toll-free 1800-425-9999 or email antiragging@apextech.edu.",
            "Dress Code: Formal or smart casual attire is mandatory on all instructional days. Laboratory coats and closed leather shoes are mandatory in chemistry and workshop sessions.",
            "Smartphones are strictly prohibited during lecture sessions and laboratory practicals unless instructed by faculty for learning activities."
        ])
    ])

    # 2. Academic Calendar
    build_pdf("Academic_Calendar.pdf", "Apex Institute of Technology - Academic Calendar 2026-2027", [
        ("1. Odd Semester Schedule (Semesters 1, 3, 5, 7)", [
            ["Milestone Event", "Date / Timeline"],
            ["Commencement of Classes", "August 3, 2026"],
            ["Internal Assessment Test 1 (IAT-1)", "September 21 - September 26, 2026"],
            ["Mid-Semester Academic Review & Attendance Audit", "October 5, 2026"],
            ["Internal Assessment Test 2 (IAT-2)", "November 9 - November 14, 2026"],
            ["Last Instructional Day", "November 28, 2026"],
            ["Semester Practical Examinations", "December 1 - December 8, 2026"],
            ["Semester End Theory Examinations (SEE)", "December 14 - December 30, 2026"],
            ["Winter Vacation & Faculty Evaluation", "January 2 - January 16, 2027"]
        ]),
        ("2. Even Semester Schedule (Semesters 2, 4, 6, 8)", [
            ["Milestone Event", "Date / Timeline"],
            ["Commencement of Classes", "January 18, 2027"],
            ["Annual Cultural Festival 'AURA 2027'", "February 19 - February 21, 2027"],
            ["Internal Assessment Test 1 (IAT-1)", "March 8 - March 13, 2027"],
            ["Annual Sports Meet 'AGILITY'", "March 27, 2027"],
            ["Internal Assessment Test 2 (IAT-2)", "April 19 - April 24, 2027"],
            ["Last Instructional Day", "May 8, 2027"],
            ["Semester Practical Examinations", "May 12 - May 19, 2027"],
            ["Semester End Theory Examinations", "May 24 - June 10, 2027"],
            ["Summer Internship Window", "June 15 - July 30, 2027"]
        ]),
        ("3. Official Holiday List", "The institution observes all national holidays including Independence Day (Aug 15), Gandhi Jayanti (Oct 2), Republic Day (Jan 26), Diwali, Pongal/Sankranti, Eid-ul-Fitr, and Good Friday. In the event of unforeseen local government holidays, compensatory working Saturdays will be scheduled by the Principal's office.")
    ])

    # 3. Examination Schedule
    build_pdf("Examination_Schedule.pdf", "Apex Institute of Technology - Examination Schedule & Regulations", [
        ("1. Examination Timings & Hall Protocol", [
            "Morning Session (FN): 09:30 AM to 12:30 PM (Entry permitted until 09:45 AM).",
            "Afternoon Session (AN): 02:00 PM to 05:00 PM (Entry permitted until 02:15 PM).",
            "Hall Tickets: Eligible students can download hall tickets from the student ERP portal 7 days prior to examination commencement.",
            "Physical college ID card and printed Hall Ticket are mandatory for entry into examination halls.",
            "Strictly prohibited items: Smartwatches, mobile phones, programmable calculators, bags, and loose notes. Possession of any electronic device constitutes examination malpractice."
        ]),
        ("2. Revaluation and Script Verification Rules", [
            "Students may apply for photocopy of evaluated answer scripts within 5 working days of result declaration.",
            "Fee for Answer Script Photocopy: Rs. 400 per subject.",
            "Fee for Revaluation: Rs. 800 per subject.",
            "If revaluation results in a mark increase of 15% or more over the original marks, the revised score will be updated and 50% of the revaluation fee will be refunded to the student's account.",
            "Applications must be submitted online through ERP under 'Examinations -> Revaluation Services'."
        ]),
        ("3. Supplementary and Arrear Examinations", "Supplementary examinations for failed courses are conducted simultaneously during regular semester-end examinations. Final year students with a maximum of two standing arrears at the end of the 8th semester are eligible for the Special Fast-Track Supplementary Exam in July.")
    ])

    # 4. Library Rules
    build_pdf("Library_Rules.pdf", "Apex Institute of Technology - Central Library Rules & Services", [
        ("1. Operating Hours & Facilities", [
            "Monday to Friday: 08:00 AM to 08:00 PM.",
            "Saturday & Sunday: 09:00 AM to 05:00 PM.",
            "Exam Period Extended Timings: Open until 10:00 PM on weekdays.",
            "The library houses over 65,000 volumes, 140 print journals, and subscribed digital libraries including IEEE Xplore, ScienceDirect, SpringerLink, and ACM Digital Library accessible on-campus and through OpenAthens remote proxy."
        ]),
        ("2. Book Borrowing Limits and Renewal", [
            "Undergraduate Students: 4 books for 14 calendar days.",
            "Postgraduate Students: 6 books for 21 calendar days.",
            "Faculty Members: 10 books for 90 calendar days.",
            "Renewals: Books may be renewed once online via the Koha OPAC portal provided no reservation hold exists from another user.",
            "Overdue Fine: Rs. 5 per day per overdue book for the first 7 days, and Rs. 10 per day thereafter.",
            "Loss of Book: The borrower must replace the book with the latest edition or pay twice the current market price plus a processing fee of Rs. 200."
        ]),
        ("3. Digital Media Lab & Printing Services", "The Digital Media Center on the 2nd floor offers 60 high-performance workstations with internet access for academic research. Printing charges: Rs. 2 per black-and-white page, Rs. 10 per color page. Binding and scanning services are available at the reprography counter.")
    ])

    # 5. Internship Guidelines
    build_pdf("Internship_Guidelines.pdf", "Apex Institute of Technology - Internship & Industrial Training Guidelines", [
        ("1. Eligibility & Approved Timelines", [
            "B.Tech students are eligible to undertake industrial internships starting from the completion of the 4th semester.",
            "Mandatory Internship: Every student must complete at least 6 weeks of industrial training or internship prior to graduation for a total of 3 academic credits.",
            "Full-semester internships (8th semester) are permitted only for students with a CGPA >= 7.50 and no active backlogs/arrears who have received an offer from a Tier-1 product or core company."
        ]),
        ("2. No Objection Certificate (NOC) Procedure", [
            "Step 1: Obtain the official Internship Offer Letter from the prospective employer detailing role, stipend, start date, and mentor contact.",
            "Step 2: Submit an online NOC request via ERP portal under 'Training & Placement -> Apply NOC' along with the offer letter copy.",
            "Step 3: Department Internship Coordinator and HOD review the technical alignment of the company profile within 3 working days.",
            "Step 4: Dean of Academic Affairs issues the stamped official college NOC.",
            "Students starting internships without an approved college NOC will not receive academic credits and cannot claim attendance waiver."
        ]),
        ("3. Evaluation & Submission Deliverables", "Upon completion, the student must submit: (a) Internship Completion Certificate, (b) Weekly Performance Diary signed by industry supervisor, and (c) Comprehensive Project Report (minimum 25 pages). Final assessment is conducted via viva-voce examination in the respective department.")
    ])

    # 6. Department Information
    build_pdf("Department_Information.pdf", "Apex Institute of Technology - Academic Departments & Laboratories", [
        ("1. Department of Computer Science & Engineering (CSE)", [
            "HOD: Dr. Arvind Ramanathan, Ph.D. (IIT Madras). Contact: hod.cse@apextech.edu, Block A, Room 301.",
            "Programs Offered: B.Tech in CSE (Intake: 180), M.Tech in CSE (Intake: 24).",
            "Specialized Labs: High-Performance Computing Lab (NVIDIA A100 GPU cluster), Cloud & Virtualization Lab, Cybersecurity Lab, and Mobile Application Development Studio."
        ]),
        ("2. Department of Information Technology (IT)", [
            "HOD: Dr. Meenakshi Sundaram, Ph.D. (IISc Bangalore). Contact: hod.it@apextech.edu, Block B, Room 204.",
            "Programs Offered: B.Tech in IT (Intake: 120), B.Tech in Artificial Intelligence & Data Science (Intake: 60).",
            "Specialized Labs: Machine Learning Lab, Big Data Analytics Lab with Hadoop cluster, Web Technologies Lab, and IoT Hardware Prototyping Center."
        ]),
        ("3. Department of Electronics & Communication Engineering (ECE)", [
            "HOD: Dr. Rajeshwari Nair, Ph.D. Contact: hod.ece@apextech.edu, Block C, Room 105.",
            "Specialized Labs: VLSI Design Lab (Cadence & Synopsys EDA tools), Embedded Systems Lab (ARM Cortex boards), Microwave & Antenna Testing Anechoic Chamber, and DSP Lab."
        ]),
        ("4. Department Contact Directory", [
            ["Department", "HOD Name", "Office Location", "Direct Helpline"],
            ["Computer Science & Engg", "Dr. Arvind Ramanathan", "Block A, Room 301", "Ext. 4101"],
            ["Information Technology", "Dr. Meenakshi Sundaram", "Block B, Room 204", "Ext. 4201"],
            ["Electronics & Comm.", "Dr. Rajeshwari Nair", "Block C, Room 105", "Ext. 4301"],
            ["Mechanical Engineering", "Dr. K. Vignesh", "Block D, Room 102", "Ext. 4401"],
            ["Electrical & Electronics", "Dr. S. Priya", "Block E, Room 201", "Ext. 4501"]
        ])
    ])

    # 7. Scholarship Details
    build_pdf("Scholarship_Details.pdf", "Apex Institute of Technology - Institutional & Government Scholarships", [
        ("1. Institutional Merit Scholarships", [
            "Chairman's Merit Scholarship: 100% tuition fee waiver for top 5 students in each engineering branch securing CGPA >= 9.50 in the preceding academic year.",
            "Dean's Honor Award: 50% tuition fee waiver for students maintaining CGPA between 9.00 and 9.49 with zero disciplinary violations.",
            "Sports Excellence Concession: 25% to 75% fee concession for athletes representing state or national university sports tournaments."
        ]),
        ("2. Government & Statutory Scholarship Schemes", [
            "Post-Matric Scholarship Scheme for SC/ST students: 100% tuition and development fee reimbursement provided annual family income is below Rs. 2,50,000.",
            "BC/MBC State Welfare Scholarship: Tuition support of Rs. 25,000 per year for students with parental annual income below Rs. 2,00,000.",
            "National Scholarship Portal (NSP) Schemes: Central Sector Scheme of Scholarship for College and University Students, AICTE Pragati Scholarship for Girls (Rs. 50,000 per annum), and AICTE Saksham Scholarship for differently-abled students."
        ]),
        ("3. Application Guidelines and Timelines", "All scholarship renewal forms and fresh applications must be routed through the College Scholarship Welfare Cell (Administrative Block, Counter 4) between August 15 and September 30 each academic year. Required documents: Income Certificate, Caste/Community Certificate, Previous Marksheets, Aadhaar Card, and Student Bank Passbook copy.")
    ])

    # 8. College FAQ
    build_pdf("College_FAQ.pdf", "Apex Institute of Technology - Frequently Asked Administrative Questions", [
        ("1. Bonafide Certificates & Student Documents", [
            "Question: How do I apply for a Bonafide Certificate?",
            "Answer: Students can apply online through the student portal under 'Services -> Apply Bonafide' or submit a physical application form at Admin Counter 2. Processing takes 2 working days. Urgent same-day processing is available for passport, visa, or educational loan verification with HOD approval.",
            "Question: How do I obtain official transcripts?",
            "Answer: Apply online with a payment of Rs. 500 for the first set and Rs. 200 for subsequent copies. Transcripts are dispatched within 7 working days.",
            "Question: How do I apply for a Bus Pass or renew it?",
            "Answer: Transport fee of Rs. 28,000 per annum must be paid through the online fee portal. Present the payment receipt at the Transport Desk (Ground Floor, Admin Block) along with two passport-size photographs to collect the RFID bus pass."
        ]),
        ("2. Hostel Accommodation & Facilities", [
            "Question: What are the hostel curfew and mess timings?",
            "Answer: Curfew: In-time for all residential students is 08:30 PM on weekdays and 09:30 PM on weekends. Mess Timings: Breakfast: 07:00 AM - 08:45 AM, Lunch: 12:15 PM - 01:45 PM, Snacks: 04:30 PM - 05:30 PM, Dinner: 07:15 PM - 09:00 PM.",
            "Question: What is the fee structure for hostel rooms?",
            "Answer: Four-sharing AC: Rs. 95,000/yr. Four-sharing Non-AC: Rs. 75,000/yr. Double sharing (reserved for 3rd and 4th years): Rs. 1,15,000/yr. Mess charge is Rs. 42,000/yr payable in two semester installments.",
            "Question: How can I register a day-out or night-out pass?",
            "Answer: Day-out and night-out permissions must be applied through the Parent ERP login 24 hours prior and approved by the Chief Warden."
        ]),
        ("3. Fee Payment & Account Queries", [
            "Question: What are the accepted fee payment modes?",
            "Answer: All college fees must be paid online via the SBI Collect Portal or through the student ERP gateway using Net Banking, UPI, or Credit/Debit cards. Cash payments are strictly prohibited at administrative counters.",
            "Question: What is the fine for late tuition fee payment?",
            "Answer: Tuition fees are due within 15 days of semester commencement. A grace period of 10 days is permitted. Thereafter, a late fine of Rs. 100 per day is levied up to 30 days, after which student portal access is temporarily frozen until payment clearance."
        ])
    ])

    print("All 8 demo PDF documents successfully created in data/sample_docs!")

if __name__ == "__main__":
    main()
