# weekly_reports
## 背景
### 大学受験塾の個別指導バイト
私がやっていた大学受験塾の個別指導バイトでは、生徒に進捗管理と週あたりの振り返りを行っていた。
その個別指導で生成されるレポートには、以下の内容が含まれていた。
- 先週の宿題と、取り組みのステータス
- 来週までの1日ごとの宿題
- 先週の取り組みの良かったところ
- 先週の取り組みの悪かったところ、その原因、その改善策
- 来週の目標
- １ヶ月ごとの中期目標
- 長期的な目標

このフォーマットは、私でも活用できるのではないかと考えた。
私はタスク管理、スケジュール管理、そしてその振り返りのやり方が全く定まっていない。
Notionや個別のアプリケーションにそれぞれの機能を分けている。しかし、これでは参照すべきところが増え、煩雑になる。
これを1つのアプリケーションに集約することを目的とする。
その上で、すでに使いやすい、機能を十分に満たしうるシステムが運営され、自分も日常的に使っているものがある。このアイデアを流用しようというのが、本システムの着想である．

## 実装
大学受験勉強用のフォーマットを、タスク管理用に変化させる．
前提として、上記の個別指導では、生徒と先生の１体１で週に1時間程度話し合い、作成していた。
今回のシステムも、週に1時間振り返りの時間を設定し、先週の振り返り、来週のタスク設定、スケジュール設定全てを行うことを前提とする。

## 現在の実装
- 週報のデータモデル（WeekReport / Day / Task / TaskSession）をJSONで扱う
- 金曜18:00のレビュー起点で翌週（土曜開始）の週報を自動生成
- 週報を確定すると、スナップショットJSONとPDFを出力

## 使い方
### 1. 依存関係のインストール
```bash
pip install -e .
```

## 環境構築・起動方法
本プロジェクトはPython 3.10以上を前提としています。以下の手順で環境構築と起動（コマンド実行）ができます。

1. リポジトリをクローンして移動します。
```bash
git clone <REPO_URL>
cd weekly_reports
```

2. 仮想環境を作成して有効化します。
```bash
python -m venv .venv
source .venv/bin/activate
```

3. 依存関係をインストールします。
```bash
pip install -e .
```

4. CLIを起動（実行）します。
```bash
weekly-report --help
```

## GUI（バックエンド + フロントエンド）の起動方法
### 1. バックエンドAPIの起動（FastAPI）
別ターミナルで以下を実行します。
```bash
weekly-report-api
```
`http://localhost:8000/api/health` で起動確認できます。

### 2. フロントエンドの起動（React + Vite）
別ターミナルで以下を実行します。
```bash
cd frontend
npm install
npm run dev
```
`http://localhost:5173` にアクセスするとGUIが表示されます。

### 2. 週報の初期生成
金曜18:00のレビュー日時を指定して、翌週の週報を初期化します。

```bash
weekly-report init-week --review-at 2026-01-16T18:00:00 --output week_report.json
```

前週の週報がある場合は、`--prev` を指定すると目標（週/月/長期）が引き継がれます。

```bash
weekly-report init-week --review-at 2026-01-16T18:00:00 --prev week_report_prev.json
```

### 3. 週報の記入
`week_report.json` にタスクやセッションを記入します。JSON構成は `example_report.json` を参照してください。

### 4. 確定・出力
```bash
weekly-report finalize week_report.json --output-dir outputs
```

- `outputs/{week_id}_snapshot.json` にスナップショットJSONを出力
- `outputs/{week_id}_weekly_report.pdf` にPDFを出力
- `week_report_final.json` に確定済みの週報を保存

## JSONスキーマ（概要）
主要なトップレベルキー:
- `week_report`: 週報ヘッダ（期間・レビュー日時・目標など）
- `days`: 日付行（7日分）
- `tasks`: 週内タスク（day_id で日付行に紐付け）
- `task_sessions`: タスク実行枠
- `last_week_tasks`: 先週の実績タスク

## ファイル構成
- `weekly_reports/cli.py`: CLIエントリーポイント
- `weekly_reports/models.py`: データモデルと入力バリデーション
- `weekly_reports/metrics.py`: 日付行の集計ロジック
- `weekly_reports/pdf.py`: PDF出力
- `weekly_reports/snapshot.py`: スナップショットJSON生成
