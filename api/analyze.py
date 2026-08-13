from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re


class handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()

        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )
        self.end_headers()

    def do_GET(self):
        self.send_json(200, {
            "status": "ok",
            "message": "Nationaal Archief API is working"
        })

    def do_POST(self):

        try:
            length = int(
                self.headers.get("Content-Length", 0)
            )

            body = self.rfile.read(length)
            request_data = json.loads(body)

            archive_url = request_data.get(
                "url",
                ""
            ).strip()

            if not archive_url:
                self.send_json(400, {
                    "error": "No Nationaal Archief URL provided."
                })
                return

            print("Received:", archive_url)

            # -------------------------------------------------
            # 1. Extract archive ID and inventory number
            # -------------------------------------------------

            match = re.search(
                r"/archief/([^/]+)/invnr/@(\d+)",
                archive_url
            )

            if not match:
                self.send_json(400, {
                    "error": (
                        "Could not identify the archive number "
                        "and inventory number from the URL."
                    )
                })
                return

            archive_id = match.group(1)
            inventory_number = match.group(2)

            print(
                "Archive:",
                archive_id,
                "Inventory:",
                inventory_number
            )

            # -------------------------------------------------
            # 2. Download EAD
            # -------------------------------------------------

            ead_url = (
                "https://service.archief.nl/gaf/oai/"
                "!open_oai.OAIHandler"
                "?verb=GetRecord"
                "&metadataPrefix=oai_ead"
                "&identifier="
                + urllib.parse.quote(archive_id)
            )

            print("Downloading EAD...")
            print(ead_url)

            request = urllib.request.Request(
                ead_url,
                headers={
                    "User-Agent":
                        "NationaalArchiefBulkDownloader/1.0"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:

                ead_data = response.read()

            print(
                "Downloaded EAD:",
                len(ead_data),
                "bytes"
            )

            # -------------------------------------------------
            # 3. Parse EAD
            # -------------------------------------------------

            root = ET.fromstring(ead_data)

            mets_url = None

            for unitid in root.iter("unitid"):

                # We only want the public inventory number,
                # not the internal identifier/handle.
                if (
                    unitid.text
                    and unitid.text.strip()
                    == inventory_number
                    and unitid.get("type") != "handle"
                ):

                    parent_did = None
                    parent_c = None

                    # Find the <did> containing this unitid
                    for did in root.iter("did"):
                        if unitid in list(did):
                            parent_did = did
                            break

                    if parent_did is None:
                        continue

                    # Find the enclosing <c>
                    for c in root.iter("c"):
                        if parent_did in list(c):
                            parent_c = c
                            break

                    if parent_c is None:
                        continue

                    # Find METS DAO inside this record
                    for dao in parent_c.iter("dao"):

                        if dao.get("role") == "METS":
                            mets_url = dao.get("href")
                            break

                    if mets_url:
                        break

            if not mets_url:
                self.send_json(404, {
                    "error": (
                        "Could not find a METS record for "
                        f"inventory number {inventory_number}."
                    )
                })
                return

            print("METS URL:", mets_url)

            # -------------------------------------------------
            # 4. Download METS
            # -------------------------------------------------

            print("Downloading METS...")

            request = urllib.request.Request(
                mets_url,
                headers={
                    "User-Agent":
                        "NationaalArchiefBulkDownloader/1.0"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:

                mets_data = response.read()

            print(
                "Downloaded METS:",
                len(mets_data),
                "bytes"
            )

            # -------------------------------------------------
            # 5. Parse METS and find JPEGs
            # -------------------------------------------------

            mets_root = ET.fromstring(mets_data)

            namespaces = {
                "mets": "http://www.loc.gov/METS/",
                "xlink": "http://www.w3.org/1999/xlink"
            }

            files = []

            for file_element in mets_root.findall(
                ".//mets:file",
                namespaces
            ):

                if file_element.get("USE") != "DISPLAY":
                    continue

                if file_element.get("MIMETYPE") != "image/jpeg":
                    continue

                flocat = file_element.find(
                    "mets:FLocat",
                    namespaces
                )

                if flocat is None:
                    continue

                file_url = flocat.get(
                     "{http://www.w3.org/1999/xlink}href"
                )

                if not file_url:
                    continue
                # Exclude thumbnail files from the downloadable image list.
                # Thumbnails are still generated separately for the UI.
                if "/thumb/" in file_url:
                    continue

                image_id = file_url.rstrip("/").split("/")[-1]
                
                thumbnail_url = (
                     "https://service.archief.nl/gaf/api/file/v1/thumb/"
                     + image_id
                )

                files.append({
                    "page": len(files) + 1,
                    "thumbnail": thumbnail_url,
                    "image": file_url
                })

            print(
                "Found",
                len(files),
                "images"
            )

            # -------------------------------------------------
            # 6. Return result
            # -------------------------------------------------

            self.send_json(200, {
                "status": "ok",
                "archive": archive_id,
                "inventory": inventory_number,
                "metsUrl": mets_url,
                "count": len(files),
                "files": files
            })

        except Exception as e:

            print("ERROR:", repr(e))

            self.send_json(500, {
                "error": str(e)
            })