import os
import re
import pandas as pd
from collections import Counter
from janome.tokenizer import Tokenizer
from janome.analyzer import Analyzer
from janome.tokenfilter import *
from janome.charfilter import *



def get_frequently_occurring_characters(count=30):
    """概要：出現回数が多い単語を抽出する関数

    引数:
        count (int, optional):出現回数が多い単語を抽出する機能を提供し、デフォルトでは 30個 の単語を抽出します.

    戻り値:is_success: bool, message: str, df: DataFrame
        is_success: 成功=1、失敗=0
        message: 成否メッセージ
        DataFrame: 集計結果。(Columns=(["単語","回数"]))
    """
    
    #処理結果メッセージ
    message ="成功"
    #成否フラグ
    is_success = 0

    def extract_noun_counts(file_path):
        """概要：名詞を抽出し、頻度をカウントする関数

        引数:
            file_path (_type_):名詞を抽出したいテキストファイルのパス

        戻り値:
            DataFrame：名詞とその出現回数を格納したDataFrame
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            article_text = file.read()
    
        # アナライザーを使用して名詞を抽出
        nouns = [token.surface for token in analyzer.analyze(article_text) if token.part_of_speech.startswith('名詞')]
    
        # 名詞の頻度をカウント
        noun_counts = Counter(nouns)
    
        return pd.DataFrame(noun_counts.items(), columns=['単語', '回数'])

    def get_yahoo_news_paths(data_folder='data'):
        """
        概要：janome解析するソーステキストファイルのパスのリストを配列で返します。
        ソーステキストファイルはファイル名が「yahoo_news連番.txt」(連番=01,02,...)のものとする。
        引数：
            data_folder:ソースファイルの格納されているフォルダの相対パスを指定。初期値：data
        戻り値：
            Array：テキストファイルのパスのリストが格納された配列を返す。
        """
        # 戻り値用配列のクリア
        file_paths = []
        # 最新のフォルダ判別用変数
        latest_folder = None
        latest_time = None
        # 指定フォルダ以下のファイル・フォルダリストを取得
        for folder_name in os.listdir(data_folder):
            # 日付フォルダを取得(例：20240919)
            if len(folder_name) == 8 and folder_name.isdigit():
                # 日付フォルダの絶対パスを取得
                folder_path = os.path.join(data_folder, folder_name)
                # フォルダの最終更新日時を取得
                folder_time = os.path.getmtime(folder_path)
                
                # 最新のフォルダを更新
                if latest_time is None or folder_time > latest_time:
                    latest_time = folder_time
                    latest_folder = folder_path

        # 最新の日付フォルダ内のファイルをループ
        if latest_folder:
            for file_name in os.listdir(latest_folder):
                # ファイル名が「yahoo_news連番.txt」のものを取得
                if re.match(r'yahoo_news\d{2}\.txt$', file_name):
                    # ファイルパスを戻り値用配列に格納
                    file_paths.append(os.path.join(latest_folder, file_name))

        return file_paths

    try:
        tokenizer = Tokenizer()
        # 英字の "I" や疑問符、記号などを削除 参照：list_0913.xlsx
        char_filters = [
            UnicodeNormalizeCharFilter(),
            RegexReplaceCharFilter(r"[Ⅰｉ?.%*/~=()〝 <>:：,+《°!！!？（）-]+", "")
        ]
        
        # 名詞のみを対象にフィルタリング。名詞,非自立, 名詞,数, 名詞,代名詞, 名詞,接尾などは解析対象外。
        token_filters = [
            POSKeepFilter(["名詞"]),
            POSStopFilter([
                "名詞,接尾,人名",
                "名詞,接尾,一般", 
                "名詞,接尾,助数詞", 
                "名詞,数",
                "名詞,代名詞,一般",
                "名詞,非自立,一般",
                "名詞,非自立,助動詞語幹",
                "名詞,非自立,副詞可能",
                "名詞,接尾,助動詞語幹",
                "名詞,接尾,特殊",
                "名詞,接尾,副詞可能", 
                "名詞,接尾,形容動詞語幹", 
                "名詞,副詞,可能"
            ]),
            LowerCaseFilter() # すべての単語を小文字化。これにより、大文字・小文字の違いにかかわらず同じ単語として処理。
        ]
        
        # フィルタリングされたテキストデータを処理
        analyzer = Analyzer(
            char_filters=char_filters,
            tokenizer=tokenizer,
            token_filters=token_filters
        )

        # ファイルパスを取得
        data_folder = get_yahoo_news_paths()
        
        # 集計結果格納DataFrameの初期化
        sumDf = pd.DataFrame()

        # ファイルパス配列をループ
        for file_path in data_folder:
            # ファイルパスが存在するか確認
            if os.path.exists(file_path):
                df = extract_noun_counts(file_path)
                sumDf = pd.concat([sumDf, df], ignore_index=True)
            else:
                raise FileNotFoundError(f"{file_path} が見つかりませんでした。")

        # 出現回数を合計して名詞でグループ化
        result = sumDf.groupby('単語', as_index=False).agg({'回数': 'sum'})
        
        # 出現回数で降順にソート

        result_sorted = result.sort_values(by='回数', ascending=False)
        
        # 出現回数の順位を計算し、同一回数に同順位を付与する
        result_sorted['順位'] = result_sorted['回数'].rank(method='min', ascending=False)
        
        # 上位30位までを抽出（同順位を含むため、30位以内で抽出）
        top_30 = result_sorted[result_sorted['順位'] <= count]
        
        # 順位で再度ソート
        top_30_sorted = top_30.sort_values(by='順位')
        
        df_dropped = top_30_sorted.drop(columns='順位')
        
        is_success = 1
        return is_success, message, df_dropped

    except FileNotFoundError as fnf_error:
        is_success = 0
        message = f"ファイルが見つかりませんでした: {fnf_error}"
        #print(message)
        return is_success, message, None

    except Exception as e:
        is_success = 0
        message = f"予期せぬエラーが発生しました: {str(e)}"
        #print(e)
        return is_success, message, None

if __name__=="__main__":
    flg, mess, df = get_frequently_occurring_characters()
    if flg:
        print("成功")
        print(df)
    else:
        print("失敗: ", mess)
