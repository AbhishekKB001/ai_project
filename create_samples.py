from PIL import Image, ImageDraw
from pathlib import Path

out_dir = Path(__file__).resolve().parent / "sample_data" / "sample_notice_images"
out_dir.mkdir(parents=True, exist_ok=True)

samples = [
    {
        "file": "exam_notice.png",
        "title": "COLLEGE OF ENGINEERING & TECHNOLOGY",
        "dept": "OFFICE OF CONTROLLER OF EXAMINATIONS",
        "sub": "NOTICE: COMMENCEMENT OF FALL MID-TERM EXAMINATIONS 2026",
        "body": "Date: October 24, 2026\n\nAll B.Tech & M.Tech students are notified that Mid-Term Exams\ncommence on November 10, 2026.\nDownload hall tickets from student ERP portal after clearing all dues.\nMandatory: Bring printed hall ticket and valid college ID card.\nEntry without physical hall ticket is strictly prohibited.\nLast date to clear fee dues: November 6, 2026.",
        "urgency": "URGENT / MANDATORY",
        "sig": "Controller of Examinations"
    },
    {
        "file": "placement_drive.png",
        "title": "CENTRAL TRAINING & PLACEMENT CELL",
        "dept": "DEPARTMENT OF CORPORATE RELATIONS",
        "sub": "NOTICE: GOOGLE & MICROSOFT CAMPUS RECRUITMENT DRIVE",
        "body": "Date: October 22, 2026\n\nApplications open for Software Development Engineer (SDE-1) roles.\nEligibility: B.Tech CSE/IT 3rd & 4th Year with CGPA 8.0 and above.\nNo active backlogs allowed.\nRegistration Deadline: November 12, 2026.\nHackerRank Coding Assessment: November 18, 2026 at 10:00 AM.\nShortlisted candidates will face technical interviews on campus.",
        "urgency": "PLACEMENT DRIVE",
        "sig": "Head, Training & Placement"
    },
    {
        "file": "hackathon_announcement.png",
        "title": "INNOVATION & INCUBATION COUNCIL",
        "dept": "CENTER FOR ARTIFICIAL INTELLIGENCE",
        "sub": "CIRCULAR: NATIONAL LEVEL HACKATHON HACKNOVA 2026",
        "body": "Date: October 20, 2026\n\nTheme: Generative AI, Web3, Smart Campus & Green Tech.\nTotal Cash Prize Pool: $10,000 + Cloud GPU Credits.\nTeam Size: 2 to 4 members (inter-departmental teams permitted).\nPrototype Abstract Submission Deadline: November 25, 2026.\nGrand Finale: December 5-6, 2026 at Campus Tech Park.\nRegistration link active on portal.",
        "urgency": "OPEN REGISTRATION",
        "sig": "Faculty Coordinator, Innovation Cell"
    }
]

for s in samples:
    img = Image.new("RGB", (820, 520), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Header border
    draw.rectangle([(20, 20), (800, 500)], outline=(30, 41, 59), width=3)
    draw.rectangle([(25, 25), (795, 95)], fill=(241, 245, 249))
    draw.text((40, 35), s["title"], fill=(15, 23, 42))
    draw.text((40, 60), s["dept"], fill=(71, 85, 105))
    
    # Urgency pill
    draw.rectangle([(620, 35), (780, 65)], fill=(225, 29, 72))
    draw.text((630, 42), s["urgency"], fill=(255, 255, 255))
    
    # Subject
    draw.text((40, 115), s["sub"], fill=(15, 23, 42))
    draw.line([(40, 140), (780, 140)], fill=(203, 213, 225), width=2)
    
    # Body
    draw.text((40, 160), s["body"], fill=(30, 41, 59))
    
    # Sign
    draw.line([(550, 440), (760, 440)], fill=(71, 85, 105), width=1)
    draw.text((550, 450), s["sig"], fill=(15, 23, 42))
    
    out_path = out_dir / s["file"]
    img.save(out_path)
    print("Created sample notice image:", s["file"])
