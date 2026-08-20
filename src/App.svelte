<script>
  let archiveUrl = ''
  let loading = false
  let downloading = false
  let error = ''
  let result = null
  let downloadStatus = ''
  let activeDownloadMode = ''

  let currentPage = 1
  const itemsPerPage = 10

  // Page-range download
  let downloadFrom = 1
  let downloadTo = 1

  // Individual page selection
  let selectedPages = new Set()

  $: totalPages = result
    ? Math.ceil(result.files.length / itemsPerPage)
    : 0

  $: startIndex = (currentPage - 1) * itemsPerPage

  $: visibleFiles = result
    ? result.files.slice(startIndex, startIndex + itemsPerPage)
    : []

  // Number of pages in the selected range
  $: selectedPageCount =
    result && downloadTo >= downloadFrom
      ? downloadTo - downloadFrom + 1
      : 0

  // Number of individually selected pages
  $: selectedCount = selectedPages.size

  // Number of individually selected pages currently visible
  $: visibleSelectedCount = visibleFiles.filter(
    file => selectedPages.has(file.page)
  ).length


  // -------------------------------------------------
  // Analyze bundle
  // -------------------------------------------------

  async function analyzeBundle() {
    error = ''
    result = null
    downloadStatus = ''
    activeDownloadMode = ''
    selectedPages = new Set()

    if (!archiveUrl.trim()) {
      error = 'Please enter a Nationaal Archief URL.'
      return
    }

    loading = true

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          url: archiveUrl.trim()
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.error || 'Something went wrong.'
        )
      }

      result = data
      currentPage = 1

      // Start with the first 10 pages selected
      // for the page-range downloader.
      downloadFrom = 1
      downloadTo = Math.min(10, data.files.length)

    } catch (err) {
      error = err.message

    } finally {
      loading = false
    }
  }


  // -------------------------------------------------
  // Individual page selection
  // -------------------------------------------------

  function togglePage(pageNumber) {
    const updated = new Set(selectedPages)

    if (updated.has(pageNumber)) {
      updated.delete(pageNumber)
    } else {
      updated.add(pageNumber)
    }

    selectedPages = updated
  }


  function selectAllPages() {
    if (!result || !result.files) {
      return
    }

    selectedPages = new Set(
      result.files.map(file => file.page)
    )
  }


  function clearSelection() {
    selectedPages = new Set()
  }


  function selectVisiblePages() {
    const updated = new Set(selectedPages)

    for (const file of visibleFiles) {
      updated.add(file.page)
    }

    selectedPages = updated
  }


  function clearVisiblePages() {
    const updated = new Set(selectedPages)

    for (const file of visibleFiles) {
      updated.delete(file.page)
    }

    selectedPages = updated
  }


  // -------------------------------------------------
  // Common download function
  // -------------------------------------------------

  async function downloadFiles(
    files,
    mode = 'bundle',
    from = null,
    to = null
  ) {
    if (!files || files.length === 0) {
      error = 'No images selected for download.'
      return
    }

    // -------------------------------------------------
    // Large-download warning
    //
    // IMPORTANT:
    // The download status is NOT activated before this
    // confirmation. Therefore, if the user clicks Cancel,
    // no "Preparing download..." status will remain.
    // -------------------------------------------------

    if (files.length > 100) {
      const confirmed = window.confirm(
        `This download contains ${files.length} pages.\n\n` +
        `Downloading a large number of pages may take ` +
        `considerable time and may be affected by network ` +
        `or server limitations.\n\n` +
        `Please allow sufficient time for the process to ` +
        `complete and avoid closing or suspending the browser ` +
        `during the download.\n\n` +
        `Do you want to continue?`
      )

      if (!confirmed) {
        return
      }
    }

    // -------------------------------------------------
    // Start download
    // -------------------------------------------------

    error = ''
    downloadStatus = 'Preparing download...'
    activeDownloadMode = mode
    downloading = true

    try {
      const response = await fetch('/api/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          files
        })
      })

      if (!response.ok) {
        let message = 'Download failed.'

        try {
          const data = await response.json()
          message = data.error || message
        } catch {
          // Response wasn't JSON
        }

        throw new Error(message)
      }

      if (mode === 'range') {
        downloadStatus =
          `Downloading pages ${from}–${to} and creating ZIP...`

      } else if (mode === 'selected') {
        downloadStatus =
          `Downloading ${files.length} selected page${files.length === 1 ? '' : 's'} and creating ZIP...`

      } else {
        downloadStatus =
          'Downloading images and creating ZIP...'
      }

      const blob = await response.blob()

      downloadStatus = 'Download complete!'

      const url = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url

      // -------------------------------------------------
      // Filename
      // -------------------------------------------------

      if (mode === 'selected') {
        link.download =
          `NationaalArchief_${result.archive}_${result.inventory}_selected.zip`

      } else if (mode === 'range') {
        link.download =
          `NationaalArchief_${result.archive}_${result.inventory}_pages_${from}-${to}.zip`

      } else {
        link.download =
          `NationaalArchief_${result.archive}_${result.inventory}.zip`
      }

      document.body.appendChild(link)
      link.click()
      link.remove()

      URL.revokeObjectURL(url)

    } catch (err) {
      error = err.message
      downloadStatus = ''

    } finally {
      downloading = false
      activeDownloadMode = ''
    }
  }


  // -------------------------------------------------
  // Download page range
  // -------------------------------------------------

  async function downloadSelectedPages() {
    if (!result || !result.files || result.files.length === 0) {
      error = 'No images available to download.'
      return
    }

    const from = Number(downloadFrom)
    const to = Number(downloadTo)

    if (
      !Number.isInteger(from) ||
      !Number.isInteger(to)
    ) {
      error = 'Please enter valid page numbers.'
      return
    }

    if (from < 1 || to > result.files.length) {
      error =
        `Please enter page numbers between 1 and ${result.files.length}.`
      return
    }

    if (from > to) {
      error =
        'The starting page must be smaller than or equal to the ending page.'
      return
    }

    const selectedFiles = result.files.slice(
      from - 1,
      to
    )

    await downloadFiles(
      selectedFiles,
      'range',
      from,
      to
    )
  }


  // -------------------------------------------------
  // Download entire bundle
  // -------------------------------------------------

  async function downloadBundle() {
    if (!result || !result.files || result.files.length === 0) {
      error = 'No images available to download.'
      return
    }

    await downloadFiles(
      result.files,
      'bundle'
    )
  }


  // -------------------------------------------------
  // Download individually selected pages
  // -------------------------------------------------

  async function downloadSelected() {
    if (!result || !result.files) {
      error = 'No images available.'
      return
    }

    const selectedFiles = result.files.filter(
      file => selectedPages.has(file.page)
    )

    if (selectedFiles.length === 0) {
      error = 'Please select at least one page.'
      return
    }

    await downloadFiles(
      selectedFiles,
      'selected'
    )
  }
