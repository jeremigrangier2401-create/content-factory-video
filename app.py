from flask import Flask, request, jsonify
import subprocess
import os
import requests
import tempfile
import uuid

app = Flask(__name__)

@app.route('/render', methods=['POST'])
def render():
    try:
        data = request.get_json(force=True)
        images = data.get('images', [])
        
        tmp = tempfile.mkdtemp()
        output_path = f"/tmp/{uuid.uuid4()}.mp4"
        
        input_files = []
        for i, img_url in enumerate(images):
            img_path = os.path.join(tmp, f"img_{i}.jpg")
            r = requests.get(img_url, timeout=30)
            with open(img_path, 'wb') as f:
                f.write(r.content)
            input_files.append(img_path)
        
        inputs = []
        for img_path in input_files:
            inputs.extend(['-loop', '1', '-t', '7', '-i', img_path])
        
        n = len(input_files)
        filter_str = ''.join([f'[{i}:v]scale=1080:1920,setsar=1[v{i}];' for i in range(n)])
        concat_str = ''.join([f'[v{i}]' for i in range(n)])
        filter_str += f'{concat_str}concat=n={n}:v=1:a=0[out]'
        
        cmd = ['ffmpeg', '-y'] + inputs + ['-filter_complex', filter_str, '-map', '[out]', '-c:v', 'libx264', '-t', str(n*7), output_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            return jsonify({'error': result.stderr}), 500
        
        return jsonify({'url': output_path, 'status': 'done'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
