import requests
from flask import Flask
from flask_restful import Api, Resource
from flask import request
import nltk
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.metrics.distance import jaccard_distance
from nltk.util import ngrams
import pyodbc
import json
from collections import defaultdict


app = Flask(__name__)
api = Api(app)
stop_words = set(stopwords.words("english"))
lem = WordNetLemmatizer()

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-97U22LI;DATABASE=CZ4034;UID=sa;PWD=password1')
cursor = conn.cursor()

company_ticker = {"baba":"alibaba",
                  "amzn":"amazon",
                  "aapl":"apple",
                  "tsla":"tesla",
                  "msft":"microsoft",
                  "fb":"facebook",
                  "googl":"google",
                  "nio":"nio",
                  "twtr":"twitter",
                  "nflx":"netflix"
                 }



class SearchResource(Resource):    
    def __init__(self):
        self.InvIndex = defaultdict(set, self.getInvIndex())
        self.words = pd.Series(list(self.InvIndex.keys()))
        
    def get(self):
        query = request.args.get('query')
        matched_index = self.search(query)
        
        data = self.queryDB('tweets',matched_index).to_json() 
        
        return {'content': data}
    
    def post(self):
        return {"data": "posted!"}
    
    def search(self, query, exact = False):
        matched_documents = None
        words = word_tokenize(query)
        prev = None
        
        for word in words:
            word_lower = word.lower()
            if word_lower not in stop_words:
                cur = lem.lemmatize(word_lower)
                
                print("CUR: ")
                print(cur)
                
                if cur in company_ticker:
                    cur = company_ticker[cur]
                
                reco_cur = self.JDreco(cur)
                
                print(reco_cur.get(0))
                
                matches = self.InvIndex[reco_cur.get(0)]
                
                match_index = [item[0] for item in matches]
                print(match_index)
    
                if matched_documents is None:
                    matched_documents = match_index
                    
                else:
                    matched_documents = list(set.intersection(set(matched_documents),set(match_index)))
                    
        return matched_documents
    
    
    def jaccard(self,entry, gram_number):
       
        spellings = self.words[self.words.str.startswith(entry[0])]
        distances = ((jaccard_distance(set(ngrams(entry,gram_number)),
                                           set(ngrams(self.words,gram_number))), self.words)
                     for word in spellings)
        closest = min(distances)
        
        print(closest)
        return closest[1]
    
    
    def JDreco(self,entry):
        return self.jaccard(entry, 2)
    
    def getInvIndex(self):
        with open('InvIndex.json') as infile:
            data = json.load(infile)
        return data

    def queryDB(self,table, dbQuery):
        return pd.read_sql_query('SELECT * FROM CZ4034.dbo.'+table+' where Doc_id IN '+str(tuple(dbQuery)),conn)

api.add_resource(SearchResource, "/search" )




if __name__=="__main__":
    app.run(debug=True)

