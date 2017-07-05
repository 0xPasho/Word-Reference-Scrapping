# -*- coding: utf-8 -*-
# encoding=utf8 
import sys  
import MySQLdb
import requests 

from selenium import webdriver  
from selenium.common.exceptions import NoSuchElementException  
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.remote.command import Command

from bs4 import BeautifulSoup
import stem.process
from stem import Signal
from stem.control import Controller

from splinter import Browser

def newIdentity():
    with Controller.from_port(port = 9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)

def webRequest( word ):
    driver.get(url+word)
    html_source = driver.page_source
    return BeautifulSoup(html_source, "html.parser")

def convertWord( sentence ):
    return unicode(str(sentence), 'latin-1')

def insertValues( idWord, meaning, example, importance, url, sourceName):
    if example:
        if example[0] == ' ':
            example = example[1:]
    else:
        example = None
    meaning = meaning.decode('unicode_escape').encode('iso8859-1').decode('utf8')
    if example: 
        example = example.decode('unicode_escape').encode('iso8859-1').decode('utf8')
    print 'Definition number - ' + str(importance)
    print 'Definition - ',
    print meaning
    print 'Example - ',
    print example

    
    #cursor.execute('INSERT INTO wordsdefinitions(definition, idLanguage, example, idWord, importance) VALUES ("'+str(meaning)+'","1","'+str(example)+'",'+str(idWord)+',"'+str(importance)+'")')
    cursor.execute("""INSERT INTO dat_word_definitions(definition, idLanguage, example, idWord, importance,source,sourceName) VALUES (%s,%s,%s,%s,%s,%s,%s)""",(meaning,1,example,idWord,importance,url,sourceName))

reload(sys)
sys.setdefaultencoding('utf-8')
# Connect
db = MySQLdb.connect(host="127.0.0.1",
                     user="root",
                     passwd="",
                     db="db_diccionario")


# Initializing variables
limit = 0
offset = 500
session = requests.session()
url = "http://www.wordreference.com/definicion/"
cursor = db.cursor()

proxyIP = "127.0.0.1"
proxyPort = 9150
profile = FirefoxProfile()
profile.set_preference('network.proxy.type', 1)
profile.set_preference('network.proxy.socks', proxyIP)
profile.set_preference('network.proxy.socks_port', proxyPort)

binary = FirefoxBinary(r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe')
driver = webdriver.Firefox(firefox_binary=binary, firefox_profile=profile)
for x in range(0, 10000):
    #print 'Extracting information from database'
    # Words in local database
    cursor.execute("SELECT * FROM dat_words LIMIT "+str(limit)+","+str(offset))
    # Get the number of rows in the resultset
    numrows = cursor.rowcount
    for y in range(0, numrows):
        rows = cursor.fetchall()
        for row in rows: 
            # Word
            idWord = row[0]
            # Convert word to unicode
            word = convertWord(str(row[1]))
            # Request to WordReference.com
            html = webRequest(word)
            # Printing process
            print '---------------------------------------------------------------------------'
            print "Actual word: "+word
            print "Actual URL: "+url+word
            wordDefinitions = html.find_all('ol',{'class':'entry'})
            errorMessage = html.find_all('p',{'id':'noEntryFound'})
            #print wordDefinitions
            for wordDefinition in wordDefinitions:
                # For separate each definition element
                eachDefinition = (wordDefinitions[0].contents[0]).find_all('li')
                # Get HTML code of the elements
                definitionOmited = wordDefinition.contents[0]
                # Separate text by > symbol 
                definitionOmitedSplited = str(definitionOmited).split('>')
                # Got the first values, that was omited by default (meaning and the example) 
                meaningOmited = (definitionOmitedSplited[1].split('<'))[0]
                exampleOmited = (definitionOmitedSplited[3].split('<'))[0]
                insertValues(idWord, meaningOmited, exampleOmited, 1, url+word, 'WordReference.com')
                for indexDefinition, definition in enumerate(eachDefinition):
                    definitionSplited = definition.contents[0].split('.')
                    meaning = definition.contents[0]
            
                    if definition.find_all('span',{'class':'i'}):
                        example = (definition.find_all('span',{'class':'i'}))[0].contents[0]
                    else:
                        example = None
                    print 'inserting values'
                    if meaning and meaning.strip(): insertValues(idWord, meaning, example, indexDefinition+2, url+word, 'WordReference.com')
            db.commit()
            if rows < 500:
                sys.exit()
# Close the connection
db.close()


