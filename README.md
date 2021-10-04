[![Build Status](https://jenkins.tuneblendr.com/job/argueview-js/job/master/42/badge/icon)](https://jenkins.tuneblendr.com/job/argueview-js/job/master/42/)
## Study Framework for Music Genre Exploration
This repository includes the several projects for music genre exploration.

### Relevant papers:
[Yu Liang and Martijn C. Willemsen. 2019. Personalized 
Recommendations for Music Genre Exploration. (UMAP19)](https://dl.acm.org/doi/abs/10.1145/3320435.3320455)
  ```
  @inproceedings{Liang2019UMAP,
  author = {Liang, Yu and Willemsen, Martijn C.}, 
  title = {Personalized Recommendations for Music Genre Exploration}, 
  year = {2019}, 
  isbn = {9781450360210}, 
  publisher = {Association for Computing Machinery}, 
  address = {New York, NY, USA}, 
  url = {https://doi.org/10.1145/3320435.3320455}, 
  doi = {10.1145/3320435.3320455}, 
  booktitle = {Proceedings of the 27th ACM Conference on User Modeling, Adaptation and Personalization}, 
  pages = {276–284}, 
  numpages = {9}, 
  keywords = {exploration, user-centric evaluation, personalization, content-based music recommendation, preference developing, user goals}, 
  location = {Larnaca, Cyprus}, 
  series = {UMAP '19}
}
```

[Yu Liang and Martijn C. Willemsen. 2021. Interactive Music Genre Exploration with Visualization and Mood Control (ACM IUI 2021)](https://dl.acm.org/doi/abs/10.1145/3397481.3450700)
```
@inproceedings{10.1145/3397481.3450700,
author = {Liang, Yu and Willemsen, Martijn C.},
title = {Interactive Music Genre Exploration with Visualization and Mood Control},
year = {2021},
isbn = {9781450380171},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3397481.3450700},
doi = {10.1145/3397481.3450700},
booktitle = {26th International Conference on Intelligent User Interfaces},
pages = {175–185},
numpages = {11},
keywords = {mood, user study, recommender system, visualization, music, interactive design, exploration},
location = {College Station, TX, USA},
series = {IUI '21}
}

[Yu Liang and Martijn C. Willemsen. 2021. The role of preference consistency, defaults and musical expertise in users’ exploration 
behavior in a genre exploration recommender (Recsys 2021)](https://doi.org/10.1145/3460231.3474253)
```
@inproceedings{10.1145/3460231.3474253,
author = {Liang, Yu and Willemsen, Martijn C.},
title = {The Role of Preference Consistency, Defaults and Musical Expertise in Users’ Exploration Behavior in a Genre Exploration Recommender},
year = {2021},
isbn = {9781450384582},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3460231.3474253},
doi = {10.1145/3460231.3474253},
abstract = { Recommender systems are efficient at predicting users’ current preferences, but how
users’ preferences develop over time is still under-explored. In this work, we study
the development of users’ musical preferences. Exploring musical preference consistency
between short-term and long-term preferences in data from earlier studies, we find
that users with higher musical expertise have more consistent preferences at their
top-listened artists and tags than those with lower musical expertise. Users typically
chose to explore genres that were close to their current preferences, and this effect
was stronger for expert users. Based on these findings we conducted a user study on
genre exploration to investigate (1) whether it is possible to nudge users to explore
more distant genres, and (2) how users’ exploration behaviors within a genre are influenced
by default recommendation settings that balance personalization with genre representativeness
in different ways. Our results show that users were more likely to select the more
distant genres if these were presented at the top of the list. However, users with
high musical expertise were less likely to do so, consistent with our earlier findings.
When given a representative or mixed (balanced) default for exploration within a genre,
users selected less personalized recommendation settings and explored further away
from their current preferences, than with a personalized default. However, this effect
was moderated by users’ slider usage behaviors. Overall, our results suggest that
(personalized) defaults can nudge users to explore new, more distant genres and songs.
However, the effect is smaller for those with higher musical expertise levels. },
booktitle = {Fifteenth ACM Conference on Recommender Systems},
pages = {230–240},
numpages = {11},
keywords = {Default, Music genre exploration, Musical expertise, Nudge, Preference consistency},
location = {Amsterdam, Netherlands},
series = {RecSys '21}
}

```

### Code structure
- general: basic function to connect with Spotify API
- recommendation: recommendation function 
- dbdw: source code for Den Bosch Data Week - Jads Cultural Night 2020
  (click to see the details about [Jads Cultural Night 2020](https://www.denbosch.nl/nl/denboschdataweek/dinsdag))
- genre_exploration: source code for the Genre Exploration Demo App
- nudge: source code for the 
[Music Genre Exploration Demo](https://music-genre-explore.herokuapp.com/) (Demo of the Recsys 2021 paper)
- genre_baseline: csv files of the 13 different music genres (avant-garde, 
  blues, classical, country, electronic, folk, jazz, latin, new-age, rap, reggae, rnb and christmas).
- dbdw-music2.csv: songs for 2020 Jads Cultural Night
- nov_music and text_analyze contains some source code for analyzing music event descriptions [inactive in development]

### Local run
- Run with install.requirements.txt
- Run with docker

### Heroku deployment with Docker
See [Container Registry & Runtime (Docker Deploys)](https://devcenter.heroku.com/articles/container-registry-and-runtime) for deployment details
```
heroku container:login
heroku create
heroku container:push web
heroku container:release web
heroku open
```

### Acknowledgement
- Thanks to everyone who has contributed to the repository: Sophia Hadash and Jolijn Martens
- Special thanks to Thijs Meeuwisse and Joris Hilberink for their contribution to the interactive design and programming
(contour plot, bar charts and the mood sliders)of the genre exploration app.
- Special thanks to Mark Graus for providing the basic flask framework I could work with.
- Special thanks to Martijn Willemsen for providing the valuable feedback, and all other kinds of help.
