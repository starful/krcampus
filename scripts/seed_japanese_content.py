#!/usr/bin/env python3
"""Seed *_ja.md from English sources without Gemini (offline Japanese copy)."""
import glob
import json
import os

import frontmatter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(BASE, "app", "content")

GUIDE_JA = {
    "visa": {
        "title": "韓国留学ビザ完全ガイド（D-2・D-4）",
        "description": "語学留学・学位取得のためのD-4・D-2ビザ手続きをステップごとに解説します。",
        "category": "ビザ",
        "body": """## 概要

韓国留学では、**D-4（語学研修）** または **D-2（留学）** ビザを利用するのが一般的です。

## D-4 語学研修ビザ

1. 語学堂に合格する
2. 学校からビザ書類（標準入学許可書など）を受け取る
3. 在韓大使館・領事館でビザ申請
4. 入国後90日以内に外国人登録証（ARC）を取得

## D-2 学位課程ビザ

大学合格後に取得します。合格通知、財政能力証明、健康診断書などが必要です。

## 入学時期と目安

| 入学 | 申請目安 |
|------|----------|
| 3月 | 前年11〜12月 |
| 9月 | 同年5〜6月 |
""",
    },
    "cost": {
        "title": "ソウル1年留学の費用目安",
        "description": "授業料・生活費を含む、ソウルでの1年間のリアルな予算を解説します。",
        "category": "予算",
        "body": """## 概要

ソウル留学の1年間の費用は、**授業料＋生活費** でおおむね **800〜1,500万ウォン** が目安です。

## 内訳の目安

| 項目 | 年間目安（ウォン） |
|------|-------------------|
| 語学堂（4クール） | 600〜800万 |
| 生活費 | 400〜700万 |
| 保険・その他 | 50〜100万 |

## 節約のポイント

- 学校寮を利用すると家賃を抑えられます
- 自炊と大学食堂を活用
- 交通系ICカード（T-money）で移動費を管理
""",
    },
    "housing": {
        "title": "韓国の学生向け住居：寮・ゴシウォン・アパート",
        "description": "語学堂生・大学生向けの住居タイプを比較し、選び方を解説します。",
        "category": "住居",
        "body": """## 住居タイプ比較

| タイプ | 月額目安 | メリット |
|--------|----------|----------|
| 学校寮 | 30〜60万ウォン | 安心・近い |
| ゴシウォン | 25〜45万ウォン | 初期費用が低い |
| ワンルーム | 50〜80万ウォン | プライベート確保 |

## 選び方

- 初めての留学は**寮またはゴシウォン**がおすすめ
- 長期滞在なら契約前に管理費・保証金を確認
- 学校から30分以内の立地を優先
""",
    },
    "school-choice": {
        "title": "韓国語学堂の選び方5つの基準",
        "description": "目的・立地・クラス規模・TOPIK対策・費用から語学堂を選ぶ方法。",
        "category": "選校",
        "body": """## 5つの選び方

1. **目的** — 会話・TOPIK・大学進学のどれが主目的か
2. **立地** — ソウル（新村・江南）か釜山か
3. **クラス規模** — 少人数クラスか大規模校か
4. **進学サポート** — 大学説明会・推薦制度の有無
5. **費用** — 10週間あたり150〜200万ウォンの相場を確認

## チェックリスト

- 定員・国籍比率
- 寮の有無
- TOPIK対策クラス
- 卒業生の進学実績
""",
    },
    "scholarship": {
        "title": "韓国留学の奨学金ガイド",
        "description": "GKS（KGSP）や大学奨学金など、留学生向け支援制度の概要。",
        "category": "予算",
        "body": """## 主な奨学金

| 制度 | 対象 | 内容 |
|------|------|------|
| GKS（KGSP） | 学位課程 | 授業料・生活費・航空券 |
| 大学独自 | 学部・大学院 | 入学金減免〜全額 |
| 語学堂 | 語学研修 | 成績優秀者割引 |

## 申請のコツ

- 大学公式サイトで締切を早めに確認
- TOPIK・英語スコアを準備
- 推薦状・学習計画書を日本語または英語で用意
""",
    },
    "arrival": {
        "title": "韓国到着後1週間チェックリスト",
        "description": "入国直後に必要なARC・SIM・銀行口座などの手続き一覧。",
        "category": "準備",
        "body": """## 到着後すぐに

1. **SIMカード** — 空港または大学近くで開通
2. **T-money** — 地下鉄・バス用ICカード
3. **住居確認** — 寮または契約書の控えを保管

## 1週間以内

- **外国人登録証（ARC）** — 入国後90日以内が期限
- **銀行口座** — パスポートとARC（または入学証明）
- **キャンパスオリエンテーション** — 出席必須の場合あり

## 持ち物

パスポート、入学許可書、住居証明、証明写真（3×4cm）
""",
    },
    "part-time": {
        "title": "韓国留学中のアルバイトルール",
        "description": "D-2・D-4ビザでの就労時間制限と一般的なバイトの種類。",
        "category": "アルバイト",
        "body": """## 就労時間の目安

| ビザ | 条件 | 時間 |
|------|------|------|
| D-2 | 大学在籍・許可取得後 | 週20時間以内 |
| D-4 | 語学堂6ヶ月以降・許可必要 | 週20時間以内 |

## よくある仕事

カフェ、コンビニ、翻訳・通訳、大学内TA

## 注意

- **許可なし就労はビザ取消の原因**になります
- 入国後一定期間はアルバイト不可の場合あり
- 学校の国際交流室に相談
""",
    },
    "insurance": {
        "title": "韓国の国民健康保険（留学生向け）",
        "description": "留学生の健康保険加入条件・保険料・病院利用方法。",
        "category": "保険",
        "body": """## 概要

6ヶ月以上滞在する留学生は**国民健康保険（NHI）** への加入が義務です。

## 保険料

- 月額おおむね **6〜8万ウォン** 前後（滞在状況により変動）
- 病院受診時、自己負担は約30%

## 手続き

1. ARC取得後、NHIS（国民健康保険公団）に登録
2. オンラインまたは区役所で手続き可能
3. 学校の案内に従うとスムーズ
""",
    },
    "bank": {
        "title": "留学生の韓国銀行口座開設ガイド",
        "description": "主要銀行の口座開設に必要な書類とおすすめの選び方。",
        "category": "生活",
        "body": """## 必要書類

- パスポート
- 外国人登録証（ARC）または入学証明書
- 韓国の電話番号

## 主要銀行

| 銀行 | 特徴 |
|------|------|
| KB国民 | ATMが多い |
| 新韓 | 留学生向け窓口あり |
| ウリ | 英語対応アプリ |

## ヒント

- 学校近くの支店を選ぶ
- 通帳なし口座＋デビットカードが一般的
""",
    },
    "mobile": {
        "title": "留学生向けSIM・携帯プラン比較",
        "description": "短期〜長期滞在向けのプリペイドSIM、eSIM、キャリア契約。",
        "category": "生活",
        "body": """## 選択肢

| タイプ | 向いている人 |
|--------|--------------|
| 空港プリペイド | 到着直後すぐ使いたい |
| eSIM | スマホ対応・短期 |
| SKT/KT/LG U+ | 6ヶ月以上・データ多め |

## 目安料金

- プリペイド：3〜5万ウォン/月
- 後払い契約：4〜7万ウォン/月

## 注意

パスポート提示が必要。ARC取得後に名義変更できる場合あり。
""",
    },
    "seoul-region": {
        "title": "ソウル vs 釜山：留学先の選び方",
        "description": "費用・大学数・生活スタイルから見た都市比較。",
        "category": "地域",
        "body": """## 比較

| 項目 | ソウル | 釜山 |
|------|--------|------|
| 生活費 | 高め | やや安い |
| 大学・語学堂 | 最多 | 充実 |
| 英語環境 | やや多い | 中程度 |
| 気候 | 四季・夏暑 | 海沿い・湿度 |

## 向いている人

- **ソウル** — 進学・就職・都会生活
- **釜山** — コスト重視・海の近くで落ち着いて学びたい
""",
    },
    "topik": {
        "title": "TOPIK試験ガイド：級・日程・対策",
        "description": "TOPIK I・IIの級、試験日程、大学進学に必要なスコア目安。",
        "category": "試験",
        "body": """## TOPIKとは

韓国語能力試験。**TOPIK I**（初級）と **TOPIK II**（中上級）があります。

## 大学進学の目安

| 課程 | 目安スコア |
|------|------------|
| 学部（韓国語） | TOPIK 3〜4級以上 |
| 大学院 | TOPIK 5〜6級 |
| 英語プログラム | TOPIK不要の場合あり |

## 対策のコツ

- 過去問を月1回は解く
- 語彙・文法・読解・聴解をバランスよく
- 語学堂のTOPIKクラスを活用
""",
    },
}

