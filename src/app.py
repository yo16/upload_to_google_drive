from flask import Flask, render_template, redirect, url_for, request
import os
from googleapiclient.http import MediaFileUpload
#import googleapiclient
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account


API_SERVICE_NAME = "drive"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/drive"]

TMP_DIR = './work'


app = Flask(__name__)

@app.route('/')
def top_page():
    return render_template('default.html')


@app.route('/post_photo', methods=['POST'])
def post_photo():
    # サービスアカウントを使ってログイン
    obj_drive = get_authenticated_service_with_service_account()
    obj_files = obj_drive.files()
    #print('files-------')
    #print(obj_files)
    
    # https://qiita.com/ekzemplaro/items/77c0e764b277b0c84b0f
    sub_folder_name = request.form.get('dir_name')
    print(sub_folder_name)
    # サブフォルダを作成する
    top_folder_id = os.environ.get('FOLDER_ID','')
    sub_folder_meta = {
        'name': sub_folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [top_folder_id]
    }
    sub_folder = obj_files.create(
        body=sub_folder_meta,
        fields='id'
    ).execute()
    sub_folder_id = sub_folder.get('id')
    print(f'sub:{sub_folder_id}')
    
    # ファイルを一度ローカルに保存して、アップロードする
    photos = request.files.getlist('photos')
    
    #print(len(photos))
    #print(photos)
    for p in photos:
        #print(p.filename)
        file_path = f'{TMP_DIR}/{p.filename}'
        p.save(file_path)
        
        file_metadata = {
            'name': p.filename,
            'parents': [sub_folder_id]
        }
        media = MediaFileUpload(
            file_path,
            mimetype='image/jpeg',
            resumable=True
        )
        file = obj_files.create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print('File ID: %s' % file.get('id'))
    
    # 
    
    return redirect(url_for('top_page'))


def get_authenticated_service_with_service_account():
    service_account_key = {
        'type': 'service_account',
        'project_id': os.environ.get('PROJ_ID', ''),
        'private_key_id': os.environ.get('PRIVATE_KEY_ID', ''),
        'private_key': os.environ.get('PRIVATE_KEY', '').replace('\\n','\n'),
        'client_email': os.environ.get('CLIENT_EMAIL', ''),
        'client_id': os.environ.get('CLIENT_ID', ''),
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
        'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/google-drive-api-hiu2022spr%40analog-height-345100.iam.gserviceaccount.com'
    }
    credentials = service_account.Credentials.from_service_account_info(service_account_key)
    scoped_credentials = credentials.with_scopes(SCOPES)
    return build(API_SERVICE_NAME, API_VERSION, credentials=scoped_credentials)


if __name__=='__main__':
    app.config.from_object('config')
    app.run(debug=app.config['DEBUG'])
