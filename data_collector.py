import json
import sqlite3
import os
import platform
from datetime import datetime, timedelta
import pandas as pd
import glob
import shutil

# psutil import with fallback
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

def is_aws_environment():
    """AWS 환경인지 확인"""
    # AWS Elastic Beanstalk 환경 변수 확인
    aws_indicators = [
        os.environ.get('AWS_REGION'),
        os.environ.get('AWS_EXECUTION_ENV'),
        os.environ.get('EB_NODE_COMMAND'),
        '/opt/elasticbeanstalk' in os.environ.get('PATH', ''),
        os.path.exists('/opt/elasticbeanstalk')
    ]
    return any(aws_indicators)

class ChromeBookmarkCollector:
    def __init__(self):
        self.chrome_paths = self._get_chrome_paths()
    
    def _get_chrome_paths(self):
        """운영체제별 Chrome 데이터 경로 반환"""
        system = platform.system()
        if system == "Windows":
            base_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
        elif system == "Darwin":  # macOS
            base_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        else:  # Linux
            base_path = os.path.expanduser("~/.config/google-chrome")
        
        return {
            'bookmarks': os.path.join(base_path, "Default", "Bookmarks"),
            'history': os.path.join(base_path, "Default", "History")
        }
    
    def extract_bookmarks(self, start_date=None, end_date=None, include_folders=True):
        """Chrome 북마크 추출 (AWS 환경에서는 샘플 데이터 반환)"""
        # AWS 환경에서는 Chrome이 설치되어 있지 않으므로 샘플 데이터 반환
        if not os.path.exists(os.path.expanduser("~")):
            return self._get_sample_bookmarks()
            
        bookmarks_file = self.chrome_paths['bookmarks']
        
        if not os.path.exists(bookmarks_file):
            # Chrome 북마크 파일이 없으면 샘플 데이터 반환
            return self._get_sample_bookmarks()
        
        with open(bookmarks_file, 'r', encoding='utf-8') as f:
            bookmarks_data = json.load(f)
        
        bookmarks = []
        
        def extract_from_folder(folder, folder_path=""):
            for item in folder.get('children', []):
                if item['type'] == 'folder':
                    if include_folders:
                        new_path = f"{folder_path}/{item['name']}" if folder_path else item['name']
                        extract_from_folder(item, new_path)
                else:
                    # URL 북마크
                    date_added = datetime.fromtimestamp(int(item['date_added']) / 1000000 - 11644473600)
                    
                    # 날짜 필터링
                    if start_date and date_added < datetime.strptime(start_date, '%Y-%m-%d'):
                        continue
                    if end_date and date_added > datetime.strptime(end_date, '%Y-%m-%d'):
                        continue
                    
                    bookmarks.append({
                        'title': item['name'],  # application.py에서 'title' 필드 사용
                        'url': item['url'],
                        'folder': folder_path,
                        'date_added': date_added.isoformat()
                    })
        
        # 북마크 바와 기타 북마크에서 추출
        roots = bookmarks_data.get('roots', {})
        for root_name, root_data in roots.items():
            if root_name in ['bookmark_bar', 'other']:
                extract_from_folder(root_data, root_name)
        
        return bookmarks
    
    def _get_sample_bookmarks(self):
        """샘플 북마크 데이터 반환 (2025년 상반기 데이터)"""
        base_date = datetime(2025, 1, 1)
        return [
            # 1월 북마크
            {'title': 'ChatGPT', 'url': 'https://chat.openai.com', 'folder': 'AI Tools', 'date_added': (base_date + timedelta(days=5)).isoformat()},
            {'title': 'Claude AI', 'url': 'https://claude.ai', 'folder': 'AI Tools', 'date_added': (base_date + timedelta(days=10)).isoformat()},
            {'title': 'GitHub Copilot', 'url': 'https://github.com/features/copilot', 'folder': 'Development', 'date_added': (base_date + timedelta(days=15)).isoformat()},
            
            # 2월 북마크
            {'title': 'AWS Console', 'url': 'https://aws.amazon.com/console', 'folder': 'Cloud', 'date_added': (base_date + timedelta(days=35)).isoformat()},
            {'title': 'Vercel Dashboard', 'url': 'https://vercel.com/dashboard', 'folder': 'Cloud', 'date_added': (base_date + timedelta(days=42)).isoformat()},
            {'title': 'Python.org', 'url': 'https://python.org', 'folder': 'Development', 'date_added': (base_date + timedelta(days=48)).isoformat()},
            
            # 3월 북마크
            {'title': 'React Docs', 'url': 'https://react.dev', 'folder': 'Development', 'date_added': (base_date + timedelta(days=65)).isoformat()},
            {'title': 'Tailwind CSS', 'url': 'https://tailwindcss.com', 'folder': 'Development', 'date_added': (base_date + timedelta(days=72)).isoformat()},
            {'title': 'MDN Web Docs', 'url': 'https://developer.mozilla.org', 'folder': 'Development', 'date_added': (base_date + timedelta(days=78)).isoformat()},
            
            # 4월 북마크
            {'title': 'Stack Overflow', 'url': 'https://stackoverflow.com', 'folder': 'Development', 'date_added': (base_date + timedelta(days=95)).isoformat()},
            {'title': 'Coursera', 'url': 'https://coursera.org', 'folder': 'Education', 'date_added': (base_date + timedelta(days=102)).isoformat()},
            {'title': 'Udemy', 'url': 'https://udemy.com', 'folder': 'Education', 'date_added': (base_date + timedelta(days=108)).isoformat()},
            
            # 5월 북마크
            {'title': 'YouTube', 'url': 'https://youtube.com', 'folder': 'Entertainment', 'date_added': (base_date + timedelta(days=125)).isoformat()},
            {'title': 'Netflix', 'url': 'https://netflix.com', 'folder': 'Entertainment', 'date_added': (base_date + timedelta(days=132)).isoformat()},
            {'title': 'Amazon', 'url': 'https://amazon.com', 'folder': 'Shopping', 'date_added': (base_date + timedelta(days=138)).isoformat()}
        ]

