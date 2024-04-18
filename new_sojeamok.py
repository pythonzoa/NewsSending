import requests
from bs4 import BeautifulSoup as bs
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import re

keywords = ["아시아나항공", "제주항공", "이스타항공", "에어인천", "에어프레미아", "티웨이항공"]
# 현재 시간을 YYYY-MM-DD HH:MM 형식으로 포맷
current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
def extract_article_content(url):
    """
    주어진 URL에서 기사의 본문을 추출하여 반환합니다.

    Args:
    url (str): 기사의 웹 주소.

    Returns:
    str: 기사 본문의 텍스트. 본문을 찾을 수 없는 경우, 비어있는 문자열을 반환합니다.
    """
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return ""

        soup = bs(response.content, 'html.parser')
        article_body = soup.find('div', class_='article-body')

        if article_body:
            paragraphs = article_body.find_all('p')
            article_text = '\n'.join(paragraph.text for paragraph in paragraphs)
            return article_text
        else:
            return ""
    except Exception as e:
        print(f"Error extracting article content: {e}")
        return ""

def is_keyword_in_article(url, keyword):
    """
    주어진 URL의 기사 본문에서 지정된 키워드의 존재 여부를 검사합니다.

    Args:
    url (str): 기사의 웹 주소.
    keyword (str): 검사할 키워드.

    Returns:
    bool: 키워드가 기사 본문에 존재하면 True, 그렇지 않으면 False를 반환합니다.
    """
    article_text = extract_article_content(url)
    return keyword in article_text

def get_naver_news(keyword):
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
    response = requests.get(url)
    soup = bs(response.text, 'html.parser')
    now = datetime.now()
    articles_list = []

    articles = soup.find_all('div', class_='news_area')
    for article in articles:
        title_tag = article.find('a', class_='news_tit')
        title = title_tag.get('title')
        link = title_tag.get('href')
        date_tag = article.find('span', class_='info')
        date_text = date_tag.text

        if "시간 전" in date_text or "분 전" in date_text:
            hours_ago = int(re.search(r'\d+', date_text).group())
            article_time = now - timedelta(hours=hours_ago)
            if article_time > now - timedelta(hours=12):
                if is_keyword_in_article(link, '화물'):
                    articles_list.append((keyword, title, link, date_text))

    return articles_list


def MarinaNews(keywords, get_naver_news, send_email):
    articles_by_keyword = {keyword: get_naver_news(keyword) for keyword in keywords}

    html = f"""
    <html>
    <head>
    <style>
      .article {{ margin-bottom: 20px; }}
      .keyword {{ font-weight: bold; margin-bottom: 5px; }}
      a {{ text-decoration: none; color: blue; }}
      a:hover {{ text-decoration: underline; }}
      .separator {{ display: inline; }} /* 구분자를 인라인으로 표시 */
    </style>
    </head>
    <body>
    <h2>최근 기사 목록</h2>
    """

    for keyword, articles in articles_by_keyword.items():
        if articles:
            html += f'<h3>{keyword}</h3>'
            article_links = []
            for _, title, link, date_text in articles:
                article_link = f'<a href="{link}">{title}</a>'
                article_links.append(article_link)
            # 각 기사 제목 사이에 구분자를 삽입
            html += ' <span class="separator"><br></span> '.join(article_links)
    html += "</body></html>"

    send_email(html)

def send_email(html_content):
    # Gmail 계정 정보
    sender_email = "hwijunjang@koreanair.com"  # 발신자 이메일 주소
    app_password = "aaig gxux eokv kmjv"  # Gmail 애플리케이션 비밀번호
    # 복수의 수신자 이메일 주소들
    receiver_emails = ["hwijunjang@koreanair.com", "onlyhalfgp@gmail.com"]  # 수신자 이메일 주소 리스트

    # 이메일 메시지 설정
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)  # 수신자 이메일 주소들을 콤마로 구분하여 설정
    msg['Subject'] = f"Project Maria 관련 최신 뉴스 - 발송 시간: {current_time}"

    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        print("이메일이 성공적으로 발송되었습니다.")
    except Exception as e:
        print(f"이메일 전송에 실패했습니다: {e}")


while True:
    MarinaNews(keywords, get_naver_news, send_email)
    time.sleep(21600)  # 6 hours
