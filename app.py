from flask import Flask, request, jsonify
import subprocess
import os
import requests
import tempfile
import uuid

app = Flask(__name__)

@app.route('/render', methods=['POST'])
def render():
    data = request.json
    images = data.get('images', [])
    texts = data.get('texts', [])
    
    tmp = tempfile.mkdtemp()
    output = f"/tmp/{uuid.uuid4()}.mp4"
    
    inputs = []
    for i, img_url in enumerate(images):
        img_path = f"{tmp}/img_{i}.jpg"
        r = requests.get(img_url)
        with open(img_path, 'wb') as f:
            f.write(r.content)
        inputs.extend(['-loop', '1', '-t', '7', '-i', img_path])
    
    filter_parts = []
    for i in range(len(images)):
        text = texts[i] if i < len(texts) else ''
        text = text.replace("'", "\\'").replace(":", "\\:")
        filter_parts.append(
            f'[{i}:v]scale=1080:1920,setsar=1,drawtext=text=\'{text}\':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=h-200:box=1:boxcolor=black@0.5:boxborderw=10[v{i}]'
        )
    
    concat_inputs = ''.join([f'[v{i}]' for i in range(len(images))])
    filter_parts.append(f'{concat_inputs}concat=n={len(images)}:v=1:a=0[out]')
    
    filter_complex = ';'.join(filter_parts)
    
    cmd = ['ffmpeg', '-y']
    cmd.extend(inputs)
    cmd.extend(['-filter_complex', filter_complex, '-map', '[out]', '-c:v', 'libx264', output])
    
    subprocess.run(cmd, check=True)
    
    with open(output, 'rb') as f:
        video_data = f.read()
    
    return jsonify({'url': output, 'size': len(video_data)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
