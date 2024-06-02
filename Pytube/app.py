from flask import Flask, render_template, request, send_file, send_from_directory
from pytube import YouTube
import os
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    yt = YouTube(url)
    audio = yt.streams.filter(only_audio=True).first()
    output_path = os.path.join(os.getcwd(), 'downloads')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    audio.download(output_path=output_path, filename='audio.mp4')
    audio_path = os.path.join(output_path, 'audio.mp4')
    return render_template('convert.html', audio_path=audio_path)

@app.route('/convert', methods=['POST'])
def convert():
    audio_path = request.form['audio_path']
    format = request.form['audio_format']
    rename = request.form['rename']
    noise_level = request.form['noise_level']
    speed = request.form['speed']
    output_file = os.path.join('downloads', f'{rename}.{format}')

    temp_with_noise = os.path.join('downloads', 'temp_with_noise.wav')
    noise_cmd = ["ffmpeg", "-y", "-i", audio_path, "-filter_complex", f"volume={noise_level}dB", temp_with_noise]
    subprocess.run(noise_cmd, check=True)

    cmd_convert = [
        "ffmpeg", "-y", "-i", temp_with_noise, "-filter:a", f"atempo={speed}", "-vn", "-ar", "44100", "-ac", "2",
        "-b:a", "128k", output_file
    ]
    subprocess.run(cmd_convert, check=True)

    if not os.path.exists(output_file):
        return "Error: Converted file not found."

    return send_file(output_file, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['audio_file']
    format = request.form['audio_format']
    rename = request.form['rename']
    noise_level = request.form['noise_level']
    speed = request.form['speed']
    input_path = os.path.join('uploads', file.filename)
    output_file = os.path.join('downloads', f'{rename}.{format}')
    
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    file.save(input_path)

    temp_with_noise = os.path.join('downloads', 'temp_with_noise.wav')
    noise_cmd = ["ffmpeg", "-y", "-i", input_path, "-filter_complex", f"volume={noise_level}dB", temp_with_noise]
    subprocess.run(noise_cmd, check=True)

    cmd_convert = [
        "ffmpeg", "-y", "-i", temp_with_noise, "-filter:a", f"atempo={speed}", "-vn", "-ar", "44100", "-ac", "2",
        "-b:a", "128k", output_file
    ]
    subprocess.run(cmd_convert, check=True)

    if not os.path.exists(output_file):
        return "Error: Converted file not found."

    return send_file(output_file, as_attachment=True)

@app.route('/preview', methods=['POST'])
def preview():
    if 'audio_file' in request.files:
        file = request.files['audio_file']
        input_path = os.path.join('uploads', 'preview_' + file.filename)
        file.save(input_path)
    else:
        audio_path = request.form['audio_path']
        input_path = os.path.join('downloads', 'audio.mp4') if audio_path == '' else audio_path

    noise_level = request.form['noise_level']
    speed = request.form['speed']
    pitch = request.form['pitch'] if 'pitch' in request.form else '1.0'  # Novo: obtém o valor do controle de pitch
    preview_file = os.path.join('downloads', 'preview_with_effects.wav')

    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    temp_with_noise = os.path.join('downloads', 'temp_preview_with_noise.wav')
    noise_cmd = ["ffmpeg", "-y", "-i", input_path, "-filter_complex", f"volume={noise_level}dB", temp_with_noise]
    subprocess.run(noise_cmd, check=True)

    # Modificado: Adiciona o filtro de alteração de tom (pitch)
    cmd_preview = [
        "ffmpeg", "-y", "-i", temp_with_noise, "-filter_complex",
        f"volume={noise_level}dB, atempo={speed}, asetrate=44100*{pitch}",
        "-vn", "-ar", "44100", "-ac", "2", "-b:a", "128k", preview_file
    ]
    subprocess.run(cmd_preview, check=True)

    if not os.path.exists(preview_file):
        return "Error: Preview file not found."

    return send_file(preview_file, as_attachment=False)

if __name__ == '__main__':
    app.run(debug=True)
