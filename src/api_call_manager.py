import requests

# TODO: Add check if the function name is repeatedly called, cache results.
def make_api_call(function_name, input_params, app_url):
	# create request object based on the url
	response = requests.post(app_url+function_name, json=input_params)
	if response.text:
		return response.text
	else:
		return ""

