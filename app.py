from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from databases.redis_db import RedisConn
import json

app = Flask(__name__)
api = Api(app)
redis = RedisConn()


class GetAllCards(Resource):
    def get(self) -> list:
        cards = json.loads(redis.get("ff-tcg-cards")).get("cards")
        return jsonify(cards)


class GetCard(Resource):
    def get(self):
        card_id = request.args.get('id')
        card = json.loads(redis.get('ff-tcg-cards')).get(card_id)
        if card:
            return jsonify(card)
        return {"message": "Card not found"}, 404


class GetCardIntents(Resource):
    def get(self):
        card_id = request.args.get('id')
        card = redis.get(card_id)
        if card:
            return jsonify(card['intents'])
        return {"message": "Card not found"}, 404


class GetCardDescription(Resource):
    def get(self):
        card_id = request.args.get('id')
        card = redis.get(card_id)
        if card:
            return jsonify(card['text'])
        return {"message": "Card not found"}, 404


api.add_resource(GetAllCards, "/cards")
api.add_resource(GetCard, "/card")
api.add_resource(GetCardIntents, "/card/intents")
api.add_resource(GetCardDescription, "/card/description")

if __name__ == "__main__":
    app.run(debug=True)