SCHOOL_JA = {
    "school_yonsei-kli": {
        "title": "延世大学韓国語学堂 — 語学プログラムガイド",
        "description": "ソウル新村キャンパスで韓国語を学ぶ、延世大学韓国語学堂の概要。",
        "features": ["TOPIK対策", "大学進学サポート", "寮あり"],
        "body": """## 学校概要

延世大学韓国語学堂（연세대학교 한국어학당）は、韓国留学で最も人気のある語学プログラムの一つです。ソウル・新村に位置し、韓国大学への進学を目指す留学生が多く集まります。

## プログラム

- **正規集中コース** — 200時間/レベル、年4回入学
- **TOPIK対策** — I・II級向け特化クラス
- **夜間コース** — すでに韓国在住の学習者向け

## 選ばれる理由

| 要素 | 内容 |
|------|------|
| 立地 | 新村 — 大学街・交通至便 |
| 実績 | 長い歴史と進学実績 |
| 活動 | 文化体験・留学生イベント |

## 出願のヒント

3月・9月入学は早めの申込が必要です。パスポート、卒業証明、残高証明をD-4ビザ用に準備しましょう。
""",
    },
    "school_snu-lei": {
        "title": "ソウル大学校 語学教育院 — 語学プログラム",
        "description": "韓国最高学府の冠岳キャンパスで学ぶ、学術韓国語プログラム。",
        "features": ["学術韓国語", "SNUキャンパス利用", "TOPIK対策"],
        "body": """## 学校概要

ソウル大学校語学教育院は、冠岳（クァナク）本キャンパスで体系的な韓国語プログラムを提供しています。学術韓国語と将来の学位取得を目指す学生に適しています。

## 特徴

- 大学レベルに合わせた厳密なカリキュラム
- 図書館・キャンパス施設の利用
- 意欲的な留学生コミュニティ

## 費用目安

10週間あたり **150〜200万ウォン** ＋ 冠岳周辺の住居費

## ビザ

多くの学生は **D-4（語学研修）** で入国し、のちにD-2へ切り替えます。
""",
    },
    "univ_yonsei-university": {
        "title": "延世大学 — 留学生入学ガイド",
        "description": "ソウル・延世大学の留学生向け学部・UICプログラム概要。",
        "features": ["英語学士プログラム", "新村キャンパス", "GKS対象"],
        "body": """## 大学概要

延世大学はソウル・新村にある名門私立大学で、Underwood International College（UIC）など国際プログラムで知られています。

## 延世を選ぶ理由

- 大規模な留学生コミュニティ
- 英語トラック学位あり
- ソウルでの就職・インターン機会

## 出願チェックリスト

1. 韓国語トラックか英語トラックかを決める
2. 成績証明・語学スコアを準備
3. 延世大学国際入学ポータルから申請
4. 合格後D-2ビザを取得
""",
    },
    "univ_seoul-national-university": {
        "title": "ソウル大学校 — 留学生入学ガイド",
        "description": "韓国国立大学の最高峰、ソウル大学の留学生向け入学情報。",
        "features": ["GKS対象", "英語履修科目", "寮あり"],
        "body": """## 大学概要

ソウル大学校（SNU）は韓国を代表する国立大学で、冠岳キャンパスに位置します。英語履修科目も増えており、留学生向け支援が充実しています。

## 国際入学

- **語学要件** — TOPIKまたは英語（プログラムによる）
- **ビザ** — 合格後D-2留学ビザ
- **奨学金** — GKS、SNUグローバル奨学金

## 学費目安（年間・ウォン）

| 項目 | 金額 |
|------|------|
| 入学金 | 約100万 |
| 授業料 | 約400万〜 |

## キャンパスライフ

冠岳キャンパスは研究施設・寮・ソウル都心へのアクセスが整っています。
""",
    },
}


