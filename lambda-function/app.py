import json
import traceback
import boto3
from dataclasses import dataclass
import os

header_github_event = "X-GitHub-Event"

def response_proxy(data):
	'''
	For HTTP status codes, you can take a look at https://httpstatuses.com/
	'''
	response = {}
	response["isBase64Encoded"] = False
	response["statusCode"] = data["statusCode"]
	response["headers"] = {}
	if "headers" in data:
		response["headers"] = data["headers"]
	response["body"] = json.dumps(data["body"])
	return response

def request_proxy(data):
	try:
		request = {}
		request = data
		if data["body"]:
			request["body"]=json.loads(data["body"])
		return request
	except Exception as e:
		traceback.print_exc()

def config_init():
	projectName=os.getenv("codebuild_projectName")
	sourceVersion=os.getenv("codebuild_version")
	if not projectName and not sourceVersion:
		return False
	return True


def handler(event, context):
	response = {}
	try:
		request = request_proxy(event)
		print(request)
		response["statusCode"]=200
		response["headers"]={}
		data = {}
		if not config_init:
			data["message"] = "Configuration check failed. Please check your configuration."
			response["statusCode"] = 500
		
		if header_github_event in request["headers"]:
			if request["headers"][header_github_event] == "ping":
				data["message"]="pong"
			elif request["headers"][header_github_event] == "push":
				if request["body"]["ref"]=='refs/heads/dev':
					trigger_build("dev")
					data["message"] = 'Building signalled : dev'
				elif request["body"]["ref"]=='refs/heads/master':
					trigger_build("master")
					data["message"] = 'Building signalled : master'
				else:
					data["message"] = "skipped"
		response["body"]=data
	except Exception as e:
		traceback.print_exc()
		response["statusCode"]=500
		response["body"]={}		
	finally:	
		return response_proxy(response)

def trigger_build(source_version):
    client = boto3.client('codebuild')
    response = client.start_build(
		projectName=os.getenv("codebuild_projectName"),
		sourceVersion=source_version
	)
    print(response)