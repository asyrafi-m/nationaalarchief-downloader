<script>
  let archiveUrl = ''
  let loading = false
  let downloading = false
  let error = ''
  let result = null
  let downloadStatus = ''

  let currentPage = 1
  const itemsPerPage = 10

  $: totalPages = result
    ? Math.ceil(result.files.length / itemsPerPage)
    : 0

  $: startIndex = (currentPage - 1) * itemsPerPage

  $: visibleFiles = result
    ? result.files.slice(startIndex, startIndex + itemsPerPage)
    : []

  async function analyzeBundle() {
    error = ''
    result = null
    downloadStatus = ''

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

    } catch (err) {
      error = err.message

    } finally {
      loading = false
    }
  }

  async function downloadBundle() {
    if (!result || !result.files || result.files.length === 0) {
      error = 'No images available to download.'
      return
    }

    // -------------------------------------------------
    // Large-download warning
    // -------------------------------------------------

    if (result.files.length > 100) {
      const confirmed = window.confirm(
        `This bundle contains ${result.files.length} pages.\n\n` +
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

    error = ''
    downloadStatus = 'Preparing download...'
    downloading = true

    try {
      const response = await fetch('/api/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          files: result.files
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

      downloadStatus = 'Downloading images and creating ZIP...'

      const blob = await response.blob()

      downloadStatus = 'Download complete!'

      const url = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = url
      link.download = `NationaalArchief_${result.archive}_${result.inventory}.zip`

      document.body.appendChild(link)
      link.click()
      link.remove()

      URL.revokeObjectURL(url)

    } catch (err) {
      error = err.message
      downloadStatus = ''
    } finally {
      downloading = false
    }
  }
</script>

<main>
  <div class="container">

    <h1>Nationaal Archief Bulk Downloader</h1>

    <p class="intro">
      Download digitised scans from the Dutch National Archives.
    </p>

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

    {#if error}
      <div class="error">
        {error}
      </div>
    {/if}

    {#if result}
      <section class="results">

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

        <button
          onclick={downloadBundle}
          disabled={loading || downloading}
        >
          {downloading
            ? 'Preparing download...'
            : 'Download entire bundle as ZIP'}
        </button>

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

        <div class="gallery">
          {#each visibleFiles as file}
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
          {/each}
        </div>

        <div class="pagination">

          <button
            onclick={() => currentPage--}
            disabled={currentPage === 1 || loading || downloading}
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
          {startIndex + 1}–{Math.min(startIndex + itemsPerPage, result.count)}
          of {result.count}
        </p>

      </section>
    {/if}

  </div>
</main>

<style>
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

  .error {
    margin-top: 20px;
    padding: 15px;
    background: #fee;
    color: #900;
    border-radius: 6px;
  }

  .results {
    margin-top: 30px;
    padding-top: 25px;
    border-top: 1px solid #ddd;
  }

  code {
    word-break: break-all;
    font-size: 12px;
  }

  li {
    margin-bottom: 10px;
  }

  .gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 16px;
    margin-top: 25px;
  }

  .thumbnail {
    display: block;
    text-decoration: none;
    color: #333;
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 8px;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }

  .thumbnail:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .thumbnail img {
    display: block;
    width: 100%;
    height: 180px;
    object-fit: contain;
    background: white;
  }

  .thumbnail span {
    display: block;
    text-align: center;
    margin-top: 8px;
    font-size: 13px;
    font-weight: 600;
  }

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

  .download-status {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 15px;
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
</style>
