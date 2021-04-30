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
```

### Code structure
- general: basic function to connect with Spotify API
- recommendation: recommendation function 
- dbdw: source code for [Den Bosch Data Week - Jads Cultural Night](https://dbdw-culture-night.herokuapp.com/)
- genre_exploration: source code for the [Genre Exploration Demo App](https://genre-explore-exp.herokuapp.com/).
- genre_baseline: csv files of the 13 different music genres (avant-garde, 
  blues, classical, country, electronic, folk, jazz, latin, new-age, rap, reggae, rnb and christmas).
- dbdw-music2.csv: songs for 2020 Jads Cultural Night
- nov_music and text_analyze contains some source code for analyzing music event descriptions [under development]

### Local run
- Run with install.requirements.text
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
