import requests

def get_request(url, params=None, headers=None):
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()  # Assuming the response is in JSON format
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# Test1: Tested get_request() function ok
# url = 'http://localhost:3001/api/v1/workspace/test/chats'
# headers = {'Authorization': 'Bearer MMFN0KA-2KC4PGB-M4QNPJW-Y7XYXY7', 'Accept': 'application/json'}
# response_data = get_request(url=url, headers=headers)
# if response_data:
#     print(response_data)
#Result
#{'history': [{'role': 'user', 'content': 'Give me a summary of all the available documents.', 'sentAt': 1721109914, 'chatId': 39}, {'type': 'chat', 'role': 'assistant', 'content': 'I apologize, but there is no conversation or context provided about specific documents. It seems that you may have started a question without providing any relevant information. If you could provide more context or clarify what type of documents you are referring to, I would be happy to try and assist you in summarizing them.', 'sources': [], 'chatId': 39, 'sentAt': 1721109914, 'feedbackScore': None}, {'role': 'user', 'content': 'What file is available in this workspace?', 'sentAt': 1721109988, 'chatId': 40}, {'type': 'chat', 'role': 'assistant', 'content': "I apologize, but it seems that we haven't started working on any files or projects together. This conversation just began, and there are no files or documents available in this workspace. If you'd like to start working on a project or share some files with me, I'm here to help!", 'sources': [], 'chatId': 40, 'sentAt': 1721109988, 'feedbackScore': None}, {'role': 'user', 'content': 'what is the email about?', 'sentAt': 1721110081, 'chatId': 41}, {'type': 'chat', 'role': 'assistant', 'content': "Based on the provided context, it appears that the email thread is about a declaration of beneficiaries and a procuration from the legal representative in France (Pierre Dupal) for Krakatoa. The main points discussed are:\n\n* A reminder to Pierre to sign a mandate allowing Maupard to proceed with the declaration.\n* Pierre's confirmation that he has no basis to reply, as he is not a shareholder, indirect beneficiary, administrator, or employee of the company and does not have any job description indicating an active operational role in the company.\n* Oudema (a clerk at Maupard Fiduciaire) explaining that Pierre's position as legal representative in France requires his signature for the declaration.", 'sources': [{'id': '28bd8ebe-74ef-473e-a59f-a8ae82550460', 'url': 'file://C:\\Users\\chawc\\AppData\\Roaming\\anythingllm-desktop\\storage\\hotdir\\20190413-email-thread-Maupard-PD-Krakatoa_translation.pdf', 'title': '20190413-email-thread-Maupard-PD-Krakatoa_translation.pdf', 'docAuthor': 'no author found', 'description': 'email-from-PD1.txt - Notepad', 'docSource': 'pdf file uploaded by the user.', 'chunkSource': 'localfile://D:\\TPProjects\\Legal\\1001126 Krakatoa\\Documents\\PD\\20190413-email-thread-Maupard-PD-Krakatoa_translation.pdf', 'published': '7/16/2024, 2:03:58 PM', 'wordCount': 386, 'token_count_estimate': 559, 'text': '<document_metadata>\nsourceDocument: 20190413-email-thread-Maupard-PD-Krakatoa_translation.pdf\npublished: 7/16/2024, 2:03:58 PM\n</document_metadata>\n\n1/ In an email dated 13 April 2018, Maupard sent a reminder to Pierre about the \nmandate previously sent for him to sign instructing Maupard to proceed with the \ndeclaration.\n2/ AV replied to 1.\n"\nDear Deborah, Oumema, Patrick [note: i.e. Maupard and clercs]\nI am following up on the issue of the declaration of beneficiaries which has been \nleft unresolved since last year.\nYou then requested a procuration from the legal representative in France (cf your \nemail below) to be able to proceed with the declaration. \nI just spoke with Mr Pierre Dupal, the legal responsible in France of Krakatoa, who \nwill contact you soon to do the necessary regarding this issue. \nPlease keep us informed regarding any progress and do not hesitate to let us know if\nyou need anything.\n"\n3/ Then PD replied to 1.\n"\nIf I am the intended recipient of the email below  our email), it is', '_distance': 0.7430442571640015, 'score': 0.25695574283599854}], 'chatId': 43, 'sentAt': 1721113962, 'feedbackScore': None}]}


def post_request(url, data, headers=None):
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()  # Assuming the response is in JSON format
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# Test2:  Tested post_request() function ok
# url = 'http://localhost:3001/api/v1/workspace/krakatoa/chat'
# data = {'message': 'What is the email about', 'mode': 'query'}
# headers = {'Authorization': 'Bearer MMFN0KA-2KC4PGB-M4QNPJW-Y7XYXY7', 'Accept': 'application/json', 'Content-Type': 'application/json'}
# response_data = post_request(url, data, headers)
#
# if response_data:
#     print(response_data)
#Result:
#{'id': '9c9ec1ba-5788-4833-9721-80a2b66225b9', 'type': 'textResponse', 'close': True, 'error': None, 'chatId': 43, 'textResponse': "The email is about a declaration of beneficiaries for Krakatoa, and Pierre Dupal's role as the legal representative in France. The main point is that Pierre needs to sign a mandate allowing Maupard to proceed with the declaration.", 'sources': [{'id': '28bd8ebe-74ef-473e-a59f-a8ae82550460', 'url': 'file://C:\\Users\\chawc\\AppData\\Roaming\\anythingllm-desktop\\storage\\hotdir\\20190413-email-thread-Maupard-PD-Krakatoa_translation.pdf', 'title': '20190413-email-thread-Maupard-PD-Krakatoa_translation.pdf', 'docAuthor': 'no author found', 'description': 'email-from-PD1.txt - Notepad', 'docSource': 'pdf file uploaded by the user.', 'chunkSource': 'localfile://D:\\TPProjects\\Legal\\1001126 Krakatoa\\Documents\\PD\\20190413-email-thread-Maupard-PD-Krakatoa_translation.pdf', 'published': '7/16/2024, 2:03:58 PM', 'wordCount': 386, 'token_count_estimate': 559, 'text': '<document_metadata>\nsourceDocument: 20190413-email-thread-Maupard-PD-Krakatoa_translation.pdf\npublished: 7/16/2024, 2:03:58 PM\n</document_metadata>\n\n1/ In an email dated 13 April 2018, Maupard sent a reminder to Pierre about the \nmandate previously sent for him to sign instructing Maupard to proceed with the \ndeclaration.\n2/ AV replied to 1.\n"\nDear Deborah, Oumema, Patrick [note: i.e. Maupard and clercs]\nI am following up on the issue of the declaration of beneficiaries which has been \nleft unresolved since last year.\nYou then requested a procuration from the legal representative in France (cf your \nemail below)  it is', '_distance': 0.7430442571640015, 'score': 0.25695574283599854}]}

