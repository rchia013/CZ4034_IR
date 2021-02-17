import requests
from flask import Flask
from flask_restful import Api, Resource
from flask import request

app = Flask(__name__)
api = Api(app)

class SearchResource(Resource):    
    def get(self):
        query = request.args.get('query')
        return {"content": query}
    
    def post(self):
        return {"data": "posted!"}

api.add_resource(SearchResource, "/search" )

if __name__=="__main__":
    app.run(debug=True)