class BrowserHistoryCollector:
    def __init__(self):
        self.chrome_paths = ChromeBookmarkCollector()._get_chrome_paths()
    
    def get_browser_history(self, days_back=30):
        """브라우저 히스토리 수집 (AWS 환경에서는 샘플 데이터 반환)"""
        history_file = self.chrome_paths['history']
        
        if not os.path.exists(history_file):
            # Chrome 히스토리 파일이 없으면 샘플 데이터 반환
            return self._get_sample_history()
        
        # 히스토리 파일 복사 (Chrome이 사용 중일 수 있음)
        temp_history = "temp_history.db"
        try:
            shutil.copy2(history_file, temp_history)
        except:
            return self._get_sample_history()
        
        try:
            conn = sqlite3.connect(temp_history)
            cursor = conn.cursor()
            
            # 지정된 일수만큼의 히스토리 가져오기
            cutoff_date = datetime.now() - timedelta(days=days_back)
            cutoff_timestamp = int(cutoff_date.timestamp() * 1000000) + 11644473600000000
            
            query = """
            SELECT url, title, visit_count, last_visit_time
            FROM urls 
            WHERE last_visit_time > ?
            ORDER BY last_visit_time DESC
            """
            
            cursor.execute(query, (cutoff_timestamp,))
            results = cursor.fetchall()
            
            history = []
            for row in results:
                url, title, visit_count, last_visit_time = row
                # Chrome 타임스탬프를 Python datetime으로 변환
                visit_date = datetime.fromtimestamp((last_visit_time - 11644473600000000) / 1000000)
                
                history.append({
                    'url': url,
                    'title': title or 'No Title',
                    'visit_count': visit_count,
                    'last_visit': visit_date.isoformat(),
                    'domain': url.split('/')[2] if len(url.split('/')) > 2 else url
                })
            
            conn.close()
            return history
            
        except:
            return self._get_sample_history()
        finally:
            if os.path.exists(temp_history):
                try:
                    os.remove(temp_history)
                except:
                    pass
    
    def _get_sample_history(self):
        """샘플 히스토리 데이터 반환 (2025년 상반기 데이터)"""
        now = datetime.now()
        return [
            # 최근 방문 (오늘)
            {'url': 'https://chat.openai.com', 'title': 'ChatGPT', 'visit_count': 45, 'last_visit': (now - timedelta(minutes=30)).isoformat(), 'domain': 'chat.openai.com'},
            {'url': 'https://github.com/trending', 'title': 'Trending repositories on GitHub', 'visit_count': 32, 'last_visit': (now - timedelta(hours=1)).isoformat(), 'domain': 'github.com'},
            {'url': 'https://stackoverflow.com/questions/tagged/python', 'title': 'Python Questions - Stack Overflow', 'visit_count': 28, 'last_visit': (now - timedelta(hours=2)).isoformat(), 'domain': 'stackoverflow.com'},
            
            # 어제
            {'url': 'https://aws.amazon.com/console', 'title': 'AWS Management Console', 'visit_count': 18, 'last_visit': (now - timedelta(days=1)).isoformat(), 'domain': 'aws.amazon.com'},
            {'url': 'https://claude.ai', 'title': 'Claude AI Assistant', 'visit_count': 22, 'last_visit': (now - timedelta(days=1, hours=3)).isoformat(), 'domain': 'claude.ai'},
            {'url': 'https://react.dev', 'title': 'React - The library for web and native user interfaces', 'visit_count': 15, 'last_visit': (now - timedelta(days=1, hours=6)).isoformat(), 'domain': 'react.dev'},
            
            # 지난주
            {'url': 'https://python.org/downloads', 'title': 'Python Downloads', 'visit_count': 12, 'last_visit': (now - timedelta(days=3)).isoformat(), 'domain': 'python.org'},
            {'url': 'https://tailwindcss.com/docs', 'title': 'Tailwind CSS Documentation', 'visit_count': 19, 'last_visit': (now - timedelta(days=4)).isoformat(), 'domain': 'tailwindcss.com'},
            {'url': 'https://vercel.com/dashboard', 'title': 'Vercel Dashboard', 'visit_count': 8, 'last_visit': (now - timedelta(days=5)).isoformat(), 'domain': 'vercel.com'},
            
            # 이번 달
            {'url': 'https://youtube.com/watch?v=dQw4w9WgXcQ', 'title': 'Programming Tutorial - YouTube', 'visit_count': 25, 'last_visit': (now - timedelta(days=7)).isoformat(), 'domain': 'youtube.com'},
            {'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript', 'title': 'JavaScript | MDN', 'visit_count': 16, 'last_visit': (now - timedelta(days=10)).isoformat(), 'domain': 'developer.mozilla.org'},
            {'url': 'https://coursera.org/browse/computer-science', 'title': 'Computer Science Courses - Coursera', 'visit_count': 11, 'last_visit': (now - timedelta(days=12)).isoformat(), 'domain': 'coursera.org'},
            
            # 지난달
            {'url': 'https://udemy.com/topic/python', 'title': 'Python Courses - Udemy', 'visit_count': 9, 'last_visit': (now - timedelta(days=20)).isoformat(), 'domain': 'udemy.com'},
            {'url': 'https://netflix.com/browse', 'title': 'Netflix Korea - Watch TV Shows Online', 'visit_count': 35, 'last_visit': (now - timedelta(days=25)).isoformat(), 'domain': 'netflix.com'},
            {'url': 'https://amazon.com/dp/B08XXBP1L9', 'title': 'Programming Books - Amazon', 'visit_count': 6, 'last_visit': (now - timedelta(days=30)).isoformat(), 'domain': 'amazon.com'},
            
            # 더 오래된 방문
            {'url': 'https://linkedin.com/in/profile', 'title': 'LinkedIn Profile', 'visit_count': 14, 'last_visit': (now - timedelta(days=45)).isoformat(), 'domain': 'linkedin.com'},
            {'url': 'https://medium.com/@developer/ai-trends-2025', 'title': 'AI Trends 2025 - Medium', 'visit_count': 7, 'last_visit': (now - timedelta(days=60)).isoformat(), 'domain': 'medium.com'},
            {'url': 'https://reddit.com/r/programming', 'title': 'r/programming - Reddit', 'visit_count': 29, 'last_visit': (now - timedelta(days=75)).isoformat(), 'domain': 'reddit.com'}
        ]

