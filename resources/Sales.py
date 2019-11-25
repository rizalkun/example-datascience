from flask import jsonify, render_template, make_response
from flask_restful import Resource
import pandas as pd
import numpy as np
import time
import turicreate as tc
import sqlalchemy as sql
from sklearn.model_selection import train_test_split
import json

def load_data():
        try:
            connect_string = 'mysql://root:123456@127.0.0.1:3306/example_science'
            sql_engine = sql.create_engine(connect_string)
            query = "select * from Transactions"
            return pd.read_sql_query(query, sql_engine)
        except Exception as e:
            print(e)

def model(train_data, name, user_id, item_id, target, n_rec):
    if name == 'popularity':
        model = tc.popularity_recommender.create(tc.SFrame(train_data), 
                                                    user_id=user_id, 
                                                    item_id=item_id, 
                                                    target=target)
    elif name == 'cosine':
        model = tc.item_similarity_recommender.create(train_data, 
                                                    user_id=user_id, 
                                                    item_id=item_id, 
                                                    target=target, 
                                                    similarity_type='cosine')
    elif name == 'pearson':
        model = tc.item_similarity_recommender.create(train_data, 
                                                    user_id=user_id, 
                                                    item_id=item_id, 
                                                    target=target, 
                                                    similarity_type='pearson')
        
    recom = model.recommend(k=n_rec)
    return recom

def split_data(data):
    train, test = train_test_split(data, test_size = .2)
    train_data = train
    return train_data

class Popularity(Resource):
    def get(self):
        try:
            transactions = load_data()
            data = pd.melt(transactions.set_index('customerId')['product_name'].apply(pd.Series).reset_index(),
            id_vars=['customerId'],
            value_name='product_name').groupby(['customerId', 'product_name']) \
                .agg({'product_name' : 'count'}) \
                .rename(columns={'product_name' : 'product_count'}) \
                .reset_index() \
                .sort_values(by='product_count', ascending=False)
        
            name = 'popularity'
            user_id = 'customerId'
            item_id = 'product_name'
            target = 'product_count'
            n_rec = 10 # number of items to recommend
            train_data = split_data(data)
            result = model(train_data, name, user_id, item_id, target, n_rec)
            df_result = pd.DataFrame(result)
            headers = {'Content-Type': 'text/html'}
            return make_response(render_template('view.html', tables=[df_result.to_html(classes='data', header="true")]),200,headers)
        except Exception as e:
            print(e)
            return { "success" : False, "message" : "Internal server error" }
    