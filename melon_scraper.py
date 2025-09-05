import requests
from bs4 import BeautifulSoup
import time
import sys
import codecs
import pprint

def scrape_melon_chart():
    url = "https://www.melon.com/chart/index.htm"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        songs = []
        
        # Try different selectors for song titles and artists
        chart_rows = soup.find_all('tr')
        
        for row in chart_rows:
            song_elem = row.find('div', class_='ellipsis rank01')
            artist_elem = row.find('div', class_='ellipsis rank02')
            
            if song_elem and artist_elem:
                song_link = song_elem.find('a')
                
                if song_link:
                    song_title = song_link.get_text().strip()
                    
                    # Get all artist links from the artist element
                    artist_links = artist_elem.find_all('a')
                    if artist_links:
                        # Extract all artist names and remove duplicates while preserving order
                        artists = []
                        seen = set()
                        for a in artist_links:
                            artist_name = a.get_text().strip()
                            if artist_name and artist_name not in seen:
                                artists.append(artist_name)
                                seen.add(artist_name)
                        artist_str = '/'.join(artists) if len(artists) > 1 else artists[0] if artists else ""
                    else:
                        # Fallback to getting text from span elements
                        artist_spans = artist_elem.find_all('span')
                        if artist_spans:
                            artists = []
                            seen = set()
                            for span in artist_spans:
                                span_text = span.get_text().strip()
                                if span_text and span_text not in ['|', ',', '&', ''] and span_text not in seen:
                                    artists.append(span_text)
                                    seen.add(span_text)
                            artist_str = '/'.join(artists) if artists else artist_elem.get_text().strip()
                        else:
                            artist_str = artist_elem.get_text().strip()
                    
                    if song_title and artist_str:
                        songs.append(f"{song_title} - {artist_str}")
        
        return songs
        
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
    except Exception as e:
        print(f"Error parsing data: {e}")
        return []


def main():
    charts = []
    
    # Set UTF-8 encoding for output
    if sys.platform.startswith('win'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    
    print("正在爬取 Melon 排行榜...")
    songs = scrape_melon_chart()
    
    if songs:
        for song in songs:
            try:
                print(song)
                charts.append(song)
                
            except UnicodeEncodeError:
                print(song.encode('utf-8', errors='ignore').decode('utf-8'))
            time.sleep(0.1)  # 避免過快輸出

    else:
        print("無法獲取排行榜數據")
    # print(charts)

if __name__ == "__main__":
    main()