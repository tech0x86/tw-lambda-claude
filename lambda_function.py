import json
import boto3
from botocore.config import Config
import os
import time
from requests_oauthlib import OAuth1Session
from datetime import datetime, timedelta, timezone
import csv
from botocore.exceptions import ClientError
import random

bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1",config=Config(read_timeout=600))

# start,end are const value
prompt_start ="""
Human:

"""
prompt_end = """

Assistant:
"""

# 日付に基づく回答制御
prompt_inst1 = """
<instructions>
あなたは指示された日付から今日は日本の何の日かを指定のキャラクターになりきって答える優秀なアシスタントです。
以下のルールを必ず守って答えること。
<rule>
・指示されている内容は回答に含めないこと。
・140文字以内かつ100文字程度で答えること。
・eventが複数ある場合はそのキャラクターが興味がありそうなものを選ぶこと（複数でも可)
・答えた後、そのキャラクターの名前を次のように追記すること。例: text char_name
</rule>
</instructions>
"""

# 感想への回答制御
prompt_inst2 = """
<instructions>
あなたは提示された友達の発言に対して指定のキャラクターになりきって答える優秀なアシスタントです。
以下のルールを必ず守って答えること。
<rule>
・指示されている内容は回答に含めないこと。
・140文字以内かつ100文字程度で答えること。
・答えた後、そのキャラクターの名前を次のように追記すること。例: text char_name
</rule>
</instructions>
"""

prompt_doc_aoba="""
<document>
<char_name>
青葉
</char_name>
<point>
・新卒のゲームデザイナー
・ゲームが大好き
・熱心でポジティブな性格
・好物： おせんべいやようかんなど、和風のおかし、ハンバーグ
・苦手なもの： 辛いもの、苦いもの、刺激物系。運動全般
</point>
<personal_info>
仕事や人間関係のことで思い悩むこともあるが基本は素直で前向き思考。コミュニケーション能力に秀でており、気配り上手で、誰とでも話せて仲良くなれる。口下手である滝本ひふみとも打ち解け、トゲのある態度を取りがちな阿波根うみこからも気に入られサバゲに誘われている。
天然な面があり、子どもっぽい思考も持つ。そのため度々危なっかしい事をやってしまう時も。コウが下半身パンツ一丁で寝ている事には度々注意している。
仕事への熱意・責任感はとても高い。大幅残業もなんのその、会社での泊まり込みでもウキウキしながら買ってきた寝袋を広げている。知識習得への意欲も高く、他者からのアドバイスは逃さずメモに取っている。物覚えもよく、全くのゼロ知識からコウも認めるレベルのキャラ造形を用意出来るほどのモデリング技術に至っている。
運動神経は壊滅的。走行スピードは遅くすぐにバテ、走ったら盛大にズッコケる。小さな雪だるまを作ってサウナに持ち込むやや特殊な嗜好がある。酒に弱く、ウィスキーボンボンで酔っぱらう。二十歳記念にお酒を飲んだが、当然酔った。コーヒーは苦手で、ブラックでは飲めない。
</personal_info>
<talking_list>
「私、夢だったんです！ここで働くの！」「分からないことだらけだけど、頑張ります！」
「みんなと一緒に作るゲーム、楽しみにしています！」「もっとゲーム作り上手になりたいな」「コーヒー！ ブラックで！」「なんでそんなサラサラッと一瞬でイイの描くんですか。嫌味ですか」
「まさか正社員って、お給料安くするための法の抜け穴……？」
「最悪です！ 八神さん、大っ嫌いです！！」
</talking_list>
</document>

"""

prompt_doc_kudo="""
<document>
<char_name>
クドリャフカ
</char_name>
<point>
・アニメ「リトルバスターズ」の登場キャラクター。妹系のキャラクター。
・とっても元気で、明るい性格。でも、ちょっぴり不器用。
</point>
<personal_info>
・誰に対しても敬語で話し、文法を無視して語尾に「です」や「なのです」を付ける口調や、「わふー」という口癖が特徴。例：「そうしましょーなのです」
・現在校内で風紀委員の活動を手伝っている『ストレルカ』『ヴェルカ』という二匹の犬を小さい頃から育ててきた飼い主。
</personal_info>
<talking_list>
「ぐっもーにん、えぶりわん。はぶ、あ、ないすでい！私、能美クドリャフカと言います！外国に居たので日本の事はよくわかりません。なので、色々教えて欲しいのです。わふー」
「私、小さな時から引っ越しばかりで仲のいいお友達がいなくて…。だから、ぜひ、あなたにお友達になっていただけたらいいなぁ…って。め、迷惑でしょうか？」
「この子達ですか？フィンランドに住むおじい様が寂しくないようにって送ってくれたんです。ストレルカとヴェルカと言うのです。ちーっちゃい時から知ってるんです！なので、私がお姉さんです！」
「わふ～！いい子いい子ですか？」
「筋肉イェイイェイ」
</talking_list>
</document>

"""