class SystemInfoCollector:
    def get_system_info(self):
        """시스템 정보 수집 (환경에 따라 실제 데이터 또는 샘플 데이터)"""
        if PSUTIL_AVAILABLE and not is_aws_environment():
            # 로컬 환경: 실제 시스템 정보 수집
            try:
                return self._get_real_system_info()
            except Exception as e:
                print(f"실제 시스템 정보 수집 실패, 샘플 데이터 사용: {e}")
                return self._get_sample_system_info()
        else:
            # AWS 환경 또는 psutil 없음: 샘플 데이터 사용
            return self._get_sample_system_info()
    
    def _get_real_system_info(self):
        """실제 시스템 정보 수집"""
        system_info = []
        
        # 기본 시스템 정보
        system_info.extend([
            {
                'category': 'OS',
                'name': 'Operating System',
                'value': f"{platform.system()} {platform.release()}",
                'details': platform.platform()
            },
            {
                'category': 'Python',
                'name': 'Python Version',
                'value': platform.python_version(),
                'details': platform.python_implementation()
            }
        ])
        
        # CPU 정보
        try:
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            system_info.extend([
                {
                    'category': 'CPU',
                    'name': 'CPU Cores',
                    'value': str(cpu_count),
                    'details': f'Physical: {psutil.cpu_count(logical=False)}, Logical: {cpu_count}'
                },
                {
                    'category': 'CPU',
                    'name': 'CPU Usage',
                    'value': f'{cpu_percent}%',
                    'details': 'Current utilization'
                }
            ])
        except:
            pass
        
        # 메모리 정보
        try:
            memory = psutil.virtual_memory()
            system_info.extend([
                {
                    'category': 'Memory',
                    'name': 'Total RAM',
                    'value': f'{memory.total // (1024**3)} GB',
                    'details': f'{memory.total // (1024**2)} MB'
                },
                {
                    'category': 'Memory',
                    'name': 'Used RAM',
                    'value': f'{memory.used // (1024**3)} GB ({memory.percent}%)',
                    'details': f'{memory.used // (1024**2)} MB used'
                },
                {
                    'category': 'Memory',
                    'name': 'Available RAM',
                    'value': f'{memory.available // (1024**3)} GB',
                    'details': f'{memory.available // (1024**2)} MB available'
                }
            ])
        except:
            pass
        
        # 디스크 정보
        try:
            # Windows에서는 C:\ 사용, Linux/Mac에서는 / 사용
            disk_path = 'C:\\' if platform.system() == 'Windows' else '/'
            disk = psutil.disk_usage(disk_path)
            system_info.extend([
                {
                    'category': 'Storage',
                    'name': 'Total Disk',
                    'value': f'{disk.total // (1024**3)} GB',
                    'details': f'{disk.total // (1024**2)} MB'
                },
                {
                    'category': 'Storage',
                    'name': 'Used Disk',
                    'value': f'{disk.used // (1024**3)} GB ({disk.percent}%)',
                    'details': f'{disk.used // (1024**2)} MB used'
                },
                {
                    'category': 'Storage',
                    'name': 'Free Disk',
                    'value': f'{disk.free // (1024**3)} GB',
                    'details': f'{disk.free // (1024**2)} MB free'
                }
            ])
        except:
            pass
        
        # 실행 중인 프로세스 (상위 10개)
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] is not None and proc_info['cpu_percent'] > 0:
                        processes.append({
                            'category': 'Process',
                            'name': proc_info['name'],
                            'value': f"PID: {proc_info['pid']}",
                            'details': f"CPU: {proc_info['cpu_percent']:.1f}%, Memory: {proc_info['memory_percent']:.1f}%"
                        })
                except:
                    continue
            
            # CPU 사용량 기준으로 정렬하여 상위 10개만
            processes.sort(key=lambda x: float(x['details'].split('CPU: ')[1].split('%')[0]), reverse=True)
            system_info.extend(processes[:10])
        except:
            pass
        
        return system_info
    
    def _get_sample_system_info(self):
        """샘플 시스템 정보 반환 (AWS 환경용)"""
        return [
            {
                'type': 'running_process',
                'name': 'chrome.exe',
                'pid': 1234,
                'cpu_percent': 15.5,
                'memory_percent': 8.2,
                'create_time': datetime.now().isoformat(),
                'category': 'browser'
            },
            {
                'type': 'running_process',
                'name': 'code.exe',
                'pid': 5678,
                'cpu_percent': 5.3,
                'memory_percent': 12.1,
                'create_time': (datetime.now() - timedelta(hours=3)).isoformat(),
                'category': 'development'
            },
            {
                'type': 'installed_program',
                'name': 'Visual Studio Code',
                'version': '1.85.0',
                'install_date': '2024-01-15',
                'category': 'development'
            },
            {
                'type': 'installed_program',
                'name': 'Google Chrome',
                'version': '120.0.6099.109',
                'install_date': '2024-01-10',
                'category': 'browser'
            }
        ]
    
    def _categorize_program(self, program_name):
        """프로그램을 카테고리별로 분류"""
        program_name_lower = program_name.lower()
        
        categories = {
            'development': ['visual studio', 'code', 'python', 'java', 'git', 'node', 'npm', 'docker', 'intellij', 'eclipse', 'sublime', 'atom'],
            'design': ['photoshop', 'illustrator', 'figma', 'sketch', 'canva', 'gimp', 'blender'],
            'office': ['word', 'excel', 'powerpoint', 'outlook', 'teams', 'slack', 'notion', 'trello'],
            'browser': ['chrome', 'firefox', 'safari', 'edge', 'opera'],
            'media': ['spotify', 'youtube', 'vlc', 'media player', 'itunes', 'netflix'],
            'communication': ['discord', 'telegram', 'whatsapp', 'zoom', 'skype', 'kakao'],
            'gaming': ['steam', 'game', 'epic', 'origin', 'battle.net'],
            'utility': ['winrar', 'zip', 'antivirus', 'cleaner', 'driver']
        }
        
        for category, keywords in categories.items():
            if any(keyword in program_name_lower for keyword in keywords):
                return category
        
        return 'other' 