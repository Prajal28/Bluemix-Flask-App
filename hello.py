from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify,make_response
import atexit
import cf_deployment_tracker
import os
import json
import time
# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

db_name = 'mydb'
client = None
db = None

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))

@app.route('/')
def home():
    return render_template('index.html')

# /* Endpoint to greet and add a new visitor to database.
# * Send a POST request to localhost:8000/api/visitors with body
# * {
# *     "name": "Bob"
# * }
# */
@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    if client:
        return jsonify(list(map(lambda doc: doc['file_name'], db)))
    else:
        print('No database')
        return jsonify([])

# /**
#  * Endpoint to get a JSON array of all the visitors in the database
#  * REST API example:
#  * <code>
#  * GET http://localhost:8000/api/visitors
#  * </code>
#  *
#  * Response:
#  * [ "Bob", "Jane" ]
#  * @return An array of all the visitor names
#  */
@app.route('/api/visitors', methods=['POST'])
def put_visitor():
    user = request.json['name']
    if client:
        data = {'name':user}
        db.create_document(data)
        return 'Hello %s! I added you to the database.' % user
    else:
        print('No database')
        return 'Hello %s!' % user

		
		
@app.route('/upload', methods=['POST'])
def upload():
    # starttime=time.time()
    file = request.files['file']
    description = request.form.get('descr') 
    createddate = request.form.get('cdate')
    title = request.form.get('title')
    creator = request.form.get('creator')
    file_t = request.form.get('file_t') 	
    file_name = file.filename
    from base64 import b64encode
    uploaded_file_content = b64encode(file.read())
    data = {'file_name': file_name, '_attachments': {file_name : {'data': uploaded_file_content}}, 'file_t':file_t,'description': description,'createddate':createddate, 'title':title, 'creator':creator}
    # t1=time.time()
    doc = db.create_document(data)
    # t2=time.time()
    # endtime=time.time()
    # servertime=(t2-t1)*100
    totaltime=(endtime-starttime)*100
    mesg='File Uploaded Successfully'
    return render_template('index.html', mesg=mesg, servertime=servertime,totaltime=totaltime)


		
#Listing of files
@app.route('/list_files', methods=['POST','GET'])
def list():
    seven_start = time.time()  
    year = (request.form.get("keyword"))
  
    count=0
    if request.method == 'GET':
        L = []
        M=[]
        desc = []
        createdate = []
        bmtime_start = time.time()
        for document in db:
            fileinfo={}
			
            descr=document['description']
            creatdate = document['createddate']
            fileinfo = document['file_name']
            filetype=document['file_t']
            if(filetype=='small'):
                count=count+1
                L.append(fileinfo)
                desc.append(descr) 
                createdate.append(creatdate)
            else:
                count=count+1
                M.append(fileinfo)
        bmtime_end = time.time()
        print L
        seven_end = time.time()
        bmtime = (bmtime_end - bmtime_start)*1000
        waittime = (seven_end - seven_start)*1000
        return render_template('list.html', L=L,count=count,M=M,desc=desc,waittime=waittime,bmtime=bmtime, creatdate=creatdate)




@app.route('/download', methods=['POST'])
def download():
	file_name = request.form.get('dname')
	for document in db:
		if (document['file_name'] == file_name):
			file = document.get_attachment(file_name, attachment_type='binary')
			response = make_response(file)
			response.headers["Content-Disposition"] = "attachment; filename=%s"%file_name
			return response
		else:
			response = 'File not found'
	return response
	
@app.route('/downloadkey', methods=['POST'])
def downloadkey():
    key = request.form.get('keyword')
    file_name=""
    for document in db:
	    descr=document['title']
		
	    if key in descr:
		
		  file_name=document['file_name']	
		  file = document.get_attachment(file_name, attachment_type='binary')
		  response = make_response(file)
		  response.headers["Content-Disposition"] = "attachment; filename=%s"%file_name
		  return response
	    else:
		  response = 'missing data'
    return response


@app.route('/delete', methods=['POST'])
def delete():
	
    file_name = request.form['deletefn']
    for document in db:
        if document['file_name'] == file_name:
            print("File found and deleted")
            res='File Found and Deleted from Cloud'
            document.delete()
            #document.delete_attachment(file_name)
            break;
        else:
            print ('File not found')
            res='File Not Found on Cloud'
    return render_template('index.html', res=res)
@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)

	
