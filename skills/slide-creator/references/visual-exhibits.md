# Visual Exhibits Architecture (5大作図手法の体系と選択規約)

スライドにおける図表（Exhibit: グラフ・ダイアグラム・物理プロット・概念図・フロー）の作成手法を、**「可編集性・科学的厳密性・幾何学精度・試作速度」** の観点から体系化した規約。
目的に合わない手法で無理に描くことを防ぎ、最適なパイプラインを選択する。

---

## 1. 作図手法の決定木（Decision Tree）

どの手法で図を作成すべきかは、以下のフローチャートに従って決定する。

```text
図版（Exhibit）の要件
 ├─ Q1. 発表直前まで人間がPowerPoint実機で数値・項目を微修正する必要があるか？
 │    └─ YES → 【手法1: PowerPoint ネイティブ図形・チャート】
 ├─ Q2. 実験データ、散布図、誤差棒、連続関数、多次元カラーマップ、相図か？
 │    └─ YES → 【手法2: Python (matplotlib / seaborn) → 高解像度PNG】
 ├─ Q3. フローチャート、因果関係、状態遷移、シーケンスなどの論理構造図か？
 │    └─ YES → 【手法5: テキストDSL (Mermaid / CeTZ / PlantUML)】
 ├─ Q4. アイコン、幾何シンボル、単機能の装置線画、分子・化学構造式か？
 │    └─ YES → 【手法3: ベクターSVG】（テキストなし/パス化済みSVG）
 └─ Q5. HTMLモック段階でのプロセス矢羽、状態マトリクス、2カラム比較か？
      └─ YES → 【手法4: HTML / CSS】（Flex/Grid/clip-path で高速プロトタイピング）
```

---

## 2. 5大作図手法の仕様とベストプラクティス

| # | 手法 | 最適な図のタイプ | PowerPointでの格納形式 | 主要なツール / ライブラリ |
|---|---|---|---|---|
| **1** | **PowerPoint ネイティブ** | 標準グラフ（棒・折れ線・円）、KPIカード、表、基本枠 | OpenXML ネイティブオブジェクト | pptxgenjs (addChart, addShape, addTable) / BLOCK_ARC |
| **2** | **Python スクリプト** | 物理実験プロット、フィッティング曲線、誤差棒、ヒートマップ | 300dpi 透過PNG | matplotlib, seaborn, assets/styles/slide_light.mplstyle |
| **3** | **ベクターSVG** | アイコン、幾何学記号、装置線画、ロゴ | パス化SVG（または高解像度PNGフォールバック） | Lucide, SimpleIcons, ベクターエディタ |
| **4** | **HTML / CSS** | プロセス矢羽（シェブロン）、ヒートマップ、2カラム対比 | モック確認後、手法1（ネイティブ図形）で実装 | build_mock.py, CSS Flexbox / Grid / clip-path |
| **5** | **テキストDSL** | 実験フローチャート、状態遷移図、シーケンス、因果ループ | 高解像度PNG / SVG | Mermaid (.mmd), Typst CeTZ (.typ), PlantUML |

---

## 3. 手法別の詳細規約と落とし穴対策

### 手法1: PowerPoint ネイティブ図形・チャート
- **適用**: 売上推移、進捗割合、単純な比較棒グラフなど、人間が後からPowerPointで修正する可能性が高いもの。
- **作法**:
  - pptxgenjs の addChart を使用し、スライドのカラーパレット（Primary/Accent）をチャート色に適用する。
  - チャート内のタイトル、軸ラベル、凡例フォントは、スライド全体の日本語フォント（Hiragino Kaku Gothic ProN 等）と完全一致させる。
  - 円グラフ・ゲージは四角形の連続配置を禁止し、ネイティブの BLOCK_ARC を使用する（Mck-ppt Rule 9）。

### 手法2: Python (matplotlib / seaborn) による科学プロット
- **適用**: 物理・自然科学の測定データ、シミュレーション結果、回帰曲線。
- **作法**:
  - **「論文図のコピペ禁止。スライド用に再描画（Re-plot）せよ」**: スライド上の配置サイズで軸フォントが最低 14〜16pt、線幅が 2〜3倍になるよう調整する。
  - **専用スタイルシートの適用**: plt.style.use("assets/styles/slide_light.mplstyle") を指定し、透過背景（transparent=True）・300dpi（dpi=300）・枠線除去（上・右のspines非表示）を自動適用する。
  - **サイズ一致の原則**: fig, ax = plt.subplots(figsize=(W, H)) の (W, H) を、スライド上に配置する実インチ数と厳密に一致させる。これによりフォントサイズ（pt）の比率がスライド本文と100%一致する。
  - **再現性**: 作図スクリプト（plot_fig1.py）を必ずスライド生成スクリプトと同じディレクトリに保存する。

### 手法3: ベクターSVG（アイコン・線画）
- **適用**: プロジェクター投影でボケさせたくない幾何シンボル、装置構成線画。
- **落とし穴対策**:
  - SVG内部に <text> タグを残さない（開いた端末のフォント環境に依存してレイアウト崩れを起こすため、テキストはすべてパス化（Convert to Path）する）。
  - PowerPoint環境によってSVG描画が不安定な場合は、300dpi以上の高解像度PNGを併用する。

### 手法4: HTML / CSS（モック・プロトタイピング）
- **適用**: build_mock.py / render_mock.py を用いた構成確認段階。
- **作法**:
  - 矢羽は clip-path: polygon(...) で描く（consulting-pptx 方式）。
  - 文字量に応じて自動でボックスが追従するため、情報量の過不足を素早く判断できる。
  - 最終PPTX化の際は、手法1（ネイティブシェイプ）として同等レイアウトを組む。

### 手法5: テキストDSL（Mermaid / Typst CeTZ）
- **適用**: 複雑なプロセス、実験プロトコル、アルゴリズムフロー。
- **作法**:
  - AI（LLM）にはマウス操作や座標計算をさせず、MarkdownテキストでMermaidコードを出力させる（座標ハルシネーションの排除）。
  - render_mock.py（Playwright/Chrome）のレンダリング機構を介してSVG/PNG化し、PPTXに配置する。
  - 物理・幾何・数式が密結合した図には、Typst + CeTZ（cetz-canvas）の活用を推奨する。
