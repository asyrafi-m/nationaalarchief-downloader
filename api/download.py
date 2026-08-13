from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import io
import zipfile


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "POST, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )
        self.end_headers()

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

            files = request_data.get("files", [])

            if not files:
                self.send_json(
                    400,
                    {"error": "No files provided."}
                )
                return

            # ---------------------------------------------
            # TEST MODE
            # Only download first 2 images
            # ---------------------------------------------

            files = files[:2]

            print(
                "Downloading",
                len(files),
                "test images..."
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
                        continue

                    print(
                        "Downloading image",
                        index + 1,
                        image_url
                    )

                    request = urllib.request.Request(
                        image_url,
                        headers={
                            "User-Agent":
                                "NationaalArchiefBulkDownloader/1.0"
                        }
                    )

                    with urllib.request.urlopen(
                        request,
                        timeout=60
                    ) as response:

                        image_data = response.read()

                    filename = (
                        f"page_{index + 1:04d}.jpg"
                    )

                    zip_file.writestr(
                        filename,
                        image_data
                    )

                    print(
                        "Added",
                        filename,
                        len(image_data),
                        "bytes"
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
                'attachment; filename="nationaalarchief-test.zip"'
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
                {"error": str(e)}
            )

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