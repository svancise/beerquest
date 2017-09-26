# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import json
import re
import os, shutil
from jinja2 import Environment, FileSystemLoader

PATH = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    trim_blocks=False)

VENUES_TO_COLLECT = [
    'https://untappd.com/v/old-ox-brewery/1575236',
    'https://untappd.com/v/ocelot-brewing-company/1879890',
    'https://untappd.com/v/vanish-brewery/4152486',
    'https://untappd.com/v/adroit-theory-brewing-company/548535',
    'https://untappd.com/v/crooked-run-brewing/886724',
    'https://untappd.com/v/quattro-goombas-virginia-craft-brewery/2648732'
]

def render_template(template_filename, context):
    return TEMPLATE_ENVIRONMENT.get_template(template_filename).render(context)

def create_site(data):
    # empty the site folder
    folder = "../site"
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)

    # we need to render a page for each beer type
    beersByType = {};
    for beer in data:
        # create a key based on the beer's type
        beerTypeKey = re.sub(r'\W+', '', beer['type'])

        # add the type key if it is not currently added then add the beer
        if beerTypeKey not in beersByType:
            beersByType[beerTypeKey] = {
                'type': beer['type'],
                'beers' : [beer]
            }
        else:
            beersByType[beerTypeKey]['beers'].append(beer)


    for key in beersByType:
        # create a folder for the type so we can have clean urls
        os.makedirs("../site/" + key)

        fileName = "../site/" + key + "/index.html"
        with open(fileName, 'w') as f:
            # render our jinja template with all the beers for this type
            html = render_template('typePage.html',
                { "beerList" : beersByType[key]["beers"] })
            f.write(html)

    # finally we render the home page
    fileName = "../site/index.html"
    with open(fileName, 'w') as f:
        html = render_template('index.html', {"beers": beersByType})
        f.write(html)

    # copy static assests
    shutil.copytree("./static", "../site/static")

# gathers all of the info for our desired venues
def getBeers():
    beersByVenue = {}
    beersByType = {}
    typeKeys = []

    beers = []

    for venue in VENUES_TO_COLLECT:
        # get the untapped page for the supplied venue.
        requestData = requests.get(venue)
        pageText = requestData.text

        # load the page into beautiful soup
        soup = BeautifulSoup(pageText, "html.parser")

        # download the brewery's logo
        logoUrl = soup.find('div', class_='logo').find('img')["src"]
        logoName = logoUrl.split('/')[len(logoUrl.split('/')) - 1]
        logoRequest = requests.get(logoUrl)
        if logoRequest.status_code == 200:
            with open('./static/img/' + logoName, 'wb') as f:
                f.write(logoRequest.content)

        # dict storing all of the information for the venue
        venueDict = {
            'name' : soup.find('div', class_='venue-name').find('h1').text,
            'address' : soup.find('p', class_='address').text.strip().replace(' ( Map )', ''),
            'phone' : soup.find('p', class_='phone').text,
            'logo': logoName,
            'updated' : soup.find('span', class_='updated-time')['data-time'],
            'untappdUrl' : venue
        }

        # get all the beers listed on the venue's tap list
        for section in soup.find_all('ul', class_="menu-section-list"):
            for beer in section.find_all('li'):
                infoData = beer.find('div', class_='beer-info')

                # we need to strip the special characters from the beer details
                details = re.split("•\s+", infoData.find('h6').find('span').contents[0])

                # get abv and ibu values
                abv = re.sub(r'\s+ABV\s+', '', details[0])
                ibu = re.sub(r'\s+IBU\s+', '', details[1])

                beerType = infoData.find('em').text.split('-')

                # save all the beer's details
                beer = {
                    'name' : infoData.find('a').text,
                    'type' : beerType[0].strip(),
                    'subtype': beerType[1].strip() if len(beerType) > 1 else None,
                    'details' : {
                        'abv': abv,
                        'ibu': ibu
                    },
                    'untappdUrl' : 'https://untappd.com' + infoData.find('a')['href'],
                    'venue' : venueDict
                }

                # add the beer to our list
                beers.append(beer)

    return beers


def main():
    beers = getBeers()
    create_site(beers)

if __name__ == '__main__':
    main()
