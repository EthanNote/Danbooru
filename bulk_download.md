# Bulk Download

## Beaware
- Server could be unreachable, leading to download exception
- Server may response same post in different pages, database unique constraint will handle it
- Server may miss some posts: a post matchs search condition and page index may not be returned
- Too many files in same folder may seriously slow down MS Windows, use split download

## Demo: Yande.re bulk download

#### step 1: get and store post information
```python
from danbooru import Danbooru
Y=Danbooru('Yande.re', 'https://yande.re')  # Creating or using 'Yande.re.sqlite'
Y.get_post(['order:score'], range(1,200), 100)
```

#### step 2: download posts
```python
from danbooru import Danbooru
Y=Danbooru('Yande.re', None)  # Since we don't need site url

# Create a post list from database, with a descent score order
postlist=Y.create_postlist(order = 'score') 

# download image files in subdirs of 'yande.re_best', each subdir has a numeric name indicades the group order
Y.split_download('yande.re_best', postlist, 100) 
```

#### Tactics
- Use sqlite client to see how many post items has stored in database
- Run step 1 for serveral times to pick up posts missed by server
- Use cache dir, this client will see if a post exists in catch dir before download, 
cache dir has same name with site name, here is 'Yande.re'
