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
factors = ["화물","합병"]


def extract_article_content(url, keywords):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = bs(response.content, 'html.parser')
        text = ' '.join(soup.stripped_strings)
        if any(keyword in text for keyword in keywords):
            return text
    except Exception as e:
        print(f"기사 본문 추출 중 오류: {e}")
    return ""


def is_recent_article(date_text):
    now = datetime.now()
    if "분 전" in date_text:
        return True
    elif "시간 전" in date_text or "TOP" in date_text:
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
            date_infos = article.find_all('span', class_='info')
            article_is_recent = False
            for date_info in date_infos:
                date_text = date_info.text
                if "일 전" in date_text:
                    article_is_recent = False
                    break
                elif is_recent_article(date_text):
                    article_is_recent = True
            if article_is_recent:
                title = article.find('a', class_='news_tit').get('title')
                link = article.find('a', class_='news_tit').get('href')
                if extract_article_content(link, factors):
                    recent_articles.append((title, link))
        return recent_articles
    except Exception as e:
        print(f"네이버 뉴스 검색 중 오류: {e}")
    return []


def send_email(html_content, recipient_emails):
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipient_emails)
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

    if unique_articles:
        # Generate and send email with articles
        html_content = "<html><head><style>body { font-family: Arial, sans-serif; }.article { margin-bottom: 20px; font-size: 14px; }</style></head><body><h2>최신 기사 리스트</h2>"
        for idx, (title, link) in enumerate(unique_articles, start=1):
            html_content += f'<p class="article">{idx}. <a href="{link}">{title}</a></p>'
        html_content += "</body></html>"
        send_email(html_content, ["hwijunjang@koreanair.com","onlyhalfgp@gmail.com"])
        # send_email(html_content, ["sanghunseo@koreanair.com","jhoon_kim@koreanair.com","skyukim@koreanair.com","hwijunjang@koreanair.com"])
    else:
        # Send notification email that no articles were found
        html_content = "<html><body><p>새로운 기사가 없습니다.</p></body></html>"
        send_email(html_content, ["hwijunjang@koreanair.com"])

if __name__ == "__main__":
    main()
