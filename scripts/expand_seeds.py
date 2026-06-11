#!/usr/bin/env python3
"""Append Korea guide/school/university seeds to reach jpcampus-scale targets."""
import csv
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

NEW_GUIDES = [
    ("gks-guide", "Budget", "GKS (KGSP) Scholarship Guide for Korea", "Complete guide to Global Korea Scholarship.", "Write a detailed GKS scholarship guide: eligibility, documents, timeline, and tips for language vs degree tracks."),
    ("d4-to-d2", "Visa", "Switching from D-4 to D-2 Visa in Korea", "How language students transition to degree visas.", "Explain D-4 to D-2 visa change process, timing, documents, and common pitfalls for international students."),
    ("seoul-neighborhoods", "Region", "Best Seoul Neighborhoods for Students", "Sinchon vs Hongdae vs Gangnam for students.", "Compare Sinchon, Hongdae, Gangnam, and Jamsil for student housing, commute, and lifestyle with a table."),
    ("busan-student-life", "Region", "Student Life in Busan: Costs and Culture", "Living and studying in Busan.", "Compare Busan student life: rent, transit, beaches, language schools, and university access."),
    ("goshiwon-guide", "Housing", "Goshiwon Guide for Korea Students", "What to expect in Korean goshiwon.", "Explain goshiwon housing: costs, contracts, pros/cons, and red flags for foreign students."),
    ("dorm-application", "Housing", "How to Apply for University Dormitories in Korea", "Dorm priority and deadlines.", "Guide to Korean university dorm applications: deadlines, fees, roommate rules, and alternatives."),
    ("topik-study-plan", "Exam", "3-Month TOPIK Study Plan", "Structured TOPIK prep schedule.", "Create a 12-week TOPIK study plan with weekly goals for vocabulary, grammar, reading, and listening."),
    ("topik-vs-klat", "Exam", "TOPIK vs KIIP: Which Do You Need?", "Language requirements explained.", "Compare TOPIK, KIIP, and university-specific Korean tests for admission and visa purposes."),
    ("arc-registration", "Settlement", "Alien Registration Card (ARC) Guide", "Step-by-step ARC application.", "Write ARC registration guide: where to go, documents, photo rules, and re-entry permit basics."),
    ("korean-bank-comparison", "Settlement", "KB vs Shinhan vs Woori for Students", "Bank comparison for newcomers.", "Compare KB, Shinhan, and Woori bank accounts for international students in Korea."),
    ("sim-esim-korea", "Settlement", "SIM and eSIM Plans in Korea (2026)", "Mobile setup for students.", "Compare prepaid SIM, eSIM, and carrier plans (SKT, KT, LG U+) for short and long stays in Korea."),
    ("t-money-guide", "Settlement", "T-money and Transit in Korea", "Using public transport cards.", "Explain T-money, Cashbee, and transit apps; how to recharge and save on Seoul/Busan commutes."),
    ("part-time-cafe", "Part-time", "Part-Time Jobs in Cafes and Stores", "Common student jobs in Korea.", "List part-time job types, average wages, Korean level needed, and how to apply legally on D-2/D-4."),
    ("internship-korea", "Part-time", "Internships for International Students", "Finding internships in Korea.", "Explain internship options, visa rules, and where to search (Saramin, university boards, LinkedIn)."),
    ("health-clinic-korea", "Insurance", "Using Clinics and Hospitals in Korea", "Medical visit guide with phrases.", "Guide to visiting clinics in Korea: NHI copay, useful Korean phrases, emergency vs routine care."),
    ("culture-shock-korea", "Culture", "Culture Shocks in Korea for New Students", "Social norms newcomers notice.", "List top culture shocks: age hierarchy, drinking culture, PC rooms, delivery apps, and classroom etiquette."),
    ("korean-study-apps", "Preparation", "Best Apps for Learning Korean Before Arrival", "Pre-departure study tools.", "Recommend apps and resources for beginners before arriving in Korea (Hangul, vocab, listening)."),
    ("packing-korea", "Preparation", "What to Pack for Korea Study Abroad", "Seasonal packing checklist.", "Create a packing checklist for Korea: documents, adapters, medicine, clothing by season."),
    ("seoul-vs-incheon", "Region", "Seoul vs Incheon for Language Study", "City comparison near capital.", "Compare studying in Seoul proper vs Incheon: cost, schools, airport access, and commute."),
    ("daegu-study", "Region", "Studying in Daegu: Universities and Cost", "Regional hub guide.", "Guide to studying in Daegu: major universities, lower costs, and student life."),
    ("gwangju-study", "Region", "Studying in Gwangju: Chonnam and Beyond", "Honam region guide.", "Explain Gwangju as a study destination: Chonnam National, rent, and regional culture."),
    ("daejeon-study", "Region", "Studying in Daejeon: KAIST and Chungnam", "Science city guide.", "Compare Daejeon universities (KAIST, Chungnam, Hoseo) and living costs."),
    ("university-english-tracks", "Selection", "English-Taught Programs in Korean Universities", "Degrees without Korean fluency.", "List types of English-taught undergraduate and graduate programs and admission requirements."),
    ("language-to-degree", "Selection", "Language School to University Pathway", "Planning your admission timeline.", "Explain typical 1-2 year language school to university pathway with TOPIK milestones."),
    ("spring-vs-fall-intake", "Selection", "March vs September Intake in Korea", "Choosing your start term.", "Compare March and September intakes for language schools and universities."),
    ("transfer-university-korea", "Selection", "Transferring to a Korean University", "Credit transfer basics.", "Explain transfer admission requirements, credit evaluation, and language requirements."),
    ("graduate-study-korea", "Selection", "Graduate School in Korea for Foreigners", "MA/PhD overview.", "Overview of Korean graduate programs: research vs coursework, funding, and TOPIK/English requirements."),
    ("k-pop-media-majors", "Selection", "K-pop and Media Programs in Korea", "Specialized study tracks.", "Survey universities and programs related to K-pop, film, and media for international students."),
    ("business-ma-korea", "Selection", "MBA and Business Programs in Korea", "Business school guide.", "Compare MBA and business programs at major Korean universities for international students."),
    ("engineering-universities-korea", "Selection", "Top Engineering Universities in Korea", "STEM study options.", "Profile top engineering schools (KAIST, POSTECH, SNU, Hanyang) for international applicants."),
    ("women-universities-korea", "Selection", "Women's Universities in Korea", "Ewha, Sookmyung, and others.", "Guide to women's universities open to international students: programs and campus life."),
    ("national-vs-private-korea", "Selection", "National vs Private Universities in Korea", "Tuition and reputation tradeoffs.", "Compare national and private universities on tuition, prestige, and international support."),
    ("remittance-korea", "Budget", "Sending Money to Korea: Wise and Banks", "International transfers guide.", "Compare Wise, bank SWIFT, and other methods for tuition and living expense transfers to Korea."),
    ("monthly-budget-busan", "Budget", "Monthly Student Budget in Busan", "Busan cost breakdown.", "Provide monthly budget table for students in Busan: rent, food, transit, phone."),
    ("monthly-budget-seoul", "Budget", "Monthly Student Budget in Seoul (2026)", "Seoul cost breakdown.", "Provide detailed monthly budget for Seoul students by frugal vs comfortable lifestyle."),
    ("convenience-store-korea", "Culture", "Mastering Korean Convenience Stores", "CU, GS25, Emart24 guide.", "Guide to Korean convenience stores: meals, bill pay, delivery pickup, and student hacks."),
    ("bicycle-korea", "Culture", "Cycling Rules in Korea for Students", "Bike registration and safety.", "Explain bicycle rules, Ttareungi bike share, and campus cycling in Korea."),
    ("weather-korea", "Preparation", "Korea Seasons: What Clothes to Bring", "Climate by season.", "Explain Korea's four seasons and what students should prepare for summer humidity and winter cold."),
    ("lgbtq-student-korea", "Culture", "LGBTQ+ Student Life in Korea", "Practical context for newcomers.", "Provide practical, respectful overview of LGBTQ+ student experiences and resources in major Korean cities."),
]

