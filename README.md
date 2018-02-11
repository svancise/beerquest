# beerquest
Find the beer you're craving: http://beerquest.s3-website-us-east-1.amazonaws.com/

Pulls taplists from various venues and organizes them by beer type. The data is then used to create a static site using Jinja2 templates. The goal is to create a SUPER lightweight website that can load very quickly on even a spotty connection. Next step is to run the collection and site generation on Lambda to update everyday. The website is hosted on s3 for next to no cost.
