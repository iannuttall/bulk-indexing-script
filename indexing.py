import os
import sys
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import BatchHttpRequest
import httplib2
from sqlalchemy import create_engine, Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime, timedelta

Base = declarative_base()

class URL(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    last_submitted = Column(DateTime, nullable=True)
    index_checked_date = Column(DateTime, nullable=True)
    is_indexed = Column(Boolean, default=False)
    
class Quota(Base):
    __tablename__ = 'quota'

    id = Column(Integer, primary_key=True)
    date = Column(String, nullable=False)
    count = Column(Integer, nullable=False)

class Log(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    log_type = Column(String, nullable=False)
    message = Column(String, nullable=False)

class BulkIndexer:
    def __init__(self):
        """
        Initialize the BulkIndexer class.
        """
        self.engine = create_engine('sqlite:///database.db')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        scopes = ['https://www.googleapis.com/auth/indexing']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scopes=scopes)
        http = credentials.authorize(httplib2.Http())
        self.service = build('indexing', 'v3', http=http)
        self.urls = self.load_urls()
        self.quota = self.get_quota()

    def index(self):
        """
        Index all URLs in the database, up to the daily quota limit.
        """
        batch = self.service.new_batch_http_request(callback=self.insert_event)
        for url in self.urls:
            if self.quota >= 200:
                print('Quota exceeded. Please try again tomorrow.')
                return
            batch.add(self.service.urlNotifications().publish(body={"url": url.url, "type": "URL_UPDATED"}))
        batch.execute()

    def load_urls(self, limit=200):
        """
        Load URLs from the database.
        """
        session = self.Session()
        urls = session.query(URL).limit(limit).all()
        session.close()
        return urls
    
    def load_unindexed_urls(self):
        """
        Load URLs from the database that have not been indexed.
        """
        session = self.Session()
        urls = session.query(URL).filter(URL.is_indexed == False).filter(URL.index_checked_date == None or URL.index_checked_date < datetime.now() - timedelta(days=7)).all()
        session.close()
        return urls

    def insert_event(self, request_id, response, exception):
        """
        Callback function for the batch request.
        """
        if exception is not None:
            self.log(str(exception), 'error')
        else:
            url = response['urlNotificationMetadata']['url']
            self.log(url, 'submitted')
            self.update_url(url, datetime.now())
            print(f'Requested indexing of {url}')
        self.update_quota()

    def remove_url(self, url):
        """
        Remove a URL from the database.
        """
        session = self.Session()
        try:
            session.query(URL).filter_by(url=url).delete()
            session.commit()
        finally:
            session.close()

    def update_url(self, url, last_submitted):
        """
        Update the last_submitted field for a given URL.
        """
        session = self.Session()
        try:
            session.query(URL).filter_by(url=url).update({'last_submitted': last_submitted})
            session.commit()
        finally:
            session.close()

    def add_urls(self, new_urls):
        """
        Add new URLs to the database.
        """
        session = self.Session()
        try:
            for url in new_urls:
                exists = session.query(URL).filter_by(url=url).first()
                if not exists:
                    session.add(URL(url=url))
            session.commit()
        finally:
            session.close()

    def load_urls_from_file(self, file_path='urls.txt'):
        """
        Load URLs from a file, add them to the database, and then clear the file.
        """
        with open(file_path, 'r') as f:
            urls = f.read().splitlines()

        self.add_urls(urls)

        with open(file_path, 'w') as f:
            f.write('')

    def get_quota(self):
        """
        Get the number of URLs submitted today.
        """
        today = datetime.now().strftime('%Y-%m-%d')
        session = self.Session()
        quota = session.query(Quota).filter_by(date=today).first()

        if quota is None:
            session.add(Quota(date=today, count=0))
            session.commit()
            return 0
        else:
            return quota.count

    def update_quota(self):
        """
        Increment the number of URLs submitted today.
        """
        today = datetime.now().strftime('%Y-%m-%d')
        session = self.Session()
        try:
            quota = session.query(Quota).filter_by(date=today).first()
            if quota:
                quota.count += 1
            else:
                session.add(Quota(date=today, count=1))
            session.commit()
        finally:
            session.close()

    def log(self, message, log_type):
        """
        Log a message to the database.
        """
        session = self.Session()
        try:
            new_log = Log(log_type=log_type, message=message)
            session.add(new_log)
            session.commit()
        except Exception as e:
            print(f"Failed to log message. Error: {e}")
        finally:
            session.close()

    def check_indexing(self):
        """
        Check URLs to see if they are indexed.

        @todo: implement a method to check the indexed status of the URLs.
        
        Options:
        1. use the DataForSEO API and perform site: and inurl: searches
        2. Build a custom scraper to check the indexed status of the URLs using scraperapi.com
        """
        pass

if __name__ == '__main__':
    indexer = BulkIndexer()
    
    if len(sys.argv) < 2:
        print("Usage: indexing.py <command> [<args>]")
        print("Commands:")
        print("   index     Run the indexing process")
        print("   load      Load URLs from a given file to the DB")
        sys.exit(1)

    command = sys.argv[1]

    if command == "index":
        indexer.index()
    elif command == "load":
        if len(sys.argv) < 3:
            print("Please provide a file name to load URLs from.")
            sys.exit(1)
        file_path = sys.argv[2]
        indexer.load_urls_from_file(file_path)
        print(f"URLs loaded from {file_path} into the database.")
    else:
        print(f"Unknown command: {command}")
