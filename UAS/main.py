
from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import Barang as ModelBarang
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'price': 4, 'quality': 3, 'durability': 4, 'weight': 6, 'size': 3}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(ModelBarang.id_barang, ModelBarang.product_name, ModelBarang.price, ModelBarang.quality, ModelBarang.durability, ModelBarang.weight, ModelBarang.size)
        result = session.execute(query).fetchall()
        print(result)
        return [{'id_barang': barang.id_barang, 'product_name': barang.product_name, 'price': barang.price, 'quality': barang.quality, 'durability': barang.durability, 'weight': barang.weight, 'size': barang.size} for barang in result]
    
    @property
    def normalized_data(self):
        price_values = []
        quality_values = []
        durability_values = []
        weight_values = []
        size_values = []

        for data in self.data:
            price_values.append(data['price'])
            quality_values.append(data['quality'])
            durability_values.append(data['durability'])
            weight_values.append(data['weight'])
            size_values.append(data['size'])

        return [
            {'id_barang': data['id_barang'],
             'price': min(price_values) / data['price'],
             'quality': data['quality'] / max(quality_values),
             'durability': data['durability'] / max(durability_values),
             'weight': data['weight'] / max(weight_values),
             'size': data['size'] / max(size_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = []

        for row in normalized_data:
            product_score = (
                row['price'] ** self.raw_weight['price'] *
                row['quality'] ** self.raw_weight['quality'] *
                row['durability'] ** self.raw_weight['durability'] *
                row['weight'] ** self.raw_weight['weight'] *
                row['size'] ** self.raw_weight['size']
            )

            produk.append({
                'id_barang': row['id_barang'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'id_barang': product['id_barang'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['id_barang']:
                  round(row['price'] * weight['price'] +
                        row['quality'] * weight['quality'] +
                        row['durability'] * weight['durability'] +
                        row['weight'] * weight['weight'] +
                        row['size'] * weight['size'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class Barang(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(ModelBarang)
        data = [{'id_barang': barang.id_barang, 'price': barang.price, 'quality': barang.quality, 'durability': barang.durability, 'weight': barang.weight, 'size': barang.size} for barang in session.scalars(query)]
        return self.get_paginated_result('barang/', data, request.args), HTTPStatus.OK.value


api.add_resource(Barang, '/barang')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)