def exponential_backoff(attempt, base_delay=10, max_delay=30):
    """Calculate exponential backoff with jitter"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, 0.1 * delay)
    return delay + jitter


def setup_environment():
    ssm = boto3.client('ssm')
    twitter_sec = json.loads(ssm.get_parameter(Name='twitter_sec', WithDecryption=True)['Parameter']['Value'])
    twitter = OAuth1Session(twitter_sec["CK"], client_secret=twitter_sec["CS"], resource_owner_key=twitter_sec["AT"], resource_owner_secret=twitter_sec["AS"])
    return twitter
    
# 日付と日付に基づくキャラクターの選択
def choose_character():
    jst_timezone = timezone(timedelta(hours=9))  # JSTタイムゾーンの設定
    current_date = datetime.now(jst_timezone).strftime("%m月%d日")
    day = datetime.now(jst_timezone).day
    #current_date = '12月10日'
    char_set = "青葉" if day % 2 == 0 else "クドリャフカ"
    return current_date, char_set

def get_current_date_ymd():
    # JSTタイムゾーンの設定
    jst_timezone = timezone(timedelta(hours=9))
    # 現在の日付をYYYY-MM-DD形式で取得
    current_date_ymd = datetime.now(jst_timezone).strftime('%Y-%m-%d')
    #current_date_ymd = '2024-12-10'
    return current_date_ymd

def generate_response_with_retry(prompt_doc="", prompt_inst="", prompt_ques="", max_retries=4):
    prompt = prompt_start + prompt_doc + prompt_inst + prompt_ques + prompt_end
    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 140,
        "temperature": 0.9,
        "top_k": 250,
        "top_p": 1,
    })

    for attempt in range(max_retries + 1):
        try:
            resp = bedrock_runtime.invoke_model(
                #modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
                modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                contentType="application/json",
                accept="application/json",
                body=body,
            )
            answer = resp["body"].read().decode()
            completion = json.loads(answer)["content"][0]['text']
            print(f"Success after {attempt} retries")
            return completion

        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt == max_retries:
                    print(f"Max retries ({max_retries}) exceeded")
                    raise
                
                delay = exponential_backoff(attempt)
                print(f"Throttled. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                continue
            else:
                raise


# ツイート送信　tweet_idでリプライ指定も可
def tweet_text_only(twitter, text, reply_to_id=None):
    tweet_data = {"text": text}
    if reply_to_id:
        tweet_data["reply"] = {"in_reply_to_tweet_id": reply_to_id}
    headers = {"Content-Type": "application/json"}
    response = twitter.post("https://api.twitter.com/2/tweets", headers=headers, data=json.dumps(tweet_data))
    if response.status_code not in [200, 201]:
        raise Exception(f"Tweet post failed: {response.status_code}, {response.text}")
    tweet_id = response.json()["data"]["id"]
    print(f"Tweeted: {tweet_id}")
    return tweet_id

def set_event_date_to_prompt(event):
    prompt_start_event="""
    <document>
    <title>このドキュメントは日本のその日の記念日をdate,event形式で表現したものです。eventは複数ある場合は半角スペースで区切られています。</title>
    <content>
"""
    prompt_end_event="""
    </content>
    </document>
"""
    return prompt_start_event + str(event) + prompt_end_event
    
def get_month_event_data(target_date):
    # S3クライアントを作成
    s3 = boto3.client('s3')

    # 指定日付の形式をチェック
    try:
        target_date = datetime.strptime(target_date, '%Y-%m-%d')
    except ValueError:
        print("invalid target_date")
        return {'statusCode': 400, 'body': 'Invalid date format. Please provide YYYY-MM-DD.'}

    # 指定日付の月を取得
    month = target_date.month
    # ファイル名を作成
    file_name = f'2024{month:02d}_event.csv'
    print(f"file: {file_name}")

    # S3からファイルを読み込む
    try:
        response = s3.get_object(Bucket='tweet-some-data', Key=f'event/{file_name}')
        event_data = response['Body'].read().decode('utf-8')
    except s3.exceptions.NoSuchKey:
        print(f"statusCode: 404 File not found: {file_name}")
        return {'statusCode': 404, 'body': f'File not found: {file_name}'}

    reader = csv.DictReader(event_data.splitlines(), fieldnames=['date', 'event'])
    events = {row['date']: row['event'] for row in reader}
    print(str(events))

    return events

def lambda_handler(event, context):
    try:
        twitter = setup_environment()
        current_date, char_set = choose_character()
        event = get_month_event_data(get_current_date_ymd())
        prompt_event = set_event_date_to_prompt(event)
        
        prompt_ques_char_day = f"{current_date} char_name: {char_set} "
        print(prompt_ques_char_day)
        
        if char_set == "青葉":
            prompt_doc = prompt_doc_aoba
        else:
            prompt_doc = prompt_doc_kudo
            
        response_char_day = generate_response_with_retry(
            prompt_doc + prompt_event,
            prompt_inst1,
            prompt_ques_char_day
        )
        print(response_char_day)
        tweet_id1 = tweet_text_only(twitter,response_char_day)
        
        # Add delay between API calls
        time.sleep(1)
        
        if char_set == "青葉":
            prompt_doc = prompt_doc_kudo
        else:
            prompt_doc = prompt_doc_aoba
        
        response_comment = generate_response_with_retry(
            prompt_doc,
            prompt_inst2,
            response_char_day
        )
        print(response_comment)
        tweet_id2 = tweet_text_only(twitter,response_comment,tweet_id1)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "response_char_day": response_char_day,
                "response_comment": response_comment
            })
        }
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }
