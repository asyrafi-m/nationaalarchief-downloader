from http.server import HTTPServer

from analyze import handler


if __name__ == "__main__":

    server = HTTPServer(
        ("127.0.0.1", 8000),
        handler
    )

    print("Python API running at:")
    print("http://127.0.0.1:8000")

    server.serve_forever()