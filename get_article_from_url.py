import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime
import re


def get_article_from_url(url):
    """
    概要：引数のURLからコンテンツの本文を取得してtxtファイルに保存する関数
    引数：
    url(str): yahooアクセスランキングのサイトURLを引数で指定
    戻り値：(success: bool, message: str)
            success: 処理が成功した場合は1(True)、失敗した場合は0(False)
            message: 処理結果を説明する
    使用例：
        suc, mess = get_article_from_url()
    """

    #処理結果メッセージ
    message ="成功"
    #成否フラグ
    is_success = 0

    # URLチェック
    if is_valid_url(url)==False:
        return is_success, "URLが不正です"
    #URL一覧の取得
    links = []

    try:
        #url取得
        response = requests.get(url)
        #HTTPステータスコードを確認し200番台であればtry:部分のみ実行
        #urlを取得する際にエラーが出たらexceptに回す
        response.raise_for_status()

        #urlからテキスト取得
        soup = BeautifulSoup(response.text, 'html.parser')

        # ランキング記事のリストを取得
        #newsFeed_itemクラスからliをすべて取得
        articles = soup.find_all('li', class_='newsFeed_item')

        #ランキング記事のリストから
        for article in articles:
            #newsFeed_item_linkクラスからaをすべて取得
            link = article.find('a', class_='newsFeed_item_link')
            #linkオブジェクトが存在し、その属性に'href'が含まれているか確認
            if link and 'href' in link.attrs:
                href = link['href']
                #Yahoo!ニュースの記事リンクのみを選別
                if href.startswith('https://news.yahoo.co.jp/articles/'):
                    links.append(href)
        #linksから各urlのテキストを取得
        for index,link_url in enumerate (links, start=1):

            print(f"Yahooニュースランキング:{index}")
            article_text = get_detail_text(link_url, "")
            time.sleep(1)
            # 記事をテキストファイルに保存
            save_article_to_file(article_text, index)
        # 処理成功フラグを立てる
        is_success = 1

    #HTTPリクエストに関連するさまざまなエラー
    except requests.RequestException as e:
        is_success = 0
        message = f"ランキングページの取得中にエラーが発生しました"
        return is_success, message
    #それ以外のエラー
    except Exception as e:
        is_success = 0
        message = f"予期せぬエラーが発生しました{str(e)}"
        return is_success, message

    return is_success, message
    


def get_detail_text(detail_link, parent_txt="", page=1):
    """
    概要：記事の詳細テキストを取得する関数
    引数：
        detail_link (str): 記事のURL
        parent_txt (str, optional): 前のページのテキスト（デフォルト: ""）
        page (int, optional): 現在のページ番号（デフォルト: 1）
   
    戻り値：str 記事のテキスト
    使用例：article_text = get_detail_text(link_url, "")
    """
    full_text = ""
   
    try:
        print(f"###{detail_link}")
        # レスポンスを取得
        response = requests.get(detail_link)
        #urlを取得する際にエラーが出たらexceptに回す
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 本文テキストの取得
        paragraphs = soup.find_all('p', class_="sc-54nboa-0 deLyrJ yjSlinkDirectlink highLightSearchTarget")
        for p in paragraphs:
            #pタグ一つにつき改行
            full_text += p.text + "\n"

        return_txt = parent_txt + full_text
        
        # 次のページがあるか確認
        # cl_link:nextのaタグを取得
        target_a_tags = soup.find_all('a', attrs={'data-cl-params': '_cl_vmodule:page;_cl_link:next;'})
        if target_a_tags:
            next_page = None
            for tag in target_a_tags:
                # hrefの値を取得
                next_page = tag.get('href')
                break
            if next_page:
                # 次ページが見つかった場合
                next_link = f"https://news.yahoo.co.jp{next_page}"
                    # 次ページのURLチェック
                if is_valid_url(next_link):
                    return_txt = get_detail_text(next_link, return_txt)
                else:
                    # 次ページのURLが不正
                    raise Exception(f"無効なURL: {next_link}")
 

    
    except requests.RequestException as e:
        raise requests.RequestException(f"リクエストエラーが発生しました: {str(e)}")
    except Exception as e:
        raise Exception(f"予期せぬエラーが発生しました: {str(e)}")

    return return_txt
            

def save_article_to_file(content, index):
    """
    概要：記事をファイルに保存する関数
    引数：
        content (str)保存する記事の内容
        index (int)記事のインデックス番号
    戻り値：None
    使用例：save_article_to_file("記事の内容", 1)
    """   
    try:
        # 現在の日付を取得
        current_date = datetime.now().strftime("%Y%m%d")
        
        # 'text'フォルダと日付フォルダを作成
        folder_path = os.path.join('data', current_date)
        os.makedirs(folder_path, exist_ok=True)

        # インデックスを使用してファイル名を生成
        filename = os.path.join(folder_path, f"yahoo_news{index:02d}.txt")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"記事を '{filename}' に保存しました。")
    except IOError as e:
        raise IOError(f"ファイルの保存中にエラーが発生しました: {e}")
    except Exception as e:
        raise Exception(f"SAVE予期せぬエラーが発生しました: {e}")
    return


def is_valid_url(url):
    """
    概要：引数に文字列を受けてURL文字列かどうかをチェックする
    引数：
        url(str)URL文字列
    戻り値：
        bool    True=URL文字列, False=URL文字列でない
    """   
    pattern = re.compile(
        r'^(https?:\/\/)'  # http:// または https://
        r'([a-zA-Z0-9.-]+)'  # ドメイン名
        r'(:\d+)?'  # ポート番号（オプション）
        r'(\/[^\s]*)?$',  # パス（オプション）
        re.IGNORECASE  # 大文字小文字を無視
    )
    return re.match(pattern, url) is not None 




if __name__ == "__main__":
    # Yahoo!ニュースのトップページURL
    test_url = "https://news.yahoo.co.jp/"

    RANKING_URL = "https://news.yahoo.co.jp/ranking/access/news/it-science"
    print("テスト開始: get_article_from_url 関数")
    success, message = get_article_from_url(RANKING_URL)
    
    print(success, message)