# Danbooru Client API
Download anime wallpapers from Danbooru sites like Konachan.com, Yande.re

### Examples
##### Get post data from a Danbooru site
```python
from danbooru import Danbooru

# Create Danbooru client
K=Danbooru(sitename='Konachan', baseurl='http://www.konachan.net')  

# Get post data via url like xxx/post.json?...
postlist=K.get_post(tags=['touhou','order:score'], page=[1,2,3], page_limit=20)
# Every post you get is stored into a SQLite database named '<sitename>.sqlite'
# The SQLite database is created when creating the client if it does not exist

# Save post data to a file
postlist.save('Th_img_highscore.dat') 
```
The client uses SQLite saving part of the post data, see source code for more detail

##### Download posts with url saved in database
```python
from danbooru import Danbooru
K=Danbooru(sitename='Konachan')

# Download posts to a specific directory, By default the directory name is same to site name
# The download method uses multi-threading approach to download massive images
# If you wish to download a specific post list instead of all posts in database, pass the post
# list parameter. see source code for detail
K.download(dir=None,threadcount=5)
```

##### Get ordered posts and download to different locations
```python
from danbooru import Danbooru
D=Danbooru()
D.split_download('konachan_best', D.create_postlist(order='score'), 100)
```