NEW_SCHOOLS = [
    ("한양대학교 ERICA 국제언어교육원", "Hanyang University ERICA International Language Institute", "Gyeonggi", "Ansan"),
    ("동국대학교 한국어교육센터", "Dongguk University Korean Language Institute", "Seoul", "Seoul"),
    ("국민대학교 한국어센터", "Kookmin University Korean Language Center", "Seoul", "Seoul"),
    ("숭실대학교 한국어교육원", "Soongsil University Korean Language Institute", "Seoul", "Seoul"),
    ("건국대학교 언어교육원", "Konkuk University Language Education Institute", "Seoul", "Seoul"),
    ("세종대학교 한국어교육센터", "Sejong University Korean Language Center", "Seoul", "Seoul"),
    ("한국외국어대학교 한국어교육센터", "HUFS Korean Language Education Center", "Seoul", "Seoul"),
    ("강남대학교 한국어교육센터", "Kangnam University Korean Language Center", "Gyeonggi", "Yongin"),
    ("경희대학교 국제교육원", "Kyung Hee University Institute of International Education", "Seoul", "Seoul"),
    ("중앙대학교 어학원", "Chung-Ang University Language Institute", "Seoul", "Seoul"),
    ("동아대학교 한국어교육원", "Dong-A University Korean Language Institute", "Busan", "Busan"),
    ("영산대학교 한국어교육원", "Youngsan University Korean Language Institute", "Busan", "Busan"),
    ("대구대학교 한국어교육원", "Daegu University Korean Language Institute", "Daegu", "Daegu"),
    ("조선대학교 한국어교육원", "Chosun University Korean Language Institute", "Gwangju", "Gwangju"),
    ("단국대학교 한국어교육센터", "Dankook University Korean Language Center", "Gyeonggi", "Yongin"),
]

