from flask import Flask, redirect
from flask_restful import Api
from flasgger import Swagger
from api.resources import BookListResource, BookResource

app = Flask(__name__)
api = Api(app)

openapi_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, config=openapi_config, template={
    "info": {
        "title": "Library API (Flask-RESTful)",
        "version": "1.0.0"
    }
})

api.add_resource(BookListResource, '/books/')
api.add_resource(BookResource, '/books/<string:book_id>')

@app.route('/')
def root():
    return redirect('/docs/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
