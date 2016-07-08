from nighthawk.triageapi.dataendpoint.common import CommonAttributes
import search_queries
import elasticsearch
from elasticsearch_dsl import Search, Q, A
import requests
from requests import ConnectionError
import json
import time
import stack_queries

class StackES(CommonAttributes):
	def __init__(self):
		CommonAttributes.__init__(self)

	def BuildRootTree(self):
		s = Search()
		t = Q('has_parent', type='hostname', query=Q('query_string', query="*"))
		aggs = A('terms', field='AuditType.Generator', size=16)

		s.aggs.bucket('datatypes', aggs)
		query = s.query(t)

		try:
			r = requests.post(self.es_host + self.es_port + self.index + self.type_audit_type + '/_search', data=json.dumps(query.to_dict()))
		except ConnectionError as e:
			ret = {"connection_error": e.args[0]}
			return ret

		data = [{
			"id": "stackable", "parent": "#", "text": "Stackable Data"
		}]

		i = ['w32services', 'w32tasks', 'w32scripting-persistence', 'w32prefetch', 'w32network-dns']

		for x in r.json()['aggregations']['datatypes']['buckets']:
			if x['key'] not in i:
				pass
			else:
				data.append({
					"id" : x['key'], "parent": "stackable", "text": x['key'], "children": True
				})

		return data

	def BuildAuditAggs(self, child_id):
		s = Search()
		s = s[0]
		t = Q('has_parent', type='hostname', query=Q('query_string', query='*'))
		aggs = A('terms', field='ComputerName.raw', size=0)


		s.aggs.bucket('endpoints', aggs)
		query = s.query(t).filter('term', AuditType__Generator=child_id)

		try:
			r = requests.post(self.es_host + self.es_port + self.index + self.type_audit_type + '/_search', data=json.dumps(query.to_dict()))
		except ConnectionError as e:
			ret = {"connection_error": e.args[0]}
			return ret

		data = []

		for x in r.json()['aggregations']['endpoints']['buckets']:
			data.append({
				"id": x['key'].upper(), "parent": child_id, "text": x['key'].upper(), "a_attr": {"href": "#" + x['key'].upper() + "/" + child_id}
			})

		return data

	def GetAuditData(self, stack_data):
		query = stack_queries.GetAuditGenerator(stack_data)

		try:
			r = requests.post(self.es_host + self.es_port + self.index + self.type_audit_type + '/_search', data=json.dumps(query))
		except ConnectionError as e:
			ret = {"connection_error": e.args[0]}
			return ret
		
		for k, v in stack_data.iteritems():
			audittype = k
			endpoints = len(v)

		data = []

		for x in r.json()['aggregations']['generator']['buckets']:
			data.append({
					"attribute": x['key'], "endpoints": [y['key'].upper() for y in x['endpoint']['buckets']], "count": x['doc_count'], "audittype": audittype
				})

		return data

