from flask import Flask, jsonify, request
from db import db
from Product import Product
import logging.config
from sqlalchemy import exc
from configparser import ConfigParser

logging.config.fileConfig('/config/logging.ini', disable_existing_loggers=False)

log = logging.getLogger(__name__)


def get_db_url():
    config = ConfigParser()
    config.read('/config/db.ini')
    db_conf = config['mysql']
    with open('/run/secrets/db_password') as db_password:
        password = db_password.read()
    database_url = f'mysql://{db_conf["username"]}:{password}@{db_conf["host"]}/{db_conf["database"]}'
    log.info(f'Connecting to database: {database_url}')
    return database_url


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = get_db_url()
db.init_app(app)


@app.route('/products')
def get_all_products():
    log.debug('GET /products')
    try:
        products = [product.json for product in Product.find_all()]
        return jsonify(products)
    except exc.SQLAlchemyError:
        log.exception('An exception occurred while trying to get all products')
        return 'An exception occurred while trying to get all products', 500


@app.route('/products/<int:p_id>')
def get_product(p_id: int):
    log.debug(f'GET /products/{p_id}')
    try:
        product = Product.find_by_id(p_id)
        if not product:
            log.warning(f'Get /products/{p_id}: Product not found')
            return 'Product with such id does not exist', 404

        return jsonify(product.json)
    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while retrieving product {p_id}')
        return f'An exception occurred while retrieving product {p_id}', 500


@app.route('/products', methods=['POST'])
def create_product():
    product_info = request.json
    log.debug(f'POST /products with product: {product_info}')
    new_product = Product(None, product_info['name'])

    try:
        new_product.save_to_db()
        return jsonify(new_product.json), 201
    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while creating product with name {product_info["name"]}')
        return f'An exception occurred while creating product with name {product_info["name"]}', 500


@app.route('/products/<int:p_id>', methods=['PUT'])
def update_product(p_id: int):
    log.debug(f'PUT /products/{p_id}')
    try:
        existing_product = Product.find_by_id(p_id)

        if existing_product:
            product_info = request.json

            existing_product.name = product_info['name']
            existing_product.save_to_db()

            return jsonify(existing_product.json), 200

        log.warning(f'PUT /products/{p_id}: Product not found')
        return 'Product with such id does not exist', 404
    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while updating product {p_id}')
        return f'An exception occurred while updating product {p_id}', 500


@app.route('/products/<int:p_id>', methods=['DELETE'])
def delete_product(p_id: int):
    log.debug(f'DELETE /products/{p_id}')
    try:
        product = Product.find_by_id(p_id)
        if product:
            product.delete_from_db()
            return 'Product removed', 204

        log.warning(f'PUT /products/{p_id}: Product not found')
        return 'Product with such id does not exist', 404
    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while deleting product {p_id}')
        return f'An exception occurred while deleting product {p_id}', 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
