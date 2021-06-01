## Recommendation module
### Descriptions
This folder contains the core recommendation functions for music genre exploration 
and music genre suggestions (i.e., recommending music genres that users are interested in). 

### Music genre recommendation: track recommendations within a genre
The music genre exploration algorithm is a content-based approach 
on Spotify audio features using Gaussian Mixture Model (more details can be found in the papers). 
The approach allows the recommendations to be generated with a trade-off between representativeness and personalization.
Additionally, a popular-based approach is also implemented in the code.


### Music genre suggestion
Two music genre suggestion approaches are implemented in the code:
1. Genre suggestions based on the cosine similarity of the individual user profile (represented by tags listened by the user) 
and the music genre (represented by tags associated with the genre), 
2. Genre suggestions based on Personalized Page Rank, which finds music genres 
   in a tag-based graph that are relevant to a user