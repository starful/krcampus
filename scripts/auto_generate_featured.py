import json
import os
import time
import re
import frontmatter
from datetime import datetime
from common import setup_logging, setup_gemini, clean_json_response, DATA_DIR, CONTENT_DIR, LOG_DIR

# --- 설정 ---
setup_logging("auto_featured.log")
model = setup_gemini()

# 학교 데이터 경로
SCHOOLS_JSON = os.path.join(os.path.dirname(DATA_DIR), "app", "static", "json", "schools_data.json")

# [새로운 전략적 TOPICS 목록]
TOPICS = [
    # 1. 취업 성공률이 높은 비즈니스 특화 학교
    {
        "slug": "career-success-business-schools",
        "title": "Boost Your Career: Top 5 Japanese Schools for Job Seekers",
        "criteria": {
            "category": "school", 
            "tag": "business" 
        },
        "count": 5,
        "thumbnail": "https://images.unsplash.com/photo-1454165833767-027ffea9e778?w=500" # 비즈니스 미팅 이미지
    },

    # 2. 여학생을 위한 안전하고 전문적인 여자 대학교/교육기관
    {
        "slug": "top-womens-education-japan",
        "title": "Empowering Women: Best Women's Universities & Colleges in Japan",
        "criteria": {
            "category": "university", 
            "tag": "woman" # Ochanomizu, Tsuda, Japan Women's 등 타겟팅
        },
        "count": 5,
        "thumbnail": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=500" # 전문직 여성 이미지
    },

    # 3. IT 및 로봇 공학 등 첨단 기술 공과 대학
    {
        "slug": "top-engineering-tech-universities",
        "title": "Future Tech Leaders: Top 5 Engineering Universities in Japan",
        "criteria": {
            "category": "university", 
            "tag": "engineering" # Tokyo Tech, Shibaura, Nagoya Tech 등
        },
        "count": 5,
        "thumbnail": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=500" # 로봇/공학 이미지
    },

    # 4. 학비 부담이 적은 우수 국립 대학교 (가성비 유학)
    {
        "slug": "best-national-universities-japan",
        "title": "Affordable Excellence: Top 5 National Universities for International Students",
        "criteria": {
            "category": "university", 
            "tag": "national" 
        },
        "count": 5,
        "thumbnail": "https://images.unsplash.com/photo-1525921429624-479b6a29d84c?w=500" # 클래식한 캠퍼스 건물
    },

    # 5. 애니메이션, 만화, 디자인 전공자를 위한 예술 학교
    {
        "slug": "creative-arts-design-schools",
        "title": "Art & Design: Best Schools for Anime, Manga, and Creative Studies",
        "criteria": {
            "category": "school", 
            "tag": "art" # 디자인, 미술 특화 학교
        },
        "count": 4,
        "thumbnail": "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=500" # 화실/드로잉 이미지
    },

    # 6. 도쿄 중심가에서 즐기는 어반 라이프스타일 학교
    {
        "slug": "urban-lifestyle-tokyo-schools",
        "title": "Study in the Heart of Tokyo: Best Central Tokyo Language Schools",
        "criteria": {
            "category": "school", 
            "region": "東京都" 
        },
        "count": 5,
        "thumbnail": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=500" # 도쿄 야경/시내 이미지
    }
]

def load_data_and_build_index():
    if not os.path.exists(SCHOOLS_JSON):
        print("❌ schools_data.json not found. Run build_data.py first.")
        return [], []

    with open(SCHOOLS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
        schools = data.get('schools', [])

    link_index = []
    for s in schools:
        name_en = s['basic_info'].get('name_en')
        if name_en and len(name_en) > 3:
            clean_name = re.sub(r'\s*\(.*?\)', '', name_en).strip()
            link_index.append({
                "name": clean_name,
                "link": s['link'],
                "id": s['id']
            })
    
    link_index.sort(key=lambda x: len(x['name']), reverse=True)
    return schools, link_index

def filter_schools(schools, criteria, limit):
    candidates = []
    for s in schools:
        if s.get('category') != criteria['category']: continue
        
        full_text = str(s).lower()
        match = True
        
        if 'region' in criteria and criteria['region'] not in s['basic_info']['address']:
            match = False
        if 'tag' in criteria and criteria['tag'].lower() not in full_text:
            match = False
            
        if match:
            candidates.append(s)
            
    return candidates[:limit]

def generate_article_content(topic, selected_schools):
    print(f"🤖 Writing Curated List: {topic['title']}...")
    
    schools_context = ""
    for s in selected_schools:
        name = s['basic_info']['name_en'] or s['basic_info']['name_ja']
        features = ", ".join(s.get('features', []))
        schools_context += f"- {name}: {features}\n"

    prompt = f"""
    You are an expert educational editor. Write a high-quality "Curated Guide" article.
    Title: "{topic['title']}"
    
    Structure:
    1. Introduction: Explain the importance of this choice for international students (approx 120 words).
    2. The Selection: List each school below with a catchy subheading.
    3. Deep Dive: For each school, provide a 2-paragraph explanation of why it was selected, its unique culture, and specific benefits for foreigners.
    4. Conclusion: Final advice on how to apply.

    Constraints:
    - Use professional, encouraging English.
    - Standard Markdown (## for schools).
    - Length: Detailed and substantial (aim for 1000+ words).
    
    Schools to include:
    {schools_context}
    """
    
    try:
        # 텍스트가 길어질 수 있으므로 flash 모델의 토큰 제한 내에서 최대한 길게 요청
        response = model.generate_content(prompt)
        return clean_json_response(response.text)
    except Exception as e:
        print(f"❌ Error during AI generation: {e}")
        return None

def apply_auto_links(content, link_index):
    updated_content = content
    for item in link_index:
        name = item['name']
        link = item['link']
        pattern = re.compile(r'(?<!\[)\b' + re.escape(name) + r'\b(?!\])')
        if pattern.search(updated_content):
            updated_content = pattern.sub(f"[{name}]({link})", updated_content, count=1)
    return updated_content

def main():
    schools, link_index = load_data_and_build_index()
    if not schools: return

    for topic in TOPICS:
        selected = filter_schools(schools, topic["criteria"], topic["count"])
        if not selected: continue
            
        raw_content = generate_article_content(topic, selected)
        if raw_content:
            linked_content = apply_auto_links(raw_content, link_index)
            
            filename = f"guide_{topic['slug']}.md"
            filepath = os.path.join(CONTENT_DIR, filename)
            
            meta = {
                "layout": "guide",
                "id": topic['slug'],
                "title": topic['title'],
                "category": "Curated List",
                "is_featured": True,
                "tags": ["Ranking", "Recommendation", topic['slug']],
                "description": f"Explore our top picks for {topic['title']}. Discover the best schools matching your career and lifestyle goals in Japan.",
                "thumbnail": topic['thumbnail'],
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("---\n")
                f.write(json.dumps(meta, ensure_ascii=False, indent=2))
                f.write("\n---\n\n")
                f.write(linked_content)
                
            print(f"✅ Created: {filename}")
            time.sleep(5) # API 속도 제한 준수

if __name__ == "__main__":
    main()