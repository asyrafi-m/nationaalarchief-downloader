# **Nationaal Archief Bulk Downloader**

A small web application that helps researchers download multiple digitised scans from the **Nationaal Archief (Dutch National Archives)**.

The application is designed for situations where a researcher needs to download a large number of pages from the same archival bundle and downloading each scan individually would be impractical.

## **Features**

- Analyse a Nationaal Archief URL and identify the available digitised scans.
- Download a specific page range.
- Download an entire bundle.
- Select individual pages for download.
- Download selected scans as a ZIP archive.
- Preview scans through a thumbnail gallery.
- Open individual scans in a new browser tab.
- Warn users before downloading a large number of pages.
- Retry failed image requests automatically.

## **How it works**

The application takes a Nationaal Archief URL as input and retrieves the scan information associated with that object.

The image files are then retrieved using the image URLs made available by the Nationaal Archief. The selected files are packaged into a ZIP archive for the researcher.

The application does **not** attempt to bypass authentication, access controls, copyright restrictions, or other technical restrictions imposed by the Nationaal Archief.

Downloads are performed sequentially rather than through a large number of simultaneous requests. Failed requests are retried with increasing delays.

## **Intended use**

This tool was developed primarily as a convenience for **academic and archival research**. It is particularly useful when working with large digitised archival bundles where a researcher needs to obtain many individual scans for local research, transcription, OCR/HTR, or other scholarly purposes.

Users remain responsible for complying with the applicable terms of use, copyright conditions, and other restrictions associated with the material they download.

The tool is an independent research project and is **not an official Nationaal Archief application**.

## **Important note**

The application retrieves files from infrastructure operated by or associated with the Nationaal Archief. Please use it responsibly and avoid unnecessarily large or repeated downloads.

The developer is currently seeking clarification from the Nationaal Archief regarding any applicable technical guidelines, rate limits, or other requirements concerning automated retrieval of publicly available scans.

## **Acknowledgements**

Thanks to **Muhammad Masruhan** for providing valuable insights into the user experience and for testing the application.

## **Technology**

The application is built with:

- [Svelte](https://svelte.dev/)
- [Vite](https://vite.dev/)
- Python
- Vercel

## **Development**

Install the dependencies:

```bash
npm install
```

Run the frontend development server:

```bash
npm run dev
```

The Python API can be run locally from the project directory:

```bash
python3 api/analyze.py
```

and, where applicable:

```bash
python3 api/download.py
```

The Vite development server proxies `/api` requests to the local Python API.

Build the application for production:

```bash
npm run build
```

## **Project status**

This is an independent research tool under active development.

The application may change as technical requirements, archival interfaces, or feedback from the Nationaal Archief develop.

## **Author**

**Muhammad Asyrafi**
PhD Researcher, Leiden University

---

_This project is not affiliated with or endorsed by the Nationaal Archief unless explicitly stated otherwise._