import json
import traceback
import boto3
import os
import hmac
import hashlib

HEADER_GITHUB_EVENT = "X-GitHub-Event"
HEADER_GITHUB_SIGNATURE = "X-Hub-Signature"
CODEBUILD_STAGES_BUILD=json.loads(os.getenv("CODEBUILD_STAGES_BUILD"))
CODEBUILD_PROJECTNAME=os.getenv("CODEBUILD_PROJECTNAME")
GITHUB_SHA1_SECRET=os.getenv("GITHUB_SHA1_SECRET")


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
	if not CODEBUILD_PROJECTNAME and not GITHUB_SHA1_SECRET and not CODEBUILD_STAGES_BUILD:
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
		
		if not ver(request["headers"][HEADER_GITHUB_SIGNATURE], raw_body):
			data["message"] = "Request failed verification."
			raise Exception("Request failed verification.")
		
		if HEADER_GITHUB_EVENT in request["headers"]:
			if request["headers"][HEADER_GITHUB_EVENT] == "ping":
				data["message"]="pong"
			elif request["headers"][HEADER_GITHUB_EVENT] == "push":
				if request["body"]["ref"] in CODEBUILD_STAGES_BUILD:
					build_branch = CODEBUILD_STAGES_BUILD[request["body"]["ref"]]["branch"]
					build_spec = CODEBUILD_STAGES_BUILD[request["body"]["ref"]]["buildspec"]
					trigger_build(CODEBUILD_PROJECTNAME, build_branch, build_spec)
				else:
					data["message"] = "skipped"
		response["body"]=data
	except Exception as e:
		traceback.print_exc()
		response["statusCode"]=500
		response["body"]=data
	finally:	
		return response_proxy(response)

def trigger_build(project_name, source_version, buildspec):
	try:
		client = boto3.client('codebuild')
		response = client.start_build(
			projectName=project_name,
			sourceVersion=source_version,
			buildspecOverride=buildspec
		)
	except Exception as e:
		raise Exception("Build signal failed.")
	
def ver(github_signature, payload):
	'''
	Verify the request with SHA1 and secret key defined.
	'''
	
	try:
		sha_name, signature = github_signature.split('=')
		mac = hmac.new(GITHUB_SHA1_SECRET.encode('utf-8'), msg=payload.encode('utf-8'), digestmod=hashlib.sha1)
		return hmac.compare_digest(signature, mac.hexdigest())
	except Exception as e:
		traceback.print_exc()
		return False
