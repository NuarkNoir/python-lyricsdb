from lxml import etree

import lxml.html
import requests
import re

import queue
import idna.idnadata

try:
    from lyricsdb import db
except:
    import db

def element_exists(Author, Album, Title):
    db.connect()
    res = db.find_item(Author, Album, Title)
    db.close()
    return res


def put_text(Author, Album, Title, Text):
    db.connect()
    db.put(Author, Album, Title, Text)
    db.close()


author_selector = ".list-group-item > a"
album_selector = "a"
song_selector = "a"
cats = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def main():
    songid = 0
    for cat in cats:
        print("Processing of category '{cat}'".format(cat=cat))
        # Getting page of category
        html = requests.get(f"https://www.lyricfinder.org/search/a-z/{cat}").text
        root = lxml.html.fromstring(html)
        els = root.cssselect(author_selector)

        artistslist = [(el.text.replace(" Lyrics", ""), el.get("href").replace("\n", "")) for el in els]
        del html, root, els

        #Getting page of artist of category
        for artist, art_href in artistslist:
            print("\tProcessing of artist '{artist}'".format(artist=artist.strip()))
            html = requests.get("https://www.lyricfinder.org" + art_href).text
            root = lxml.html.fromstring(html)
            alb_card = root.cssselect(".col-md-6 .card")
            for card in alb_card:
                if card.cssselect(".card-header")[0].text.strip() == "Albums":
                    root = lxml.html.fromstring(etree.tostring(card))
                    break
            els = root.cssselect(album_selector)
            albumslist = [(el.text_content(), el.get("href")) for el in els]
            del html, root, els

            # Getting page of album of artist of category
            try:
                for album, alb_href in albumslist:
                    if len(album) == 0:
                        continue
                    print("\t\tProcessing of album '{album}'".format(album=album.strip()))
                    html = requests.get("https://www.lyricfinder.org" + alb_href).text
                    root = lxml.html.fromstring(html)
                    alb_card = root.cssselect(".col-md-6 .card")
                    try:
                        for card in alb_card:
                            if card.cssselect(".card-header")[0].text.strip() == "Tracks":
                                root = lxml.html.fromstring(etree.tostring(card))
                                break
                    except:
                        print("\t\tNo tracks in this album.'")
                        continue
                    els = root.cssselect(song_selector)
                    songslist = [(el.text_content(), el.get("href")) for el in els]
                    del html, root, els

                    # Getting page of song of album of artist of category
                    try:
                        for song, sng_href in songslist:
                            if element_exists(artist, album, song):
                                print("\t\t\t\tDuplicate item found.")
                                continue
                            songid += 1
                            print(f"\t\t\tProcessing of song '{song.strip()}'")
                            html = requests.get("https://www.lyricfinder.org" + sng_href).text
                            if not song in html:
                                print("\t\t\t\tNo text found for this song")
                                put_text(artist, album, song, "No text found for this song")
                                continue
                            root = lxml.html.fromstring(html)
                            content = root.cssselect(".container")[0]
                            root = lxml.html.fromstring(etree.tostring(content))
                            content = root.cssselect("div.col-lg-6")[0]
                            lines = re.sub("(Written)(.*)", "", content.text_content().strip())
                            lines = re.sub("(Publisher)(.*)", "", lines.strip())
                            lines = lines.replace("Lyrics powered by Lyric Find", "")\
                                        .replace("(adsbygoogle = window.adsbygoogle || []).push({});", "").split("\n")[1:]
                            text = "\n".join(lines).strip()
                            put_text(artist, album, song, text)
                    except:
                        print("\t\tNo songs in this album.'")
                        continue
            except:
                print("\t\tNo albums from this author.'")
                continue
        return


if __name__ == '__main__':
    main()
    """
    db.connect()
    s = "SELECT * FROM SongsWords WHERE Title LIKE 'A%'"
    print(db.execute(s).fetchall())
    db.close()
    """
