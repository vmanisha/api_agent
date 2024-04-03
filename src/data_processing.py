import re
import argparse as ap
import pandas as pd
from openapi_schema_pydantic import OpenAPI
import requests
import json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, helpers
import boto3
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


class APISpecIndex():

    opensearch_client = None
    index_name = None

    def __init__(self, host_url, index_name):
        host = host_url
        #'qia3iowywamezen9p0mk.us-east-1.aoss.amazonaws.com' # cluster endpoint, for example: my-test-domain.us-east-1.aoss.amazonaws.com
        region = 'us-east-1'
        service = 'aoss'
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, region, service)

        # create an opensearch client and use the request-signer
        self.opensearch_client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_maxsize=20,
        )
        self.index_name = index_name
        try:
            # if index does not exist
            self.create_index({'function_embedding': 768})
        except Exception as ex:
            print(ex)


    def create_index(self, fields_with_dimensions):
        properties = {}
        for field, dimension in fields_with_dimensions.items():
            properties[field]={'type':'knn_vector', 'dimension': dimension}
        
        create_response = self.opensearch_client.indices.create(self.index_name, 
            body={
                "settings":{
                    "index.knn": True,
                    'index': {
                      'number_of_shards': 1
                    }    
                },
                "mappings":{
                    "properties": properties
                }
            }               
        )
        print('\nCreating index:')
        print(create_response)
        return create_response

    def get_api_from_link(self, link):
        response = requests.get(link)
        #print(response.text)
        open_api = OpenAPI.parse_obj(json.loads(response.text))
        return open_api


    def search_index(self, search_query, embedding_model):
        query_emb = embedding_model.encode(search_query)
        search_embed_query = {
            "query": {
                "knn": {
                    "function_embedding": {
                        "vector": query_emb, 
                        "k": 5
                    }
                    
                }
            }
        }
    
        sresults = self.opensearch_client.search(index=self.index_name, 
            body=search_embed_query)
        results = []
        
        print("Retrieved total ", len(sresults["hits"]["hits"]), "results")
        for hit in sresults["hits"]["hits"]:
            print('function name', hit['_source']['function_name'])
            results.append({'Function name': hit['_source']['function_name'], \
                'Description': hit['_source']['short_description'], \
                'API Doc': hit['_source']['raw_json']})
        
        return results


    def index_documents(self, open_api_obj, embedding_model):

        documents = []
        get_post_obj = None
        parameter_names=None
        
        for key in open_api_obj.paths.keys():
            
            get_post_obj= None
            if open_api_obj.paths[key].get:
                get_post_obj = open_api_obj.paths[key].get
            elif open_api_obj.paths[key].post:
                get_post_obj = open_api_obj.paths[key].post
            elif open_api_obj.paths[key].delete:
                get_post_obj = open_api_obj.paths[key].delete

            if get_post_obj:
                func_description = "Function name is "+key

                if get_post_obj.description:
                    desc = get_post_obj.description
                    func_description += ' You can '+ desc.lower().strip()

                parameter_names = []
                if get_post_obj.parameters:
                    for entry in get_post_obj.parameters:
                        if entry.description:
                            parameter_names.append(entry.name + ' ('+entry.description.replace('\n',' ')+')')
                        else:
                            parameter_names.append(entry.name)

                if len(parameter_names) > 0:
                    func_description += ' It has parameters '+ ', '.join(parameter_names)

                function_embedding  = embedding_model.encode(func_description, normalize_embeddings=True)

                document = {'function_name':key, 
                             'short_description':desc,
                             'full_description':func_description,
                             'function_embedding': function_embedding,
                             'raw_json': open_api_obj.paths[key].json(by_alias=True, exclude_none=True, indent=2),
                                "_index": self.index_name}

                documents.append(document)
            else:
                print('Cannot index ', key, open_api_obj.paths[key])

        helpers.bulk(self.opensearch_client, documents)


def main():
    parser = ap.ArgumentParser('Run dataprocessing from a list of links')
    parser.add_argument('-i', '--index_name',required=True, help='Index to store crawled data.')
    parser.add_argument('-f', '--fields',required=True, help='Fields to index')
    parser.add_argument('-l', '--file_with_links',required=True, help='Links to crawl. CSV with column "urls"')
    
    args = parser.parse_args()

    # initialize the processor
    specs_processor = APISpecIndex('qia3iowywamezen9p0mk.us-east-1.aoss.amazonaws.com', args.index_name)
    embedding_model = SentenceTransformer("BAAI/bge-base-en-v1.5")

    links_frame = pd.read_csv(args.file_with_links)
    for entry in links_frame['urls'].drop_duplicates():
        open_api_object = specs_processor.get_api_from_link(entry)
        specs_processor.index_documents(open_api_object, embedding_model)
        print('Indexed ', entry)

    # Finished indexing apis.
    print('Finished processing all APIs')


if __name__ == '__main__':
    main()