import urllib
import os
from zipfile import ZipFile
import sys

gradle_version = "2.11"
gradle_path = "gradle-{0}".format(gradle_version)

def install_gradle(path, version = gradle_version):
    gradle = "gradle-{0}".format(version)
    gradleZip = "{0}-bin.zip".format(gradle)
    gradleZipPath = os.path.join(path,gradleZip)
    url = "https://services.gradle.org/distributions/{0}".format(gradleZip)
    
    print "Downloading {0}".format(gradleZip)
    urllib.urlretrieve(url, gradleZipPath, report_progress)
    
    print "Download complete!"
    print "Extracting gradle"
    with ZipFile(gradleZipPath, 'r') as archive:
        archive.extractall(path)
    print "Extraction complete!"
    os.remove(gradleZipPath)


def report_progress(block, block_size, total_size):
    percent = float(block * block_size) / total_size
    percent = int(percent*100)
    sys.stdout.write("Downloading gradle: {0}%\r".format(percent, 100))
    if percent >= 100:
        sys.stdout.write("\n")
