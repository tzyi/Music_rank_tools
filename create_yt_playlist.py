import os
import time
import argparse
from datetime import datetime
import sys
sys.path.append('.')
from melon_scraper import scrape_melon_chart

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.errors import HttpError

class MelonToYouTubePlaylist:
    
    def __init__(self):
        self.youtube = self.get_youtube_client()
        self.tracks = []
    
    def get_youtube_client(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        
        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = os.path.join("create_yt_playlist", "client_secret.json")
        
        scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_local_server(port=0)
        youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
        return youtube
    
    def get_melon_tracks(self):
        """從Melon排行榜獲取歌曲列表"""
        print("正在獲取 Melon 排行榜...")
        songs = scrape_melon_chart()
        
        if not songs:
            print("無法獲取 Melon 排行榜數據")
            return []
        
        tracks = []
        for song_str in songs:
            try:
                # 解析歌曲字符串格式: "歌名 - 歌手"
                if " - " in song_str:
                    song_name, artist_name = song_str.split(" - ", 1)
                    tracks.append({
                        'name': song_name.strip(),
                        'artist': artist_name.strip()
                    })
            except Exception as e:
                print(f"解析歌曲信息出錯: {song_str} - {e}")
                continue
        
        print(f"成功獲取 {len(tracks)} 首歌曲")
        return tracks
    
    def search_youtube_video(self, track, num):
        """在YouTube搜索對應的影片"""
        print(f"{num}. 搜索: {track['name']} - {track['artist']}")
        query = "{} {}".format(track['name'], track['artist'])
        
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
            if err.resp.status in [403, 500, 503]:
                time.sleep(5)
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
    
    def create_playlist_from_melon(self, playlist_name=None):
        """從Melon排行榜創建YouTube播放清單的主要方法"""
        # 獲取Melon排行榜
        tracks = self.get_melon_tracks()
        if not tracks:
            return
        
        # 設置播放清單名稱和描述
        if playlist_name is None:
            current_date = datetime.now().strftime("%Y-%m-%d")
            playlist_name = f"Melon Chart Top 100 - {current_date}"
        
        description = f"Melon排行榜音樂播放清單 - 創建於 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
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
    parser = argparse.ArgumentParser(description='從Melon排行榜創建YouTube播放清單')
    parser.add_argument(
        '--name', '-n', 
        type=str, 
        help='自訂播放清單名稱 (如未提供則使用預設名稱)'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=100,
        help='限制歌曲數量 (預設: 100)'
    )
    
    args = parser.parse_args()
    
    try:
        converter = MelonToYouTubePlaylist()
        converter.create_playlist_from_melon(playlist_name=args.name)
        
    except KeyboardInterrupt:
        print("\n程序被用戶中斷")
    except Exception as e:
        print(f"程序執行出錯: {e}")

if __name__ == '__main__':
    main()