def _dump(meta: dict, body: str) -> str:
    return frontmatter.dumps(frontmatter.Post(body, **meta))


def seed_guide(slug: str, ja: dict) -> None:
    src = os.path.join(CONTENT, f"guide_{slug}.md")
    if not os.path.isfile(src):
        return
    post = frontmatter.load(src)
    meta = dict(post.metadata)
    meta["lang"] = "ja"
    meta["title"] = ja["title"]
    meta["description"] = ja["description"]
    meta["category"] = ja["category"]
    if meta.get("tags"):
        meta["tags"] = [ja["category"]]
    out = os.path.join(CONTENT, f"guide_{slug}_ja.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(_dump(meta, ja["body"].strip() + "\n"))
    print(f"  guide_{slug}_ja.md")


def seed_school(file_id: str, ja: dict) -> None:
    src = os.path.join(CONTENT, f"{file_id}.md")
    if not os.path.isfile(src):
        return
    post = frontmatter.load(src)
    meta = dict(post.metadata)
    meta["lang"] = "ja"
    meta["title"] = ja["title"]
    meta["description"] = ja["description"]
    meta["features"] = ja["features"]
    basic = dict(meta.get("basic_info") or {})
    basic["name_ja"] = ja["title"].split(" — ")[0].split(" —")[0]
    meta["basic_info"] = basic
    out = os.path.join(CONTENT, f"{file_id}_ja.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(_dump(meta, ja["body"].strip() + "\n"))
    print(f"  {file_id}_ja.md")


def main():
    print("Seeding Japanese guides...")
    for slug, ja in GUIDE_JA.items():
        seed_guide(slug, ja)

    print("Seeding Japanese schools/universities...")
    for file_id, ja in SCHOOL_JA.items():
        seed_school(file_id, ja)

    count = len(glob.glob(os.path.join(CONTENT, "*_ja.md")))
    print(f"Done. {count} *_ja.md files in content/")


if __name__ == "__main__":
    main()
