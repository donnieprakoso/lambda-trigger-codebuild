import json
import traceback
import boto3
import os
import hmac
import hashlib

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
	github_secret=os.getenv("github_sha1_secret")
	if not projectName and not github_secret:
		return False
	return True


def handler(event, context):
	''' 
	Main handler — essentially, this function will get the raw JSON data from GitHub webhook and verify the signature using HMAC with SHA1.
	'''
	
	response = {}
	raw_body = event["body"].replace('\n', '')
	try:
		request = request_proxy(event)
		response["statusCode"]=200
		response["headers"]={}
		data = {}
		if not config_init:
			data["message"] = "Configuration check failed. Please check your configuration."
			raise Exception("Configuration check failed")

		if not ver(request["headers"]["X-Hub-Signature"], raw_body):
			data["message"] = "Request failed verification."
			raise Exception("Request failed verification.")
		
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
		response["body"]=data
	finally:	
		return response_proxy(response)

def trigger_build(source_version):
	client = boto3.client('codebuild')
	response = client.start_build(
		projectName=os.getenv("codebuild_projectName"),
		sourceVersion=source_version
	)
	print(response)
	
def ver(github_signature, payload):
	'''
	Verify the request with SHA1 and secret key defined.
	'''
	
	try:
		secret_key = os.getenv('github_sha1_secret')
		sha_name, signature = github_signature.split('=')    
		mac = hmac.new(secret_key.encode('utf-8'), msg=payload.encode('utf-8'), digestmod=hashlib.sha1)
		return hmac.compare_digest(signature, mac.hexdigest())
	except Exception as e:
		traceback.print_exc()
		return False
