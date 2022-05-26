"""
Rental Data Project
By Cole Koryto
Inspired from: https://oxylabs.io/blog/python-web-scraping
"""
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import date
import os
import pathlib
import csv
import datetime
from webdriver_manager.chrome import ChromeDriverManager  # pip3 install webdriver_manager


# function checks if user inputted name is viable
def checkCityName(userInput):
    # pulls up page for user entered city
    url = "https://www.trulia.com/for_rent/" + userInput + ",MI/"
    driver.get(url)
    firstPageContent = driver.page_source
    soup = BeautifulSoup(firstPageContent, features="html.parser")

    # checks if results can be found for user's page
    if soup.find(attrs={'data-testid': 'srp-no-results-message'}) != None:
        print("The entered city name is not valid\n")
        return False
    else:
        return True


# runs code to get and process rental data
if __name__ == "__main__":
    # sets up main selenium driver
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.minimize_window()

    # inputs a viable city name from the user and gets target URL
    viableNameFound = False
    userInput = ""
    while not viableNameFound:
        userInput = input("Please enter a Michigan city name: ")
        print("Checking for city page...")
        if checkCityName(userInput):
            viableNameFound = True

    # loads the contents of the page into BeautifulSoup
    targetURL = "https://www.trulia.com/for_rent/" + userInput + ",MI/"
    driver.get(targetURL)
    firstPageContent = driver.page_source
    soup = BeautifulSoup(firstPageContent, features="html.parser")

    # finds the number of pages of data on trulia.com
    pageNums = []
    for element in soup.findAll(attrs={'class': 'ButtonBase-sc-14ooajz-0 PaginationButton-sc-1yuoxn6-1 fea-DjF'}):
        pageNums.append(element.text)
    if len(pageNums) > 0:
        totalPages = int(pageNums[len(pageNums) - 1])
    else:
        totalPages = 1

    # extracts rental information from all available pages
    prices = []
    beds = []
    baths = []
    sqft = []
    addresses = []
    CONST_FETCHING_LOOP = 10
    print("\nFetching Trulia rental data")

    # loops CONST_FETCHING_LOOP times to ensure all listings are retrieved, does this to make sure all listings are grabbed
    # this has to be done because Trulia randomly excludes some listings when you look up, so it much be run several times
    # to get all listings
    pagesProcessed = 0
    for i in range(0, CONST_FETCHING_LOOP):

        # loops over all pages for city
        for currentPageNum in range(1, totalPages+1):
            # prints current page progress
            print("Loading... {0:.5} %".format(str(pagesProcessed / (totalPages * CONST_FETCHING_LOOP) * 100)))

            # sets up web driver for current page
            driver.get(targetURL + str(currentPageNum) + "_p/")
            currentPageContent = driver.page_source
            soup = BeautifulSoup(currentPageContent, features="html.parser")

            # navigates to each listing on a page
            for listing in soup.findAll(attrs={'class': 'Grid__CellBox-sc-144isrp-0 SearchResultsList__WideCell-b7y9ki-2 jiZmPM'}):
                # checks if this listing block is empty of data by checking if there is a data-testid attribute
                if not listing.has_attr('data-testid'):
                    continue

                # gets addresses by getting the correct data-testid attribute
                if listing.find(attrs={'data-testid': 'property-address'}) != None:
                    tag = listing.find(attrs={'data-testid': 'property-address'})
                    attribute = tag['title']

                    # checks if address has already been put in list in another iteration
                    if attribute in addresses:
                        continue
                    else:
                        addresses.append(attribute)
                else:
                    addresses.append("No Data")

                # gets prices by getting the correct data-testid attribute
                if listing.find(attrs={'data-testid': 'property-price'}) != None:
                    tag = listing.find(attrs={'data-testid': 'property-price'})
                    attribute = tag['title']
                    prices.append(attribute)
                else:
                    prices.append("No Data")

                # gets the number of beds by getting the correct data-testid attribute
                if listing.find(attrs={'data-testid': 'property-beds'}) != None:
                    tag = listing.find(attrs={'data-testid': 'property-beds'})
                    attribute = tag['title']
                    beds.append(attribute)
                else:
                    beds.append("No Data")

                # gets the number of baths by getting the correct data-testid attribute
                if listing.find(attrs={'data-testid': 'property-baths'}) != None:
                    tag = listing.find(attrs={'data-testid': 'property-baths'})
                    attribute = tag['title']
                    baths.append(attribute)
                else:
                    baths.append("No Data")

                # gets the square footage by getting the correct data-testid attribute
                if listing.find(attrs={'data-testid': 'property-floorSpace'}) != None:
                    tag = listing.find(attrs={'data-testid': 'property-floorSpace'})
                    attribute = tag['title']
                    sqft.append(attribute)
                else:
                    sqft.append("No Data")

            # increments pages processed
            pagesProcessed += 1

    # exits chrome webpage
    driver.quit()

    # gets current date for output
    today = date.today()
    currentDate = today.strftime("%m-%d-%Y")

    # makes new file name
    newFileName = 'Active Listings on ' + currentDate + '.csv'

    # check if program has already ran today by looking if active listings file for today is already made
    currentFilePath = pathlib.Path(__file__).parent.absolute()
    filesInCurrentFolder = os.listdir(currentFilePath)
    alreadyRan = False
    if filesInCurrentFolder.__contains__(newFileName):
        alreadyRan = True

    # sets up data output with pandas
    column1 = pd.Series(addresses, name='Addresses')
    column2 = pd.Series(prices, name='Prices')
    column3 = pd.Series(beds, name='Beds')
    column4 = pd.Series(baths, name='Baths')
    column5 = pd.Series(sqft, name='Square Footage')
    df = pd.DataFrame({'Addresses': column1, 'Prices': column2, 'Beds': column3, 'Baths': column4, 'Square Footage': column5})
    df.to_csv(newFileName, index=False, encoding='utf-8')
    print("\nAll data found. See Active Listings CSV file for today's listings.")



    """
    Takes today's listings and compares them to the Master Rental Listing Data file and updates the master file. 
    Adds new listings to master file and removes expired listings. Expired listings are saved to Listing Data Records.
    """

    # finds correct previous file to open
    filesInCurrentFolder = os.listdir(currentFilePath)
    filesInCurrentFolder.remove(newFileName)
    listingsFileNames = []
    previousFileName = "None"
    for fileName in filesInCurrentFolder:
        if "Active Listings on " in fileName:
            listingsFileNames.append(fileName)

    # stops program if no previous data exists
    if len(listingsFileNames) == 0:
        print("No previous Active Listings file found. Rerun tomorrow to update Master Rental Listings file")
        input("Press any key to exit program")
        exit()

    # finds listing file that is closest to today
    smallestDifference = 999999999
    for fileName in listingsFileNames:
        year = int(fileName[25:29])
        month = int(fileName[19:21])
        day = int(fileName[22:24])
        daysDifference = (date.today() - datetime.date(year, month, day)).days
        if daysDifference < smallestDifference:
            smallestDifference = daysDifference
            previousFileName = fileName

    # checks if Master Rental Listing Data.csv exists yet
    print("\nUpdating Master Rental Listing Data and Listing Data Records file...\n")
    masterFileExists = False
    for fileName in filesInCurrentFolder:
        if fileName == "Master Rental Listing Data.csv":
            masterFileExists = True
            break

    # puts data in list and removes listings if master rental listing data.csv if the file exists
    if masterFileExists:
        # takes data from Master Rental Listing Data.csv and puts it into masterFileData List
        print("Master file exists, updating file")
        with open("Master Rental Listing Data.csv") as csvDataFile:
            masterFileData = list(csv.reader(csvDataFile))
        masterFileData.pop(0)

        # puts addresses from master file into list for easier processing
        masterAddresses = []
        for i in range(0, len(masterFileData)):
            masterAddresses.append(masterFileData[i][0])

        # checks if each listing in masterFileData is in today's listings, if not, it is removed from masterFileData
        print("Removing expired listings: ")
        savedData = [[]]
        #print(masterFileData)
        #checkFinished = False
        for i in range(0, len(masterFileData)):
            if i >= len(masterFileData) - 1:
                break
            #print("Checking: " + str(masterFileData[i]))
            addressNotPresent = True
            while addressNotPresent:
                if i >= len(masterFileData) - 1:
                    break
                if masterAddresses[i] in addresses:
                    addressNotPresent = False
                else:
                    print(masterAddresses[i])
                    savedData.append([masterFileData[i][0], masterFileData[i][1], masterFileData[i][2], masterFileData[i][3], masterFileData[i][4], masterFileData[i][5]])
                    masterFileData.pop(i)
                    masterAddresses.pop(i)

        # sets up data output to records file
        if len(savedData) >= 1:
            recordsFile = open("Listing Data Records.csv", 'a+', newline='')
            with recordsFile:
                write = csv.writer(recordsFile)
                write.writerows(savedData)

        # adds the number of days the listing has been active if program has not already ran today
        if not alreadyRan:
            # calculates how many days to add
            year = int(previousFileName[25:29])
            month = int(previousFileName[19:21])
            day = int(previousFileName[22:24])
            daysToAdd = (date.today() - datetime.date(year, month, day)).days

            # increments the listing duration for each listing
            for i in range(0, len(masterFileData)):
                masterFileData[i][5] = int(masterFileData[i][5]) + daysToAdd

    # initializes masterFileData list with today's data, and makes new records file
    else:

        print("Master file does NOT exist, creating new master and records file")
        masterFileData = []
        for i in range(0, len(addresses)):
            #print([addresses[i], prices[i], beds[i], baths[i], sqft[i], 0])
            masterFileData.append([addresses[i], prices[i], beds[i], baths[i], sqft[i], 1])

        # creates Listing Data Records file
        recordsFile = open("Listing Data Records.csv", 'w+', newline='')
        with recordsFile:
            write = csv.writer(recordsFile)
            write.writerow(['Addresses', 'Prices', 'Beds', 'Baths', 'Square Footage', 'Listing Duration'])

    # adds the new listings to the masterFileData list that are not already in list
    print("Adding: ")
    for address in addresses:
        addressFound = False
        for i in range(0, len(masterFileData)):
            if address in masterFileData[i]:
                addressFound = True
        if not addressFound:
            print(addresses[addresses.index(address)])
            masterFileData.append([addresses[addresses.index(address)], prices[addresses.index(address)], beds[addresses.index(address)], baths[addresses.index(address)], sqft[addresses.index(address)], 1])

    # updates master rental listing csv file by overwriting master rental listing csv file

    # takes data from masterFileData and puts in appropriate list
    masterAddresses = []
    for i in range(0, len(masterFileData)):
        masterAddresses.append(masterFileData[i][0])
    masterPrices = []
    for i in range(0, len(masterFileData)):
        masterPrices.append(masterFileData[i][1])
    masterBeds = []
    for i in range(0, len(masterFileData)):
        masterBeds.append(masterFileData[i][2])
    masterBaths = []
    for i in range(0, len(masterFileData)):
        masterBaths.append(masterFileData[i][3])
    masterSqft = []
    for i in range(0, len(masterFileData)):
        masterSqft.append(masterFileData[i][4])
    masterDuration = []
    for i in range(0, len(masterFileData)):
        masterDuration.append(masterFileData[i][5])

    # sets up data output
    series1 = pd.Series(masterAddresses, name='Addresses')
    series2 = pd.Series(masterPrices, name='Prices')
    series3 = pd.Series(masterBeds, name='Beds')
    series4 = pd.Series(masterBaths, name='Baths')
    series5 = pd.Series(masterSqft, name='Square Footage')
    series6 = pd.Series(masterDuration, name='Listing Duration')
    df = pd.DataFrame(
        {'Addresses': series1, 'Prices': series2, 'Beds': series3, 'Baths': series4, 'Square Footage': series5, 'Listing Duration': series6})
    df.to_csv("Master Rental Listing Data.csv", index=False, encoding='utf-8')
