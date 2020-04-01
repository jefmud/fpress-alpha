import os
import zipfile

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

class Zipper:
    dir = './uploads'
    def __init__(self, dir):
        self.dir = dir
        
    def save(self, filename):
        zipf = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)
        zipdir(self.dir, zipf)
        zipf.close()
        

if __name__ == '__main__':
    # test the class, save uploads folder to local
    test = Zipper('./uploads')
    test.save('uploads.zip')