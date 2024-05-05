import json
import boto3
from botocore.config import Config
import os
import time
from requests_oauthlib import OAuth1Session
from datetime import datetime, timedelta, timezone

bedrock_runtime = boto3.client("bedrock-runtime", region_name="ap-northeast-1",config=Config(read_timeout=600))

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
あなたは指示された日付から今日は日本の何の日かを指定のキャラクターになりきって答えるBotです。
以下のルールを必ず守って答えること。
<rule>
・指示されている内容は回答に含めないこと。
・140文字以内かつ100文字程度で答えること。
・答えた後、そのキャラクターの名前を次のように追記すること。例: text char_name
</rule>
</instructions>
"""

# 感想への回答制御
prompt_inst2 = """
<instructions>
あなたは提示された友達の発言に対して指定のキャラクターになりきって答えるBotです。
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
涼風 青葉
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
</talking_list>
</document>
"""

prompt_doc_kudo="""
<document>
<char_name>
能見クドリャフカ
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
</talking_list>
</document>
"""

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
    char_set = "青葉" if day % 2 == 0 else "クドリャフカ"
    return current_date, char_set

def generate_response(prompt_doc="",prompt_inst="", prompt_ques=""):
    prompt = prompt_start + prompt_doc + prompt_inst + prompt_ques + prompt_end
    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": 140,
        "temperature": 0.9,
        "top_k": 250,
        "top_p": 1,
    })

    resp = bedrock_runtime.invoke_model(
        modelId="anthropic.claude-v2:1",
        contentType="application/json",
        accept="*/*",
        body=body,
    )

    answer = resp["body"].read().decode()
    completion = json.loads(answer)["completion"]
    return completion

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

def lambda_handler(event, context):
    twitter = setup_environment()
    current_date, char_set = choose_character()
    prompt_ques_char_day = f"{current_date} char_name: {char_set} "
    if char_set =="青葉":
        prompt_doc = prompt_doc_aoba
    else :
        prompt_doc = prompt_doc_kudo
    response_char_day = generate_response(prompt_doc,prompt_inst1,prompt_ques_char_day)
    tweet_id1 = tweet_text_only(twitter,response_char_day)
    print(response_char_day)

    if char_set =="青葉":
        prompt_doc = prompt_doc_kudo
    else :
        prompt_doc = prompt_doc_aoba
    
    response_comment = generate_response(prompt_doc,prompt_inst2,response_char_day)
    tweet_id2 = tweet_text_only(twitter,response_comment,tweet_id1)
    
    print(response_comment)
    
    return {
        "statusCode": 200,
        "body": "end lambda"
        }
