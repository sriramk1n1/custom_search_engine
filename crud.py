from models import User, Page, SessionLocal, Backwardhash
from werkzeug.security import check_password_hash
import re

def get_base_url(url):
    url += "/"
    match = re.findall(r"https?://([^/]+)/", url)
    return match[0] if match else ""

def is_page_crawled(url):
    session = SessionLocal()
    pages = session.query(Page).all()
    if pages==None:
        return False
    for page in pages:
            print(get_base_url(page.url))
            if get_base_url(page.url)==url:
                session.close()
                return True
    session.close()
    return False
    

def add_user(email, password):
    session = SessionLocal()
    try:
        user = User(email=email, password=password)
        session.add(user)
        session.commit()
    finally:
        session.close()

def add_page(email, id, url, status):
    session = SessionLocal()
    try:
        page = Page(url=url, status=status, email=email, pageid=id)
        session.add(page)
        session.commit()
    finally:
        session.close()

def update_status(id, status):
    session = SessionLocal()
    try:
        pages = session.query(Page).filter_by(pageid=id).all()
        if not pages:
            return
        for page in pages:
            page.status=status
        session.commit()
    finally:
        session.close()

def get_all_pages_for_user(email):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        return user.pages if user else None
    finally:
        session.close()

def is_valid_user(email,password):
    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session.close()
        return True
    else:
        session.close()
        return False
    
def delete_page(pageid, email):
    session = SessionLocal()
    try:
        page = session.query(Page).filter_by(pageid=pageid, email=email).first()
        if page:
            session.delete(page)
            session.commit()
            return True
        return False
    finally:
        session.close()

def get_url_from_hash(hash):
    session = SessionLocal()
    try:
        item = session.query(Backwardhash).filter_by(hash=hash).first()
        return item.url if item else None
    finally:
        session.close()

def add_url_to_hash(hash, url):
    session = SessionLocal()
    try:
        item = Backwardhash(hash=hash, url=url)
        session.merge(item)
        session.commit()
    finally:
        session.close()

def set_crawling(id):
    session = SessionLocal()
    try:
        pages = session.query(Page).filter_by(pageid=id).all()
        if not pages:
            return
        for page in pages:
            crawled, uncrawled = page.status.split(",")[:2]
            page.status = f"{crawled}, {uncrawled}, Crawling..."
        session.commit()
    finally:
        session.close()

def is_user_premium(email):
    session = SessionLocal()
    
    try:
        user = session.query(User).filter_by(email=email).first()
        
        if user is not None:
            return user.premium
        else:
            return False
    finally:
        session.close()

def make_user_premium(email):
    session = SessionLocal()
    
    try:
        user = session.query(User).filter_by(email=email).first()
        
        if user is not None:
            user.premium = True
            session.commit()
    finally:
        session.close()

# make_user_premium("sriramjkini@gmail.com")