# Danbooru Client API

## Usage
- Get post data from a Danbooru site
```python
from danbooru import Danbooru
K=Danbooru(sitename='Konachan', baseurl='http://www.konachan.net')  # Create Danbooru client
postlist=K.get_post(tags=['touhou','order:score'], page=[1,2,3], page_limit=20) # Get post data via url like xxx/post.json?...
postlist.save('Th_img_highscore.dat') # Save post data to a file
```
The client uses SQLite saving part of the post data, see source code for more detail

- Download posts with url saved in database
```python
from danbooru import Danbooru
K=Danbooru(sitename='Konachan')
K.download(dir=None,threadcount=5)
```
