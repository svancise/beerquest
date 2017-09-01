# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import json
import re
import os
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

def create_index_html(data):
    # we need to render a page for each beer type
    for key in data["typeKeys"]:
        # create a folder for the type so we can have clean urls
        os.makedirs("../site/" + key[0])

        fileName = "../site/" + key[0] + "/index.html"
        with open(fileName, 'w') as f:
            # render our jinja template with all the beers for this type
            html = render_template('typePage.html', { "beerList" : data["types"][key[0]]})
            f.write(html)

    # finally we render the home page
    fileName = "../site/index.html"
    with open(fileName, 'w') as f:
        html = render_template('index.html', data)
        f.write(html)

# gathers all of the info for our desired venues
def getBeers():
    beersByVenue = {}
    beersByType = {}
    typeKeys = []


    for venue in VENUES_TO_COLLECT:
        # get the untapped page for the supplied venue.
        requestData = requests.get(venue)
        pageText = requestData.text

        # load the page into beautiful soup
        soup = BeautifulSoup(pageText, "html.parser")

        # dict storing all of the information for the venue
        venuDict = {
            'name' : soup.find('div', class_='venue-name').find('h1').text,
            'address' : soup.find('p', class_='address').text.strip().replace(' ( Map )', ''),
            'phone' : soup.find('p', class_='phone').text,
            'updated' : soup.find('span', class_='updated-time')['data-time'],
            'untappdUrl' : venue,
            'beersOnTap' : []
        }

        # get all the beers listed on the venue's tap list
        for section in soup.find_all('ul', class_="menu-section-list"):
            for beer in section.find_all('li'):
                infoData = beer.find('div', class_='beer-info')

                # we need to strip the special characters from the beer details
                details = re.split(u"â\x80¢",infoData.find('h6').find('span').contents[0])

                beerType = infoData.find('em').text.split('-')

                # save all the beer's details
                beer = {
                    'name' : infoData.find('a').text,
                    'type' : beerType[0].strip(),
                    'subtype': beerType[1].strip() if len(beerType) > 1 else None,
                    'details' : details[0].strip(),
                    'untappdUrl' : 'https://untappd.com' + infoData.find('a')['href']
                }

                # add the beer to the venue's information
                venuDict['beersOnTap'].append(beer)

                # create a key based on the beer's type
                beerTypeKey = re.sub(r'\W+', '', beer['type'])

                # add the type key if it is not currently added then add the beer
                if beerTypeKey not in beersByType:
                    typeKeys.append((beerTypeKey, beer["type"]))
                    beersByType[beerTypeKey] = {
                        'type': beer['type'],
                        'beers': [beer]
                    }
                else:
                    beersByType[beerTypeKey]['beers'].append(beer)

    # sort the keys
    typeKeys.sort(key=lambda x: x[0])

    return {
        "venues" : beersByVenue,
        "types" : beersByType,
        "typeKeys": typeKeys
    }


def main():
    beers = getBeers()
    create_index_html(beers)

if __name__ == '__main__':
    main()