NEW_UNIVS = [
    ("동국대학교", "Dongguk University", "Seoul"),
    ("국민대학교", "Kookmin University", "Seoul"),
    ("숭실대학교", "Soongsil University", "Seoul"),
    ("건국대학교", "Konkuk University", "Seoul"),
    ("세종대학교", "Sejong University", "Seoul"),
    ("동아대학교", "Dong-A University", "Busan"),
    ("영산대학교", "Youngsan University", "Busan"),
    ("대구대학교", "Daegu University", "Daegu"),
    ("조선대학교", "Chosun University", "Gwangju"),
    ("단국대학교", "Dankook University", "Gyeonggi"),
    ("한국외국어대학교", "Hankuk University of Foreign Studies", "Seoul"),
    ("서울시립대학교", "University of Seoul", "Seoul"),
    ("광운대학교", "Kwangwoon University", "Seoul"),
    ("명지대학교", "Myongji University", "Seoul"),
    ("상명대학교", "Sangmyung University", "Seoul"),
    ("숙명여자대학교", "Sookmyung Women's University", "Seoul"),
    ("덕성여자대학교", "Duksung Women's University", "Seoul"),
    ("한국항공대학교", "Korea Aerospace University", "Gyeonggi"),
    ("울산대학교", "Ulsan National Institute of Science and Technology", "Ulsan"),
    ("전북대학교", "Jeonbuk National University", "Jeonbuk"),
    ("창원대학교", "Changwon National University", "Gyeongnam"),
    ("제주대학교", "Jeju National University", "Jeju"),
    ("강원대학교", "Kangwon National University", "Gangwon"),
    ("한국교통대학교", "Korea National University of Transportation", "Chungbuk"),
    ("한국체육대학교", "Korea National Sport University", "Seoul"),
    ("한국예술종합학교", "Korea National University of Arts", "Seoul"),
    ("한국방송통신대학교", "Korea National Open University", "Seoul"),
    ("한국기술교육대학교", "Korea University of Technology and Education", "Chungnam"),
    ("울산과학기술원", "Ulsan National Institute of Science and Technology", "Ulsan"),
    ("포항공과대학교", "POSTECH", "Gyeongbuk"),
]


def _append_csv(path, fieldnames, rows, key_col):
    existing = set()
    if os.path.isfile(path):
        with open(path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                existing.add(row[key_col].strip())
    new_rows = [r for r in rows if r[key_col] not in existing]
    if not new_rows:
        return 0
    write_header = not os.path.isfile(path) or os.path.getsize(path) == 0
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerows(new_rows)
    return len(new_rows)


def main():
    g = _append_csv(
        os.path.join(DATA, "guide_topics.csv"),
        ["slug", "category", "title", "description", "prompt"],
        [{"slug": s, "category": c, "title": t, "description": d, "prompt": p} for s, c, t, d, p in NEW_GUIDES],
        "slug",
    )
    s = _append_csv(
        os.path.join(DATA, "language_schools.csv"),
        ["name_ko", "name_en", "region", "city"],
        [{"name_ko": a, "name_en": b, "region": c, "city": d} for a, b, c, d in NEW_SCHOOLS],
        "name_ko",
    )
    u = _append_csv(
        os.path.join(DATA, "universities.csv"),
        ["name_ko", "name_en", "region"],
        [{"name_ko": a, "name_en": b, "region": c} for a, b, c in NEW_UNIVS],
        "name_ko",
    )
    print(f"Added guides={g}, schools={s}, universities={u}")


if __name__ == "__main__":
    main()
