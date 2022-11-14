from facebook_scraper import get_posts

for post in get_posts('GracePointLife', pages=2):
    print(post['is_live'])