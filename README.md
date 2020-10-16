# nike-bot
Simple scalping bot to buy shoes from nike.com at release. Selenium and request

## Installation
1) Download Chrome browser and [chromedriver](https://chromedriver.chromium.org/downloads)
2) Create a `login` text file with your nike.com login details
```
email
password
```

## Usage
1) Run the script, chrome should navigate to nike.com and login
2) Once logged on, navigate to the page of the item you want to purchase. eg. https://www.nike.com/launch/t/womens-air-jordan-1-lucky-green
3) You will be asked to select an item size you want to purchase, enter number between 0 and `n`
4) Script will buy the item once it becomes available, you will have to go through the checkout manually

## TODO
Test at launch

Emulate all of the tracking requests and workout how the tokens are calculated
