import math
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


print("Loading JSON")
with open('InvIndex.json') as infile:
    data = json.load(infile)
print("JSon loaded")   
 
app = Flask(__name__)
api = Api(app)

# =============================================================================
# print("Loading JSON")
# with open('InvIndex.json') as infile:
#     data = json.load(infile)
# print("JSon loaded")    
# =============================================================================
    
#=============================================================================
conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-97U22LI;DATABASE=CZ4034;UID=sa;PWD=password1')
cursor = conn.cursor()
#=============================================================================

stop_words = set(stopwords.words("english"))
lem = WordNetLemmatizer()

class SearchResource(Resource):    
    def __init__(self):
        self.InvIndex = defaultdict(set, data)
        self.words = pd.Series(list(self.InvIndex.keys()))
        self.company_ticker = {"baba":"alibaba",
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
        
        # CHANGE PARAM WHEN MORE SCRAPED!
        self.num_docs = 1000000
        
    ################# API FUNCTIONS #######################
        
    def get(self):
        query = request.args.get('query')
# =============================================================================
#         try:
#             exact = request.args.get('exact')
#         except:
#             exact = False
#         try:
#             filter_on = request.args.get('filter_on')
#         except:
#             filter_on = False
# =============================================================================
        
        matched_index = self.search(query)
        
        data1 = self.queryDB('db123',matched_index)
        x = pd.DataFrame(data = data1)
        x['Date'] = x['Date'].dt.strftime('%Y-%m-%d')
        x.drop(columns = ['Doc_id','Name'], inplace = True)
        x['Time'] = x["Time"].str.replace(r'Z','')
        x['json'] = x.apply(lambda x : x.to_json(), axis=1)
        xlist = x['json'].to_list()
        jsonFunc = lambda m : json.loads(m)
        jsonRes = list(map(jsonFunc, xlist))        
        return jsonRes;
    
    def post(self):
        return {"data": "posted!"}
    
    ################# QUERY SEARCH #######################
    
    def clean_query(self, query, exact):
        query_clean = []
        
        query_split = word_tokenize(query)
        
        for query_word in query_split:
            word_lower = query_word.lower()
            if word_lower not in stop_words:
                cur = lem.lemmatize(word_lower)
                
                if cur in self.company_ticker:
                    cur = self.company_ticker[cur]
                    
                if not exact:
                    cur = self.JDreco(cur)
                
                if (cur not in query_clean):
                    query_clean.append(cur)
                    
        return query_clean
    
    def search(self, query, exact = False, filter_on = False, filter_amt = 500):
        matched_documents = None
        
        # (1) Clean Query:
        query_clean = self.clean_query(query, exact)
        print("Recommended Query List:")
        print(query_clean)
        
        
        # (2) Find All Docs (match any one word in query):
        for word in query_clean:
            if word in self.InvIndex:
                matches = self.InvIndex[word]
                match_index = list(matches.keys())
            else:
                print("No Matches for Word: "+word)
                continue
    
            if matched_documents is None:
                matched_documents = match_index
            else:
                #matched_documents = list(set.intersection(set(matched_documents),set(match_index)))
                matched_documents = list(set.union(set(matched_documents),set(match_index)))
                
                
        # (3) Filter Most Relevant:
        if filter_on:
            weights = self.tf_idf(query_clean)
            
            doc_score = {}
            
            for docID in matched_documents:
                doc_score[docID] = self.calc_match_score(weights, docID)
                
            matched_documents = sorted(doc_score, key=doc_score.get, reverse = True)
            
            if (filter_amt <= len(matched_documents)):
                matched_documents = matched_documents[:filter_amt]
        
        # (4) Return Results:
        return matched_documents
    
    ################# RECOMMENDATION #######################

    def jaccard(self,entry, gram_number):
        spellings = self.words[self.words.str.startswith(entry[0])]
        distances = ((jaccard_distance(set(ngrams(entry,gram_number)),
                                           set(ngrams(word,gram_number))), word)
                     for word in spellings)
        closest = min(distances)
        return closest[1]
    
    
    def JDreco(self,entry):
        return self.jaccard(entry, 2)
    
    ################# TF.IDF #######################
    
    def tf_idf(self,query):
        weights = {}
        
        for word in query:
            
            # Find IDF value
            if (word in self.InvIndex):
                idf_value = self.idf(self.InvIndex[word])
            else:
                idf_value = 0
                
            # Find TF Value
            tf_value = 1/len(query)
            
            # Store TF.IDF
            weights[word] = tf_value * idf_value
        return weights
            
    
    def idf(self,word_dict):
        value = self.num_docs/len(word_dict)
        return math.log(value, 10)
    
    ################# FILTER MOST RELEVANT #######################
    
    def calc_match_score(self, weights_query, docID):
        
        result = 0
        
        for word in weights_query:

            #QUERY
            query_score = weights_query[word]
            
            #DOC
            try:
                doc_score = float(self.InvIndex[word][docID]['tf.idf'])
            except:
                doc_score = 0
            
            #PRODUCT
            result += query_score * doc_score
            
        return result
    
    ################# INVERTED INDEX #######################
    
    def getInvIndex(self):
        print("Loading JSON 2")
        with open('InvIndex.json') as infile:
            data = json.load(infile)
        print("Json Loaded 2")
        return data
    
    ################# DATABASE CONNECTION & QUERY #######################

    def queryDB(self,table, dbQuery):
        return pd.read_sql_query('SELECT TOP 2 * FROM CZ4034.dbo.'+table+' where Doc_id IN '+str(tuple(dbQuery)) + ' ',conn)

api.add_resource(SearchResource, "/search" )




if __name__=="__main__":
# =============================================================================
#     print("Loading JSON")
#     with open('InvIndex.json') as infile:
#         data = json.load(infile)
#     print("JSon loaded")  
# =============================================================================
    
    app.run(debug=True)

