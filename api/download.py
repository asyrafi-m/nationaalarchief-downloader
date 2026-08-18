import urllib.request
import urllib.error
import io
import zipfile
import time


def download_image(image_url, page_number):

    max_attempts = 10

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
                    "Accept": (
                        "image/avif,image/webp,"
                        "image/apng,image/svg+xml,"
                        "image/*,*/*;q=0.8"
                    ),
                    "Referer": (
                        "https://www.nationaalarchief.nl/"
                    )
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

                wait_time = min(attempt * 2, 10)

                print(
                    f"Retrying page {page_number} "
                    f"in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                print(
                    f"Page {page_number} failed after "
                    f"{max_attempts} attempts."
                )

        except Exception as e:

            print(
                f"Error downloading page "
                f"{page_number}: {repr(e)}"
            )

            if attempt < max_attempts:

                wait_time = min(attempt * 2, 10)

                print(
                    f"Retrying page {page_number} "
                    f"in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                print(
                    f"Page {page_number} failed after "
                    f"{max_attempts} attempts."
                )

    return None


def create_zip(files):

    if not files:
        raise ValueError("No files provided.")

    print(
        "Creating ZIP for",
        len(files),
        "images..."
    )

    zip_buffer = io.BytesIO()

    failed_pages = []

    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:

        for index, file in enumerate(files):

            image_url = file.get("image")

            page_number = file.get(
                "page",
                index + 1
            )

            if not image_url:

                print(
                    f"Skipping page {page_number}: "
                    "no image URL"
                )

                failed_pages.append(page_number)

                continue

            image_data = download_image(
                image_url,
                page_number
            )

            if image_data is None:

                failed_pages.append(page_number)

                print(
                    f"Continuing without "
                    f"page {page_number}..."
                )

                continue

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
        # Add error report
        # ---------------------------------------------

        if failed_pages:

            error_text = (
                "The following pages could not be "
                "downloaded after multiple attempts:\n\n"
            )

            error_text += "\n".join(
                f"Page {page}"
                for page in failed_pages
            )

            error_text += (
                "\n\nThese failures may be temporary. "
                "You can try downloading the bundle "
                "again later."
            )

            zip_file.writestr(
                "DOWNLOAD_ERRORS.txt",
                error_text
            )

    zip_data = zip_buffer.getvalue()

    print(
        "ZIP size:",
        len(zip_data),
        "bytes"
    )

    print(
        "Failed pages:",
        failed_pages
    )

    return zip_data