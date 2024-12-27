import sys
import os
import re
import get_article_from_url as gaf
import get_frequently_occurring_characters as gfoc
import write_to_excel as wte


def delete_yahoo_news_txt(data_folder='data'):
    """
    概要：ソーステキストファイルの格納されているフォルダをフォルダごと削除します。
    フォルダ名はyyyyMMdd
    該当フォルダには「yahoo_news連番.txt」(連番=01,02,...)のファイルがあり、
    テキストファイルがすべて消去できた場合は該当フォルダも消去します
    引数：data_foler(str, optional)
        data_folder:ソースファイルの格納されているフォルダの相対パスを指定。初期値：data
    戻り値：(is_success:bool, message: str)
        is_success: 成否を返す1(True)成功、0(False)失敗
        message: エラーメッセージ
    """
    #処理結果メッセージ
    message ="成功"
    #成否フラグ
    is_success = 0
    try:
        # 指定されたフォルダ内の全てのエントリをループ
        for folder_name in os.listdir(data_folder):
            folder_path = os.path.join(data_folder, folder_name)
            # フォルダ名がyyyyMMdd形式かを確認
            if len(folder_name) == 8 and folder_name.isdigit() and os.path.isdir(folder_path):
                # フォルダ内の「yahoo_news連番.txt」ファイルを削除
                files_deleted = True
                for file_name in os.listdir(folder_path):
                    if re.match(r"yahoo_news\d{2}\.txt$", file_name):
                        file_path = os.path.join(folder_path, file_name)
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"ファイル削除に失敗しました: {file_path}, エラー: {e}")
                            files_deleted = False
                
                # すべての該当ファイルが削除できた場合にフォルダを削除
                if files_deleted:
                    try:
                        os.rmdir(folder_path)
                    except OSError:
                        # yahoo_news連番.txt以外のファイルが存在する場合はフォルダは削除しません
                        pass
        is_success = 1
        return is_success, message
    except Exception as e:
        is_success = 0
        message = f'エラーが発生しました: {e}'
        return is_success, message


if __name__ == "__main__":

    RANKING_URL = "https://news.yahoo.co.jp/ranking/access/news/it-science"
    TEMPLATE_FILE_NAME = "yahoo_news.xlsx"
    
    print("yahooNews分析用データの自動生成プログラム")
    print("開始")

    # yahooニュースサイトのアクセスランキングから記事情報をスクレーピング
    is_success, mess = gaf.get_article_from_url(RANKING_URL)
    if is_success==0:
        print("スクレーピング中にエラーが発生しました:", mess)
        sys.exit()

    # スクレーピング結果をもとに形態素解析を行い、頻出する名詞を抽出
    is_success, mess, df = gfoc.get_frequently_occurring_characters()
    if is_success==0:
        print("形態素解析中にエラーが発生しました:", mess)
        sys.exit()

    # 名詞の抽出結果をExcelの所定フォーマットに出力
    is_success, mess = wte.write_to_excel(TEMPLATE_FILE_NAME, df)
    if is_success==0:
        print("Excelファイル出力中にエラーが発生しました:", mess)
        sys.exit()

    # ソーステキストファイルの削除
    is_success, mess = delete_yahoo_news_txt()
    if is_success==0:
        print("ソースファイルの削除に失敗しました: ", mess)

    print("終了")