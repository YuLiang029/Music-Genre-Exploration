## Music genre dataset

### Descriptions
The music genre dataset contains tracks of 13 music genres (*Avant-garde*, *Blues*, *Classical*, 
*Country*, *Electronic*, *Folk*, *Jazz*, 
*Latin*, *New-age*, *Pop-rock*, *Rap*, *Reggae*, *R&B*) scraped from the 
[Spotify API](https://developer.spotify.com/documentation/web-api/). 
It extends the original dataset used by the two papers with several more music genres. 

To build the dataset, we first get the represented artists from [allmusic.com](https://www.allmusic.com/genres) 
(see the folder [original_genre_artist_from_all_music](https://github.com/YuLiang029/spotify-experiment-framework/tree/master/original_genre_artist_from_all_music)), 
and then extended the dataset with 
[Spotify API for Related Artists](https://developer.spotify.com/documentation/web-api/reference/#endpoint-get-an-artists-related-artists)

### Features
In addition to the features scraped from Spotify, each track is associated with a *baseline score*, 
*baseline ranking* and *density value*. These three variables tells how much a track matches 
the genre-typical tastes on the four audio feature (*energy*, *valence*, *danceability*, and *acousticness*). 
Tracks with higher density values are more representative of the genre. 
The feature *baseline ranking* stands for the ranking sorted by density values 
(lower rank means higher density value). 
The feature *baseline score* is calculated as the reverse of ranking. Please refer to our papers for details.