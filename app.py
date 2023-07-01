from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from databases.db_mongo import MongoDB


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/ff-tcg-fast-storage"
app.config["JWT_SECRET_KEY"] = "your-secret-key"
api = Api(app)
Mongo = MongoDB(app.config["MONGO_URI"], "yugioh")

class GetAllCards(Resource):
    def get(self) -> list:
        cards = Mongo.db.cards.find()

        if not cards:
            return {"message": "No cards found"}, 404

        return jsonify([card for card in cards])


class GetCard(Resource):
    def get(self):
        card_id = request.args.get('id')
        card = Mongo.find_one("cards", {"_id": card_id})
        if card:
            return jsonify(card)
        return {"message": "Card not found"}, 404


class GetCardIntents(Resource):
    def get(self):
        card_id = request.args.get('id')
        card = Mongo.find_one("cards", {"_id": card_id})
        if card:
            return jsonify(card['intents'])
        return {"message": "Card not found"}, 404

class GetCardDescription(Resource):
    def get(self):
        card_id = request.args.get('id')
        card = Mongo.find_one("cards", {"_id": card_id})
        if card:
            return jsonify(card['description'])
        return {"message": "Card not found"}, 404
