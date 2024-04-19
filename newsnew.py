import requests
from bs4 import BeautifulSoup as bs
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
from datetime import datetime, timedelta


# 환경 변수에서 이메일 계정 정보를 가져옵니다. 실제 환경에서는 이 값을 설정해야 합니다.
sender_email = "hwijunjang@koreanair.com"
app_password = "aaig gxux eokv kmjv"

keywords = ["아시아나항공", "제주항공", "이스타항공", "에어인천", "에어프레미아", "티웨이항공"]
# keywords = ["아시아나항공"]
factors = ["화물","합병"]
# factors = [""]


def extract_article_content(url, keywords):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = bs(response.content, 'html.parser')
        print(soup)

        # 첫 번째 셀렉터로 시도: 'news_view' 클래스를 가진 section 태그
        article_section = soup.find('section', class_='news_view')
        # 두 번째 셀렉터로 시도: 'article-body' 클래스를 가진 div 태그
        if not article_section:
            article_section = soup.find('div', class_='article-body')
        # 세 번째 셀렉터로 시도: 'viewer' 클래스를 가진 div 태그
        if not article_section:
            article_section = soup.find('div', class_='viewer')
        # 네 번째 셀렉터로 시도: 'pop_area ai_pop' 클래스를 가진 div 태그
        if not article_section:
            article_section = soup.find('div', class_='pop_area ai_pop')
        if not article_section:
            article_section = soup.find('div', class_='articlebody')
        if not article_section:
            article_section = soup.find('div', class_='section-content')
        if not article_section:
            article_section = soup.find('div', class_='news-cont-area print')
        if not article_section:
            article_section = soup.find('div', class_='cont_body')


        if article_section:
            # 태그 내의 모든 텍스트를 추출합니다.
            content = '\n'.join(segment.strip() for segment in article_section.stripped_strings)
            # 복수의 키워드 중 하나라도 본문 내에 포함되어 있는지 검사합니다.
            if any(keyword in content for keyword in keywords):
                return content
    except Exception as e:
        print(f"기사 본문 추출 중 오류: {e}")
    return ""

def is_recent_article(date_text):
    now = datetime.now()
    if "시간 전" in date_text or "분 전" in date_text or "TOP" in date_text:
        hours_ago = int(re.search(r'\d+', date_text).group())
        article_time = now - timedelta(hours=hours_ago)
        return article_time > now - timedelta(hours=24)
    return False

def get_naver_news(keyword):
    try:
        url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
        response = requests.get(url)
        response.raise_for_status()
        soup = bs(response.text, 'html.parser')
        articles = soup.find_all('div', class_='news_area')
        recent_articles = []
        for article in articles:
            if is_recent_article(article.find('span', class_='info').text):
                title = article.find('a', class_='news_tit').get('title')
                link = article.find('a', class_='news_tit').get('href')
                # 기사 본문에서 '화물' 키워드가 포함되어 있는지 확인합니다.
                if extract_article_content(link,factors):
                    recent_articles.append((title, link))
        return recent_articles
    except Exception as e:
        print(f"네이버 뉴스 검색 중 오류: {e}")
    return []

def send_email(html_content):
    receiver_emails = ["hwijunjang@koreanair.com","onlyhalfgp@gmail.com"]
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)
    msg['Subject'] = f"Project Marina 최신 뉴스 목록 - {datetime.now().strftime('%y/%m/%d %H:%M')}"
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
        print("이메일이 성공적으로 발송되었습니다.")
    except Exception as e:
        print(f"이메일 전송 실패: {e}")

def main():
    articles = [article for keyword in keywords for article in get_naver_news(keyword)]
    unique_articles = list(set(articles))

    # HTML 시작 부분에 스타일을 정의합니다.
    html_content = """
    <html>
    <head>
    <style>
      body { font-family: Arial, sans-serif; }
      .article { margin-bottom: 20px; font-size: 14px; } /* 폰트 크기를 14px로 설정 */
    </style>
    </head>
    <body>
    <h2>최신 기사 리스트</h2>
    """

    # 기사 제목과 링크를 HTML로 구성하면서 숫자를 붙입니다.
    for idx, (title, link) in enumerate(unique_articles, start=1):
        html_content += f'<p class="article">{idx}. <a href="{link}">{title}</a></p>'

    html_content += "</body></html>"

    send_email(html_content)

if __name__ == "__main__":
    main()
