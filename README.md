# Music Rank Tools

這個工具可以爬取 Melon 排行榜並自動在 YouTube 創建播放清單。

## 功能

1. **melon_scraper.py** - 爬取 Melon 排行榜
2. **create_yt_playlist.py** - 從 Melon 排行榜創建 YouTube 播放清單
3. **txt_playlist.py** - 使用 rank.txt 文件創建 YouTube 播放清單



## 安裝

1. 安裝所需依賴項：
```bash
pip install -r requirements.txt
```

2. 設置 YouTube API：
   - 前往 [Google Cloud Console](https://console.cloud.google.com/)
   - 創建新項目或選擇現有項目
   - 啟用 YouTube Data API v3
   - 創建 OAuth 2.0 客戶端 ID 憑證
   - 下載憑證文件並重命名為 `client_secret.json`
   - 將 `client_secret.json` 放在目錄中

## 使用方法

### 1. 只爬取 Melon 排行榜

```bash
python melon_scraper.py
```

### 2. 從 Melon 排行榜創建 YouTube 播放清單

#### 使用預設播放清單名稱：
```bash
python create_yt_playlist.py
```
預設名稱格式：`Melon Chart Top 100 - YYYY-MM-DD`

#### 使用自訂播放清單名稱：
```bash
python create_yt_playlist.py --name "我的韓流音樂清單"
```
或使用縮寫：
```bash
python create_yt_playlist.py -n "我的韓流音樂清單"
```

#### 查看所有可用選項：
```bash
python create_yt_playlist.py --help
```

### 3. rank.txt導入播放清單

#### 使用預設的 rank.txt 文件
```bash
  python txt_playlist.py
```

#### 指定其他txt文件
```bash
python txt_playlist.py songs.txt
```


#### 自訂播放清單名稱
```bash
python txt_playlist.py --name "我的音樂清單"
python txt_playlist.py -n "我的音樂清單"
```

#### 限制歌曲數量 (只取前50首)
```bash
python txt_playlist.py --limit 50
python txt_playlist.py -l 50
```

#### 組合使用
```bash
python txt_playlist.py rank.txt --name "Melon Top 100" --limit 50
```

Features:

1. 自動格式解析: 支援你的 rank.txt 格式 (數字→歌手 - 歌名)
2. 命令行參數: 可自訂播放清單名稱和歌曲數量限制
3. 錯誤處理: 包含完整的錯誤處理和進度顯示
4. API限制處理: 自動處理YouTube API限制和重試機制


## 注意事項

1. 首次運行時，程序會打開瀏覽器進行 Google 帳戶授權
2. 程序會自動處理 API 請求限制，添加適當的延遲
3. 如果某些歌曲在 YouTube 上找不到對應影片，程序會跳過並繼續處理下一首
4. 創建的播放清單默認為公開狀態

## 故障排除

如果遇到 API 配額限制，請稍後再試或申請增加 YouTube API 配額。

## 依賴項

- beautifulsoup4: 用於網頁爬取
- requests: 用於 HTTP 請求
- google-auth-oauthlib: Google OAuth 認證
- google-api-python-client: YouTube API 客戶端