</script>


<main>
  <div class="container">

    <h1>Nationaal Archief Bulk Downloader</h1>

    <p class="intro">
      Version 1.0.1<br />
      Download digitised scans from the Dutch National Archives.
    </p>


    <!-- --------------------------------------------- -->
    <!-- URL input -->
    <!-- --------------------------------------------- -->

    <label for="archive-url">
      Nationaal Archief URL
    </label>

    <textarea
      id="archive-url"
      bind:value={archiveUrl}
      placeholder="Paste a Nationaal Archief URL here..."
    ></textarea>

    <button
      onclick={analyzeBundle}
      disabled={loading || downloading}
    >
      {loading ? 'Analyzing...' : 'Analyze bundle'}
    </button>


    <!-- --------------------------------------------- -->
    <!-- Error -->
    <!-- --------------------------------------------- -->

    {#if error}
      <div class="error">
        {error}
      </div>
    {/if}


    {#if result}

      <section class="results">

        <!-- ----------------------------------------- -->
        <!-- Bundle information -->
        <!-- ----------------------------------------- -->

        <div class="bundle-info-citation">
          <div class="bundle-info">
            <h2>Bundle found</h2>

            <p>
              <strong>Archive:</strong>
            {result.archive}
            </p>

            <p>
              <strong>Inventory:</strong>
            {result.inventory}
            </p>

            <p>
              <strong>Images:</strong>
              {result.count}
            </p>
          </div>
        <!-- ----------------------------------------- -->
        <!-- Export archive information as citation -->
        <!-- ----------------------------------------- -->
          <div class="export-citation">
            <p>Export archive information as citation (BibTeX, RIS)</p>
            <div>
              <button
              class="card-button"
            > RIS
            </button>
            <button
              class="card-button"
            > BibTeX
            </button>
            </div>
          </div>
        </div>

        <!-- ----------------------------------------- -->
        <!-- Download instruction -->
        <!-- ----------------------------------------- -->

        <p class="download-instruction">
          Please choose the download option that best suits your needs.
        </p>


        <!-- ----------------------------------------- -->
        <!-- Download options -->
        <!-- ----------------------------------------- -->

        <div class="download-options">


          <!-- --------------------------------------- -->
          <!-- Page range -->
          <!-- --------------------------------------- -->

          <div class="download-card">

            <h3>Download a page range</h3>

            <p class="card-description">
              Enter the first and last page you want to download.
            </p>

            <div class="range-inputs">

              <label>
                From

                <input
                  type="number"
                  min="1"
                  max={result.count}
                  bind:value={downloadFrom}
                  disabled={loading || downloading}
                />
              </label>

              <span class="range-dash">–</span>

              <label>
                To

                <input
                  type="number"
                  min="1"
                  max={result.count}
                  bind:value={downloadTo}
                  disabled={loading || downloading}
                />
              </label>

            </div>

            <p class="selection-info">
              {selectedPageCount}
              page{selectedPageCount === 1 ? '' : 's'}
              selected
            </p>

            <button
              class="card-button"
              onclick={downloadSelectedPages}
              disabled={
                loading ||
                downloading
              }
            >
              {activeDownloadMode === 'range' && downloading
                ? 'Preparing download...'
                : `Download pages ${downloadFrom}–${downloadTo}`}
            </button>

          </div>


          <!-- --------------------------------------- -->
          <!-- Entire bundle -->
          <!-- --------------------------------------- -->

          <div class="download-card">

            <h3>Download entire bundle</h3>

            <p class="card-description">
              Download all images in this bundle as a ZIP file.
            </p>

            <button
              class="card-button"
              onclick={downloadBundle}
              disabled={loading || downloading}
            >
              {activeDownloadMode === 'bundle' && downloading
                ? 'Preparing download...'
                : 'Download entire bundle as ZIP'}
            </button>

          </div>


          <!-- --------------------------------------- -->
          <!-- Individual pages -->
          <!-- --------------------------------------- -->

          <div class="download-card">

            <h3>Select individual pages</h3>

            <p class="card-description">
              Select specific pages from the thumbnails below.
            </p>

            <div class="selection-summary">

              <strong>{selectedCount}</strong>
              {selectedCount === 1 ? 'page' : 'pages'} selected

            </div>

            <div class="selection-buttons">

              <button
                onclick={selectAllPages}
                disabled={loading || downloading}
              >
                Select all
              </button>

              <button
                onclick={clearSelection}
                disabled={
                  selectedCount === 0 ||
                  loading ||
                  downloading
                }
              >
                Clear selection
              </button>

              {#if visibleSelectedCount < visibleFiles.length}

                <button
                  onclick={selectVisiblePages}
                  disabled={loading || downloading}
                >
                  Select visible
                </button>

              {/if}

              {#if visibleSelectedCount > 0}

                <button
                  onclick={clearVisiblePages}
                  disabled={loading || downloading}
                >
                  Clear visible
                </button>

              {/if}

            </div>

            {#if selectedCount > 0}

              <button
                class="card-button individual-download"
                onclick={downloadSelected}
                disabled={loading || downloading}
              >
                {activeDownloadMode === 'selected' && downloading
                  ? 'Preparing download...'
                  : `Download ${selectedCount} selected ${selectedCount === 1 ? 'page' : 'pages'} as ZIP`}
              </button>

            {/if}

          </div>

        </div>


        <!-- ----------------------------------------- -->
        <!-- Download status -->
        <!-- ----------------------------------------- -->

        {#if downloadStatus}

          <div
            class:complete={downloadStatus === 'Download complete!'}
            class="download-status"
          >

            {#if downloadStatus === 'Download complete!'}

              <span class="status-check">✓</span>

            {:else}

              <span class="status-spinner"></span>

            {/if}

            {downloadStatus}

          </div>

        {/if}


        <!-- ----------------------------------------- -->
        <!-- Gallery -->
        <!-- ----------------------------------------- -->

        <div class="gallery-section">

          <h2>Thumbnail section</h2>

          <div class="gallery">

            {#each visibleFiles as file}

              <div
                class:selected={selectedPages.has(file.page)}
                class="thumbnail-wrapper"
              >

                <label class="selection-checkbox">

                  <input
                    type="checkbox"
                    checked={selectedPages.has(file.page)}
                    onchange={() => togglePage(file.page)}
                    disabled={loading || downloading}
                  />

                  <span>Select page {file.page}</span>

                </label>


                <a
                  href={file.image}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="thumbnail"
                >

                  <img
                    src={file.thumbnail}
                    alt={`Page ${file.page}`}
                    loading="lazy"
                  />

                  <span>Page {file.page}</span>

                </a>

              </div>

            {/each}

          </div>


          <!-- --------------------------------------- -->
          <!-- Pagination -->
          <!-- --------------------------------------- -->

          <div class="pagination">

            <button
              onclick={() => currentPage--}
              disabled={
                currentPage === 1 ||
                loading ||
                downloading
              }
            >
              ← Previous
            </button>


            <div class="page-numbers">

              {#each Array(totalPages) as _, i}

                <button
                  class:active={currentPage === i + 1}
                  onclick={() => currentPage = i + 1}
                  disabled={loading || downloading}
                >
                  {i + 1}
                </button>

              {/each}

            </div>


            <button
              onclick={() => currentPage++}
              disabled={
                currentPage === totalPages ||
                loading ||
                downloading
              }
            >
              Next →
            </button>

          </div>


          <p class="page-info">

            Showing pages
            {startIndex + 1}–{Math.min(
              startIndex + itemsPerPage,
              result.count
            )}
            of {result.count}

          </p>

        </div>

      </section>

    {/if}

  </div>
</main>


<style>

  /* --------------------------------------------- */
  /* Main layout */
  /* --------------------------------------------- */

  main {
    min-height: 100vh;
    background: #f5f5f5;
    padding: 60px 20px;
    box-sizing: border-box;
  }


  .container {
    max-width: 900px;
    margin: 0 auto;
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }


  h1 {
    margin: 0 0 10px;
    font-size: 2rem;
    color: #333;
    line-height: normal;
    letter-spacing: normal;
    font-weight: lighter;
  }


  .intro {
    color: #666;
    margin-bottom: 30px;
  }


  label {
    display: block;
    font-weight: 600;
    margin-bottom: 8px;
  }


  textarea {
    width: 100%;
    min-height: 100px;
    box-sizing: border-box;
    padding: 12px;
    font-family: monospace;
    font-size: 14px;
    border: 1px solid #ccc;
    border-radius: 6px;
    resize: vertical;
  }


  button {
    margin-top: 20px;
    padding: 12px 20px;
    border: none;
    border-radius: 6px;
    background: #333;
    color: white;
    font-size: 15px;
    cursor: pointer;
  }


  button:hover {
    background: #555;
  }


  button:disabled {
    opacity: 0.6;
    cursor: wait;
  }


  /* --------------------------------------------- */
  /* Error */
  /* --------------------------------------------- */

  .error {
    margin-top: 20px;
    padding: 15px;
    background: #fee;
    color: #900;
    border-radius: 6px;
  }


  /* --------------------------------------------- */
  /* Results */
  /* --------------------------------------------- */

  .results {
    margin-top: 30px;
    padding-top: 25px;
    border-top: 1px solid #ddd;
  }


  .bundle-info h2 {
    margin-top: 0;
  }


  .bundle-info p {
    margin: 8px 0;
  }


  /* --------------------------------------------- */
  /* Download instruction */
  /* --------------------------------------------- */

  .download-instruction {
    margin: 28px 0 18px;
    color: #555;
    font-size: 14px;
  }


  /* --------------------------------------------- */
  /* Download options */
  /* --------------------------------------------- */

  .download-options {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
    align-items: stretch;
  }


  .download-card {
    display: flex;
    flex-direction: column;
    padding: 20px;
    background: #f8f8f8;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-sizing: border-box;
    justify-content: space-between;
  }


  .download-card h3 {
    margin: 0 0 8px;
    font-size: 16px;
    color: #333;
  }


  .card-description {
    margin: 0;
    color: #666;
    font-size: 13px;
    line-height: 1.5;
  }


  /* --------------------------------------------- */
  /* Page range */
  /* --------------------------------------------- */

  .range-inputs {
    display: flex;
    align-items: end;
    gap: 8px;
    margin-top: 18px;
    justify-content: center;
  }


  .range-inputs label {
    margin: 0;
    font-size: 13px;
  }


  .range-inputs input {
    display: block;
    width: 75px;
    box-sizing: border-box;
    margin-top: 5px;
    padding: 9px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 14px;
  }


  .range-dash {
    padding-bottom: 9px;
    color: #666;
  }


  .selection-info {
    margin: 12px 0 0;
    color: #666;
    font-size: 13px;
  }


  /* --------------------------------------------- */
  /* Card buttons */
  /* --------------------------------------------- */

  .card-button {
    width: 100%;
    margin-top: auto;
    padding: 11px 14px;
    font-size: 14px;
  }


  /* --------------------------------------------- */
  /* Individual selection */
  /* --------------------------------------------- */

  .selection-summary {
    margin-top: 18px;
    color: #555;
    font-size: 14px;
  }


  .selection-buttons {
    display: flex;
    gap: 6px;
    flex-wrap: nowrap;
    margin-top: 8px;
  }


  .selection-buttons button {
    margin-top: 4px;
    padding: 7px 9px;
    font-size: 12px;
    background: white;
    color: #333;
    border: 1px solid #ccc;
  }


  .selection-buttons button:hover {
    background: #eee;
  }


  .individual-download {
    margin-top: auto;
  }


  /* --------------------------------------------- */
  /* Download status */
  /* --------------------------------------------- */

  .download-status {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 18px;
    padding: 12px 15px;
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 6px;
    color: #555;
    font-size: 14px;
  }


  .status-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid #ccc;
    border-top-color: #333;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    flex-shrink: 0;
  }


  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }


  .download-status.complete {
    background: #f0f8f0;
    border-color: #b8d8b8;
    color: #286328;
  }


  .status-check {
    font-size: 18px;
    font-weight: bold;
  }


  /* --------------------------------------------- */
  /* Gallery */
  /* --------------------------------------------- */

  .gallery-section {
    margin-top: 30px;
  }


  .gallery-section h2 {
    margin: 0 0 15px;
    font-size: 18px;
    color: #333;
  }


  .gallery {
    display: grid;

    /*
     * Keep exactly five thumbnails per row at the
     * normal desktop width.
     */
    grid-template-columns: repeat(5, minmax(0, 1fr));

    gap: 12px;
  }


  .thumbnail-wrapper {
    position: relative;
    min-width: 0;
    background: #f5f5f5;
    border: 2px solid transparent;
    border-radius: 8px;
    padding: 6px;
    box-sizing: border-box;
    transition:
      border-color 0.15s ease,
      box-shadow 0.15s ease;
  }


  .thumbnail-wrapper.selected {
    border-color: #333;
    box-shadow:
      0 4px 12px rgba(0, 0, 0, 0.15);
  }


  .selection-checkbox {
    display: flex;
    align-items: center;
    gap: 5px;
    margin-bottom: 5px;
    font-size: 11px;
    font-weight: 600;
    color: #555;
    cursor: pointer;
    white-space: nowrap;
  }


  .selection-checkbox input {
    width: 15px;
    height: 15px;
    margin: 0;
    cursor: pointer;
    flex-shrink: 0;
  }


  .selection-checkbox input:disabled {
    cursor: wait;
  }


  .thumbnail {
    display: block;
    text-decoration: none;
    color: #333;
    background: white;
    border-radius: 6px;
    padding: 0;
    transition:
      transform 0.15s ease,
      box-shadow 0.15s ease;
  }


  .thumbnail:hover {
    transform: translateY(-2px);
    box-shadow:
      0 4px 12px rgba(0, 0, 0, 0.15);
  }


  .thumbnail img {
    display: block;
    width: 100%;
    height: 170px;
    object-fit: contain;
    background: white;
  }


  .thumbnail span {
    display: block;
    text-align: center;
    margin-top: 7px;
    margin-bottom: 7px;
    font-size: 12px;
    font-weight: 600;
  }


  /* --------------------------------------------- */
  /* Pagination */
  /* --------------------------------------------- */

  .pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-top: 30px;
    flex-wrap: wrap;
  }


  .pagination button {
    margin-top: 0;
    padding: 8px 12px;
    font-size: 14px;
  }


  .page-numbers {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
    justify-content: center;
  }


  .page-numbers button {
    background: white;
    color: #333;
    border: 1px solid #ccc;
  }


  .page-numbers button:hover {
    background: #eee;
  }


  .page-numbers button.active {
    background: #333;
    color: white;
    border-color: #333;
  }


  .page-info {
    text-align: center;
    color: #666;
    font-size: 13px;
    margin-top: 12px;
  }


  /* --------------------------------------------- */
  /* Responsive layout */
  /* --------------------------------------------- */

  @media (max-width: 800px) {

    .download-options {
      grid-template-columns: 1fr;
    }

    .gallery {
      grid-template-columns: repeat(5, minmax(0, 1fr));
    }

  }


  @media (max-width: 600px) {

    main {
      padding: 20px 10px;
    }

    .container {
      padding: 25px 18px;
    }

    .gallery {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

  }

</style>