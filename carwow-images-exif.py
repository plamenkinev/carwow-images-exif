from bs4 import BeautifulSoup
from urllib.request import urlopen
import piexif
import sys

def get_image_urls(review_url):
    """Returns a list of images from a carwow review"""
    html = urlopen(review_url).read()
    soup = BeautifulSoup(html, "html.parser")
    images = soup.find_all("a", {"class": "rsImg"})

    urls = []
    for image in images:
        href = image.get('href')
        url = "http:" + href[:href.find('?')]
        urls.append(url)

    return urls

def get_image_bytes(image_url):
    """Returns an array of bytes of the image, None if response not HTTP 200"""
    connection = urlopen(image_url)
    if (connection.getcode() == 200):
        image_bytes = connection.read()
        return image_bytes
    else:
        return None

def get_exif_data(image_bytes):
    exif = piexif.load(image_bytes)
    return exif

def save_to_file(image_bytes, name):
    filename = "{}.jpg".format(name)
    if (image_bytes != None):
        with open(filename, "wb") as file:
            bytes_written = file.write(image_bytes)
            print("{} Bytes written to disk as {}.".format(bytes_written, filename))
    else:
        print("Unable to write file {}!".format(filename))

def parse_exif(exif_data):
    exif_section = exif_data["Exif"]
    zeroth_section = exif_data["0th"]

    exif_dict = {}
    try:
        exif_dict["Make"] = zeroth_section[271].decode("UTF-8")

        exif_dict["Model"] = zeroth_section[272].decode("UTF-8")

        exif_dict["Lens"] = exif_section[42036].decode("UTF-8")

        focal_length, divisor = exif_section[37386]
        exif_dict["Focal length"] = "{} mm".format(focal_length / divisor)

        depth_of_field, divisor = exif_section[33437]
        exif_dict["Depth of Field"] = "f/{}".format(depth_of_field / divisor)

        exif_dict["Exposure"], divisor = exif_section[33434]
        exif_dict["Exposure"] = "{}/{} sec".format(exif_dict["Exposure"], divisor )

        iso = exif_section[34855]
        exif_dict["ISO"] = "ISO {}".format(iso)

        exif_dict["Date/Time"] = exif_section[36867].decode("UTF-8")

        exif_dict["Software"] = zeroth_section[305].decode("UTF-8")
    except KeyError:
        print("No EXIF in image!")

    return exif_dict

def gen_html(images_exif_data):
    filename ="index.html"
    header = """
    <!DOCTYPE html>

    <html lang="en">
    <head>
        <title>My Webpage</title>
    </head>

    <body>
        <table>
            <tbody>"""
    footer = """
                </tbody>
        </table>
    </body>
    </html>"""

    with open(filename, "w") as index_file:
        index_file.write(header)
        for index in range(0, len(images_exif_data)):
            index_file.write("<tr>")
            index_file.write("<td>")
            index_file.write('<a href="{0}.jpg"><img src="{0}_thumb.jpg"></a>'.format(index+1))
            index_file.write("</td>")
            index_file.write("<td>")
            index_file.write('<ul>')
            for key, value in images_exif_data[index].items():
                index_file.write("<li>{} : {}</li>".format(key, value))
            index_file.write('</ul>')
            index_file.write("</td>")
            index_file.write("</tr>")
        index_file.write(footer)

if (__name__ == '__main__'):
    if (len(sys.argv) != 2):
        print("ERROR: Usage {} URL".format(sys.argv[0]))
        exit()

    url = sys.argv[1]
    image_urls = get_image_urls(url)

    if (image_urls != []):
        images_exif_data = []
        cnt = 1
        for image_url in image_urls:
            bytes = get_image_bytes(image_url)
            xif = get_exif_data(bytes)
            save_to_file(bytes, cnt)
            save_to_file(xif['thumbnail'], str(cnt) + "_thumb")
            xif_data = parse_exif(xif)
            images_exif_data.append(xif_data)
            cnt = cnt + 1

        gen_html(images_exif_data)