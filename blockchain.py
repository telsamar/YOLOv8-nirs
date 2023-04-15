import json
import os
import hashlib
from pathlib import Path
import time
from PIL import Image

BLOCKCHAIN_DIR = 'blockchain/'
PHOTO_ITOG_DIR = 'images_only_face/'

def get_hash(prev_block):
    prev_block_path = os.path.join(BLOCKCHAIN_DIR, prev_block)
    with open(prev_block_path, 'rb') as f:
        content = f.read()
    return hashlib.sha256(content).hexdigest()

def check_integrity():
    files = sorted([f for f in os.listdir(BLOCKCHAIN_DIR) if not f.startswith('.')], key=lambda f: int(os.path.splitext(f)[0]))

    results = []

    for file in files[1:]:
        block_path = os.path.join(BLOCKCHAIN_DIR, file)
        with open(block_path) as f:
            block = json.load(f)

        prev_hash = block.get('prev_block').get('hash')
        prev_filename = block.get('prev_block').get('filename')

        actual_hash = get_hash(prev_filename)

        if prev_hash == actual_hash:
            res = 'Ok'
        else:
            res = 'was Changed'

        print(f'Block {int(prev_filename) + 1}: {res}')
        results.append({'block': prev_filename, 'result': res})
    return results

def write_block(photo_name, class_name):
    blocks_count = len(os.listdir(BLOCKCHAIN_DIR)) - 1
    prev_block = str(blocks_count)
    
    basename, extension = os.path.splitext(photo_name)
    filetype = {
        ".jpg": "JPEG image",
        ".png": "PNG image",
        ".gif": "GIF image",
    }.get(extension.lower(), "unknown")

    with Image.open("images_only_face/" + photo_name) as img:
        width, height = img.size
        resolution = f"{width}x{height}"

    data = {
        "name_of_photo": photo_name,
        "filetype": filetype,
        "hash_photo": get_hash_photo(photo_name),
        "size in bytes": os.path.getsize("images_only_face/" + photo_name),
        "resolution": resolution,
        "created": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime("images_only_face/" + photo_name))),
        "object on photo": class_name,
        "prev_block": {
            "hash": get_hash(prev_block),
            "filename": prev_block,
            "size in bytes": os.path.getsize("blockchain/" + prev_block)         
        }   
    }

    print("block realised")

    current_block = os.path.join(BLOCKCHAIN_DIR, str(blocks_count + 1))

    with open(current_block, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write('\n')

def get_hash_photo(photo_name):
    photo_path = os.path.join(PHOTO_ITOG_DIR, photo_name)
    with open(photo_path, 'rb') as f:
        content_photo = f.read()
    return hashlib.sha256(content_photo).hexdigest()

def main():
    Path(BLOCKCHAIN_DIR).mkdir(parents=True, exist_ok=True)
    Path(PHOTO_ITOG_DIR).mkdir(parents=True, exist_ok=True)

    folder = 'images_only_face/'
    files = sorted(os.listdir(folder), key=lambda x: os.path.getctime(os.path.join(folder, x)))
    for i, filename in enumerate(files):
        write_block(filename, class_name = "test")

    print('Blockchain is successfully written in file.')

if __name__ == '__main__':
    main()