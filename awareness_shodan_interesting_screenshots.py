import click
import shodan
import base64
import io
import random
from PIL import Image

# Helpers
interesting_screenshot_labels = ['windows', 'login', 'desktop', 'terminal']
exclude_screenshot_labels = ['webcam']

def is_interesting_host(host):
    return any(label in interesting_screenshot_labels for label in host['screenshot']['labels']) \
        and not any(label in exclude_screenshot_labels for label in host['screenshot']['labels']) \
        #and ('text' in host['screenshot'] and len(host['screenshot']['text'].splitlines()) > 2) # Filter for results with longer text fields (= usually more accounts)

@click.command()
@click.option("--shodan_key",
                required=True,
                type=click.STRING,
                prompt="Shodan API Key")
@click.option("--country_code",
                required=True,
                type=click.STRING,
                prompt="Country code to search")
@click.option("--rows",
                required=True,
                type=click.INT,
                prompt="Rows in final mosaic")
@click.option("--columns",
                required=True,
                type=click.INT,
                prompt="Columns in final mosaic")
@click.option("--mosaic_count",
                required=True,
                type=click.INT,
                prompt="Number of mosaics to create")
def main(shodan_key, country_code, rows, columns, mosaic_count):
    # collect potentially interesting hosts
    shodan_api = shodan.Shodan(shodan_key)
    visually_interesting_hosts = shodan_api.search(query="country:%s has_screenshot:true" % country_code, limit=500, fields='screenshot')

    screenshot_goal = rows * columns
    interesting_hosts = list(filter(is_interesting_host, visually_interesting_hosts['matches']))

    # Create multiple mosaics of interesting screenshots
    screenshot_width = 1024
    screenshot_height = 800
    total_height = screenshot_height * rows
    total_width = screenshot_width * columns

    for i in range(mosaic_count):
        host_sample = random.sample(interesting_hosts, screenshot_goal)
        screenshots = [Image.open(io.BytesIO(base64.b64decode(host['screenshot']['data']))) for host in host_sample]

        screenshot_collection = Image.new('RGB', (total_width, total_height))
        for img_idx, image in enumerate(screenshots):
            screenshot_collection.paste(image,
                                        box=(img_idx % columns * screenshot_width,
                                            img_idx // columns * screenshot_height))

        screenshot_collection.save("output/shodan_%s_screenshots_%i.png" % (country_code.upper(), i), dpi=(300, 300))

if __name__ == '__main__':
    main()