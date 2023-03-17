import base64
from curses import flash
from flask import Flask, redirect, request, send_from_directory, url_for
from flask.templating import render_template
from fileinput import filename
from flask_socketio import SocketIO, emit, send
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import os
from io import BytesIO
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, StringField

app = Flask(__name__)
io = SocketIO(app)


app.config['SECRET_KEY'] = 'umasenhalegal'
app.config['UPLOADED_PHOTOS_DEST'] = '/home/luisabueno/new_site/static/uploads'
app.config['UPLOAD_FOLDER'] = '/home/luisabueno/new_site/static/uploads'


photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)

class UploadForm(FlaskForm):
    photo = FileField(
        validators=[
            FileAllowed(photos, 'Apenas imagens são permitidas'),
            FileRequired('Não pode deixar o campo de imagem vazio')
        ],
    )
    title = StringField('Título', description = 'Título da imagem')
    submit = SubmitField('Upload')

messages = []


@app.route('/', methods=['POST','GET'])
def upload_image_handler():
    form = UploadForm()    
    if form.validate_on_submit():

        msg = {}

        photo = form.photo.data
        title = form.title.data
        msg['title'] = title

        filename = photos.save(photo)
        file_url = url_for('get_file_url', filename=filename)
        msg['photo'] = file_url

        messages.append(msg)

    else:
        file_url = None
        filename = None
    return render_template('chat.html', form=form, file_url=file_url, filename=filename)


#Abrir Imagem
@app.route('/uploads/<filename>')
def get_file_url(filename):
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'], filename)


@io.on('sendMessage')
def send_message_handler(data):

    msg = {}
    
    # Extrair o objeto File do evento de submissão do formulário e convertê-lo
    file_binary = data['file']
    bytes_io = BytesIO(file_binary)
    title = data['title']
    msg['title'] = title

    # Criar um objeto FileStorage a partir do objeto File
    photo = FileStorage(stream=bytes_io, filename=data['filename'], content_type=data['content_type'])

    # Salvar a foto e obter sua URL
    filename = photos.save(photo)
    file_url = url_for('get_file_url', filename=filename)
    msg['photo'] = file_url

    # Adicionar a URL à lista de mensagens
    messages.append(msg)

    # Transmitir a URL para todos os clientes conectados
    emit('getMessage', msg, broadcast=True)



@io.on('message')
def message_handler(msg):

    # envia mensagem para quem estiver ouvindo
    send(messages)

if __name__ == "__main__":
    io.run(app, debug=True)

