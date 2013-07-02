import urllib2
from datetime import datetime
from functools import wraps

from pyquery import PyQuery as pq
from flask import Flask, jsonify, request, current_app

app = Flask(__name__)

def jsonp(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = str(func(*args, **kwargs).data)
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return current_app.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)

    return decorated_function

@app.route('/')
def index():
    return '/movies/:id'

@app.route('/movies/<id>')
@jsonp
def movies_info(id):
    url = 'http://www.imdb.com/title/%s/' % id

    req = urllib2.Request(url)
    req.add_header('Accept-Language', 'en-US')
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.52 Safari/537.36')
    html = urllib2.urlopen(req).read()

    d = pq(html)

    def tail(el):
        if el:
            return el[0].tail.strip()

    data = {}

    data['imdb_id'] = id
    data['imdb_url'] = url

    data['title'] = d('#overview-top h1 span:eq(0)').text()
    data['year'] = int(d('#overview-top h1 .nobr').text().split(u'\u2013')[0].strip('() '))
    data['poster'] = d('#img_primary img').attr('src')
    data['rating'] = d('.star-box-giga-star').text()
    data['rating_count'] = int(d('span[itemprop=ratingCount]').text().replace(',', ''))
    data['plot_simple'] = d('p[itemprop=description]').text()
    data['actors'] = [d(x).text() for x in d('.cast_list span[itemprop=name]')]
    data['rated'] = d('span[itemprop=contentRating]').text()
    data['languages'] = [d(x).text() for x in d('#titleDetails h4:contains("Language:")').siblings('a')]
    data['filming_locations'] = d('#titleDetails h4:contains("Filming Locations:")').siblings('a').text()
    data['country'] = [d(x).text() for x in d('#titleDetails h4:contains("Country:")').siblings('a')]
    data['also_known_as'] = [tail(d('#titleDetails h4:contains("Also Known As:")'))]
    data['directors'] = [d(x).text() for x in d('div[itemprop=director] a')]
    data['writers'] = [d(x).text() for x in d('div[itemprop=creator] a')]
    data['genres'] = [d(x).text() for x in d('div[itemprop=genre] a')]

    runtime = d('#titleDetails h4:contains("Runtime:")').parent().text()

    if runtime:
        data['runtime'] = [x.strip() for x in runtime.split('Runtime:')[1].split('|')]
    
    release_date = ' '.join(tail(d('#titleDetails h4:contains("Release Date:")')).split(' ')[:3])
    
    if release_date:
        if '(' in release_date:
            data['release_date'] = int(release_date.split(' ')[0] + '0000')
        else:
            rd = datetime.strptime(release_date, '%d %B %Y').date()
            data['release_date'] = int('%.2d%.2d%.2d' % (rd.year, rd.month, rd.day))

    movie_type = d('.infobar')[0].text.split('-')[0].strip()

    if movie_type == 'TV Series':
        data['type'] = 'TVS'
    elif movie_type == 'TV Movie':
        data['type'] = 'TVM'
    elif movie_type == 'Video':
        data['type'] = 'V'
    elif movie_type == 'Video Game':
        data['type'] = 'VG'
    else:
        data['type'] = 'M'

    return jsonify(**data)

if __name__ == '__main__':
    app.run(debug=True, port=1234) 