# CZ4034_IR


Put this on a browser
GET https://api.stocktwits.com/api/2/oauth/authorize?client_id=71fe7d4893672527&response_type=code&redirect_uri=http://www.example.com
Sign in with HL's Stocktwit account (because the app key and secret is under his account)
This will appened a authorization code in the url

Run this on postman
POST https://api.stocktwits.com/api/2/oauth/token?code=0e52895255adab90b30bd7fff9be2348099923c6&client_id=71fe7d4893672527&client_secret=ebe2ef1336d77783e5971599fe8a34c79cdf599f&redirect_uri=http://www.example.com&grant_type=authorization_code
Change the code parameter with the new one
This will return a token to be used in API Requests
