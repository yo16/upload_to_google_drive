from flask import Flask, render_template, redirect, url_for, request
import glob
import os
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account
import mimetypes
import datetime


API_SERVICE_NAME = "drive"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/drive"]

TMP_DIR = './work'


app = Flask(__name__)

@app.route('/')
def top_page():
    # ローカルのworkにある古いファイルをたまに消す
    rm_old_files()
    
    return render_template('default.html')


def rm_old_files():
    # 今の時刻
    now = datetime.datetime.now().timestamp()
    # 削除対象の時間（秒）
    del_time = 60*60    # 1時間
    
    # 削除対象を見つける
    del_list = []
    for f in glob.glob(f'{TMP_DIR}/*'):
        # 最終更新時刻
        mtime = os.stat(f).st_mtime
        
        # 一定時間以上たっている場合は削除
        if (now-mtime)>del_time:
            del_list.append(f)
    
    # 削除
    for f in del_list:
        os.remove(f)


@app.route('/post_photo', methods=['POST'])
def post_photo():
    # サービスアカウントを使ってログイン
    obj_drive = get_authenticated_service_with_service_account()
    obj_files = obj_drive.files()
    #print('files-------')
    #print(obj_files)
    
    # https://qiita.com/ekzemplaro/items/77c0e764b277b0c84b0f
    sub_folder_name = request.form.get('dir_name')
    #print(sub_folder_name)
    
    # サブフォルダ名の存在を確認
    top_folder_id = os.environ.get('FOLDER_ID','')
    sub_folder_id = ''
    q_str = "mimeType = 'application/vnd.google-apps.folder' and " + \
        f"name = '{sub_folder_name}' and " + \
        f"parents in '{top_folder_id}'"
    sub_folder_confirm = obj_files.list(
        q=q_str,
        pageSize=10,
        fields='files(id)'
    ).execute()
    items = sub_folder_confirm.get('files',[])
    if len(items)==0:
        # ない
        # サブフォルダを作成する
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
    else:
        # ある
        sub_folder_id = items[0].get('id')
    #print(f'sub:{sub_folder_id}')
    
    # ファイルを一度ローカルに保存して、アップロードする
    photos = request.files.getlist('photos')
    
    #print(len(photos))
    #print(photos)
    os.makedirs(TMP_DIR, exist_ok=True)
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
            mimetype=mimetypes.guess_type(file_path)[0],
            resumable=True
        )
        file = obj_files.create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        #print('File ID: %s' % file.get('id'))
    
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
