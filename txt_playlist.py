import os
import time
import argparse
from datetime import datetime
import sys

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.errors import HttpError

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

class TxtToYouTubePlaylist:
    
    def __init__(self):
        self.search_quota_exhausted = False
        self.youtube = self.get_youtube_client()
    
    def get_youtube_client(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        
        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"
        
        scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_local_server(port=0)
        youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
        return youtube
    
    def read_txt_file(self, file_path):
        """從txt文件讀取歌曲列表，支援多種分隔符與格式"""
        print(f"正在讀取文件: {file_path}")
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return []
        tracks = []
        # 支援的分隔符
        separators = [' - ', ' – ', ' — ', '–', '—', '-']
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    # 處理格式: "數字→歌手 - 歌名" 或 "歌手 - 歌名"
                    if '→' in line:
                        line = line.split('→', 1)[1]
                    # 嘗試所有分隔符
                    sep_found = None
                    for sep in separators:
                        if sep in line:
                            sep_found = sep
                            break
                    if sep_found:
                        parts = line.split(sep_found, 1)
                        left = parts[0].strip()
                        right = parts[1].strip()
                        # 嘗試自動判斷哪邊是歌手哪邊是歌名
                        # 若其中一邊包含明顯的歌手名關鍵字（如 with, feat, ft.），則優先判斷
                        # 否則預設左為歌名、右為歌手（如 test.txt），但若右邊有多個單字或大寫，則右為歌名
                        # 這裡優先支援 rank.txt 格式（歌手 – 歌名）
                        # 若右邊有括號或英文歌名，左邊多為歌手
                        # 先嘗試 rank.txt 格式
                        if file_path.lower().endswith('rank.txt'):
                            artist_name = left
                            song_name = right
                        else:
                            # 嘗試 test.txt 格式
                            song_name = left
                            artist_name = right
                        tracks.append({
                            'name': song_name.strip(),
                            'artist': artist_name.strip(),
                            'line_num': line_num
                        })
                    else:
                        print(f"第 {line_num} 行格式不正確，跳過: {line}")
                except Exception as e:
                    print(f"解析第 {line_num} 行出錯: {line} - {e}")
                    continue
        except Exception as e:
            print(f"讀取文件出錯: {e}")
            return []
        print(f"成功讀取 {len(tracks)} 首歌曲")
        return tracks
    
    def search_youtube_video(self, track, num):
        """在YouTube搜索對應的影片"""
        print(f"{num}. 搜索: {track['name']} - {track['artist']}")
        query = "{} {}".format(track['name'], track['artist'])

        if self.search_quota_exhausted:
            return self.search_with_yt_dlp(query)
        
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=1
            )
            response = request.execute()
            
            if response['items']:
                item = response['items'][0]
                video_title = item['snippet']['title']
                video_id = item['id']['videoId']
                print(f"   找到: {video_title} (ID: {video_id})")
                return video_id
            else:
                print(f"   未找到對應影片: {query}")
                return None
                
        except HttpError as err:
            print(f"   搜索出錯: {err}")
            error_text = str(err).lower()
            quota_error = (
                err.resp.status in [403, 429]
                and ("quota" in error_text or "ratelimit" in error_text)
            )
            if quota_error:
                self.search_quota_exhausted = True
                print("   YouTube Search API 配額已用完，改用 yt-dlp 搜尋後續歌曲。")
                return self.search_with_yt_dlp(query)
            if err.resp.status in [403, 500, 503]:
                time.sleep(5)
            return None

    def search_with_yt_dlp(self, query):
        """不使用 YouTube Data API Search quota 搜尋第一個影片。"""
        if yt_dlp is None:
            print("   搜尋配額已用完，且未安裝 yt-dlp。請先執行: pip install yt-dlp")
            return None
        try:
            options = {"quiet": True, "no_warnings": True, "skip_download": True,
                       "extract_flat": True}
            with yt_dlp.YoutubeDL(options) as ydl:
                result = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = result.get("entries", []) if result else []
            if entries and entries[0].get("id"):
                video = entries[0]
                print(f"   yt-dlp 找到: {video.get('title', query)} (ID: {video['id']})")
                return video["id"]
            print(f"   yt-dlp 找不到影片: {query}")
        except Exception as error:
            print(f"   yt-dlp 搜尋出錯: {error}")
        return None
    
    def create_youtube_playlist(self, title, description=""):
        """創建YouTube播放清單"""
        try:
            request = self.youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description
                    },
                    "status": {
                        "privacyStatus": "public"
                    }
                }
            )
            response = request.execute()
            
            playlist_id = response['id']
            playlist_title = response['snippet']['title']
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            
            print('=' * 50)
            print(f"播放清單創建成功!")
            print(f"名稱: {playlist_title}")
            print(f"網址: {playlist_url}")
            print('=' * 50)
            
            return playlist_id
            
        except HttpError as err:
            print(f"創建播放清單出錯: {err}")
            if err.resp.status in [403, 500, 503]:
                time.sleep(5)
            return None
    
    def add_video_to_playlist(self, video_id, playlist_id):
        """將影片添加到播放清單"""
        try:
            request = self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    'snippet': {
                        'playlistId': playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video_id
                        }
                    }
                }
            )
            request.execute()
            return True
            
        except HttpError as err:
            print(f"   添加影片出錯: {err}")
            if err.resp.status in [409]:  # 影片已存在
                print("   影片已存在於播放清單中")
                return True
            elif err.resp.status in [500, 503]:
                time.sleep(5)
                return False
            return False
    
    def create_playlist_from_txt(self, txt_file_path, playlist_name=None, limit=None):
        """從txt文件創建YouTube播放清單的主要方法"""
        # 讀取txt文件
        tracks = self.read_txt_file(txt_file_path)
        if not tracks:
            return
        
        # 限制歌曲數量
        if limit and limit < len(tracks):
            tracks = tracks[:limit]
            print(f"限制歌曲數量為前 {limit} 首")
        
        # 設置播放清單名稱和描述
        if playlist_name is None:
            file_name = os.path.basename(txt_file_path).replace('.txt', '')
            current_date = datetime.now().strftime("%Y-%m-%d")
            playlist_name = f"{file_name} - {current_date}"
        
        description = f"從 {txt_file_path} 創建的播放清單 - 創建於 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 創建播放清單
        playlist_id = self.create_youtube_playlist(playlist_name, description)
        if not playlist_id:
            print("播放清單創建失敗")
            return
        
        # 搜索並添加每首歌曲
        success_count = 0
        total_count = len(tracks)
        
        print(f"\n開始處理 {total_count} 首歌曲...")
        
        for num, track in enumerate(tracks, 1):
            print(f"\n進度: {num}/{total_count}")
            
            # 搜索YouTube影片
            video_id = self.search_youtube_video(track, num)
            
            if video_id:
                # 添加到播放清單
                if self.add_video_to_playlist(video_id, playlist_id):
                    success_count += 1
                    print(f"   ✓ 成功添加到播放清單")
                else:
                    print(f"   ✗ 添加到播放清單失敗")
            else:
                print(f"   ✗ 未找到對應影片")
            
            # 避免API請求過於頻繁
            time.sleep(1)
        
        print(f"\n" + "=" * 50)
        print(f"播放清單創建完成!")
        print(f"成功添加: {success_count}/{total_count} 首歌曲")
        print(f"播放清單網址: https://www.youtube.com/playlist?list={playlist_id}")
        print("=" * 50)

def main():
    parser = argparse.ArgumentParser(description='從txt文件創建YouTube播放清單')
    parser.add_argument(
        'txt_file', 
        nargs='?',
        default='rank.txt',
        help='txt文件路徑 (預設: rank.txt)'
    )
    parser.add_argument(
        '--name', '-n', 
        type=str, 
        help='自訂播放清單名稱 (如未提供則使用檔名+日期)'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        help='限制歌曲數量'
    )
    
    args = parser.parse_args()
    
    try:
        converter = TxtToYouTubePlaylist()
        converter.create_playlist_from_txt(
            txt_file_path=args.txt_file,
            playlist_name=args.name,
            limit=args.limit
        )
        
    except KeyboardInterrupt:
        print("\n程序被用戶中斷")
    except Exception as e:
        print(f"程序執行出錯: {e}")

if __name__ == '__main__':
    main()
