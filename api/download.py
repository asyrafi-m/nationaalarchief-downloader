from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import io
import zipfile
import time


class handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):

        body = json.dumps(data).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)

    def do_OPTIONS(self):

        self.send_response(204)

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.end_headers()

    def download_image(self, image_url, page_number):

        max_attempts = 3

        for attempt in range(1, max_attempts + 1):

            try:

                print(
                    f"Downloading page {page_number} "
                    f"(attempt {attempt}/{max_attempts}): "
                    f"{image_url}"
                )

                request = urllib.request.Request(
                    image_url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 "
                            "(Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 "
                            "(KHTML, like Gecko) "
                            "Chrome/138.0 Safari/537.36"
                        ),
                        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                        "Referer": "https://www.nationaalarchief.nl/"
                    }
                )

                with urllib.request.urlopen(
                    request,
                    timeout=120
                ) as response:

                    image_data = response.read()

                print(
                    f"Downloaded page {page_number}: "
                    f"{len(image_data)} bytes"
                )

                return image_data

            except urllib.error.HTTPError as e:

                print(
                    f"HTTP error downloading page "
                    f"{page_number}: {e.code}"
                )

                if attempt < max_attempts:

                    wait_time = attempt * 2

                    print(
                        f"Retrying page {page_number} "
                        f"in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                else:

                    raise Exception(
                        f"Failed to download page "
                        f"{page_number}: "
                        f"HTTP {e.code} after "
                        f"{max_attempts} attempts"
                    )

            except Exception as e:

                print(
                    f"Error downloading page "
                    f"{page_number}: {repr(e)}"
                )

                if attempt < max_attempts:

                    wait_time = attempt * 2

                    print(
                        f"Retrying page {page_number} "
                        f"in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                else:

                    raise Exception(
                        f"Failed to download page "
                        f"{page_number}: {e}"
                    )

    def do_POST(self):

        try:

            # ---------------------------------------------
            # 1. Read request
            # ---------------------------------------------

            length = int(
                self.headers.get("Content-Length", 0)
            )

            body = self.rfile.read(length)

            request_data = json.loads(body)

            files = request_data.get(
                "files",
                []
            )

            if not files:

                self.send_json(
                    400,
                    {
                        "error":
                        "No files provided."
                    }
                )

                return

            print(
                "Downloading",
                len(files),
                "images..."
            )

            # ---------------------------------------------
            # 2. Create ZIP in memory
            # ---------------------------------------------

            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(
                zip_buffer,
                "w",
                zipfile.ZIP_DEFLATED
            ) as zip_file:

                for index, file in enumerate(files):

                    image_url = file.get("image")

                    if not image_url:

                        print(
                            f"Skipping page "
                            f"{index + 1}: no image URL"
                        )

                        continue

                    page_number = index + 1

                    image_data = self.download_image(
                        image_url,
                        page_number
                    )

                    filename = (
                        f"page_{page_number:04d}.jpg"
                    )

                    zip_file.writestr(
                        filename,
                        image_data
                    )

                    print(
                        f"Added {filename} "
                        f"{len(image_data)} bytes"
                    )

            # ---------------------------------------------
            # 3. Return ZIP
            # ---------------------------------------------

            zip_data = zip_buffer.getvalue()

            print(
                "ZIP size:",
                len(zip_data),
                "bytes"
            )

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/zip"
            )

            self.send_header(
                "Content-Disposition",
                'attachment; filename="nationaalarchief-bundle.zip"'
            )

            self.send_header(
                "Access-Control-Allow-Origin",
                "*"
            )

            self.send_header(
                "Content-Length",
                str(len(zip_data))
            )

            self.end_headers()

            self.wfile.write(zip_data)

        except Exception as e:

            print(
                "DOWNLOAD ERROR:",
                repr(e)
            )

            self.send_json(
                500,
                {
                    "error": str(e)
                }
            )


if __name__ == "__main__":

    from http.server import HTTPServer

    server = HTTPServer(
        ("127.0.0.1", 8000),
        handler
    )

    print(
        "Python API running at:"
    )

    print(
        "http://127.0.0.1:8000"
    )

    server.serve_forever()