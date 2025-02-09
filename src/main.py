from db import db
import requests
from bs4 import BeautifulSoup
from time import sleep


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://www.meinestadt.de/lohne-oldenburg/stadtplan/strassenverzeichnis/a",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}


# helper function to get postcode
def get_german_postcode(city_name):

    url = "https://www.wikidata.org/w/api.php"

    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "de",  # Search in German
        "search": city_name,
        "type": "item",  # Search for items (Wikidata entities)
        "limit": 1,  # We only need the top result
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["search"]:  # Check if any results were found
            item_id = data["search"][0]["id"]  # Get the Wikidata item ID

            # Now, get the postal code property (P281) for the item
            entity_params = {
                "action": "wbgetentities",
                "format": "json",
                "ids": item_id,
                "props": "claims",  # Get the claims (properties)
            }

            entity_response = requests.get(url, params=entity_params)
            entity_response.raise_for_status()
            entity_data = entity_response.json()

            if (
                item_id in entity_data["entities"]
                and "claims" in entity_data["entities"][item_id]
                and "P281" in entity_data["entities"][item_id]["claims"]
            ):
                postcodes = entity_data["entities"][item_id]["claims"]["P281"]

                # Wikidata can have multiple postcodes. Let's return the first one
                if postcodes:
                    try:
                        return int(postcodes[0]["mainsnak"]["datavalue"]["value"])
                    except Exception as e:
                        post = postcodes[0]["mainsnak"]["datavalue"]["value"].split("–")
                        postR = int(post[0])
                        return postR
                else:
                    return None  # No postcode found for that city in wikidata.
            else:
                return None  # No postcode property found for the city

        else:
            return None  # No city found

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
    except (ValueError, KeyError) as e:  # Catch JSON decode errors and key errors
        print(f"Error processing data: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


# database handling
def saveCitysinDB(plz: int, city: str, bundeslandID: int):
    try:
        # check if plz is int
        if type(plz) != int or plz == None:
            print(f"{city} has not a valid plz")
            plz = 1
        ## setup the db
        database = db("localhost", "root", "", "DE_adressen")
        conn = database.connect()
        mycursor = conn.cursor()
        ## prepare statement and data and execute
        sql = "INSERT INTO Stadt VALUES(%s, %s, %s)"
        values = (plz, city, bundeslandID)
        mycursor.execute(sql, values)
        conn.commit()
        conn.close()
        print(f"{city} was added to the database")
        return True
    except Exception as err:
        print(err, "  Stadt:", city)
        return False


# helper functions
def getContent(url) -> str:
    res = requests.get(url, headers=headers)
    return res


def normalize_german_city_name(city_name: str) -> str:
    city_name = city_name.lower()
    city_name = city_name.replace(" ", "-")
    city_name = city_name.replace("ä", "ae")
    city_name = city_name.replace("ö", "oe")
    city_name = city_name.replace("ü", "ue")
    city_name = city_name.replace("ß", "ss")
    return city_name


## TODO: get all cities of a bundesland
def getCitys(url: str, gotError: int) -> list:
    try:
        res = getContent(url)
        soup = BeautifulSoup(res.text, "html.parser")
        getStadt = soup.find_all("span", attrs={"itemprop": "name"})
        cities = list()
        for stadts in getStadt:
            plz = get_german_postcode(normalize_german_city_name(stadts.text))
            cities.append(
                {
                    "name": stadts.text,
                    "plz": plz,
                }
            )

        return cities
    except Exception as err:
        print("something went wrong", err)
        sleep(1)
        if gotError > 2:
            print("something is really wrong")
            return
        getCitys(url, gotError + 1)

    return 0


stadte = getCitys(
    "https://www.citypopulation.de/de/germany/cities/nordrheinwestfalen/", 0
)

for stadt in stadte[3:]:
    saveCitysinDB(stadt["plz"], stadt["name"], 10)
print("done")


## get streets of a city
def getCityStreets(urls: list, gotError: int) -> list:
    strassen: str = list()
    for i, url in enumerate(urls):
        try:
            if gotError > 2:
                print("something is really wrong")
                # pass to the next street chr
                continue
            elif gotError > 3:
                print("something is really really wrong")
                return
            response = getContent(url)
            soup = BeautifulSoup(response.text, "html.parser")
            stadtData = soup.find("ol")

            for stadt in stadtData.find_all("li"):
                strassen.append(stadt.text)
        except Exception as err:
            print("something went wrong", err)

            sleep(1)
            # cut the urls till where it worked
            urls = urls[i:]
            getCityStreets(urls, gotError + 1)
    return strassen


def getUrlsOfStreets(url, numberOfchr, urls: list):
    if numberOfchr > 122:
        return urls
    url += chr(numberOfchr)
    urls.append(url)
    url = url[:-1]
    return getUrls(url, numberOfchr + 1, urls)
