# tw-lambda-claude
AWS Bedrock上のclaudeをlambdaを使ってツイート文を生成
投稿した内容について1回だけリプライをする

# 環境構築など
- Twitter API
- AWS BedRockでClaudeの利用申請
- requests_oauthlibのlambdaレイヤー

# プロンプトテクニック(for claude)
- XML形式で学習しているので、その形式で指示
- 以下の順がいいっぽい
prompt_start(開始文言) + prompt_doc（関連ドキュメント) + prompt_inst(指示文言) + prompt_ques(質問事項) + prompt_end(終了文言)
