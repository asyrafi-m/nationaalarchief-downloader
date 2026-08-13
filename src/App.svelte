<script>
  let archiveUrl = ''
  let loading = false
  let error = ''
  let result = null

  let currentPage = 1
  const itemsPerPage = 20

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
          archive: result.archive,
          inventory: result.inventory,
          files: result.files
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

  error = ''
  loading = true

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

    const blob = await response.blob()

    const url = URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.href = url
    link.download = `${result.archive}_${result.inventory}.zip`

    document.body.appendChild(link)
    link.click()
    link.remove()

    URL.revokeObjectURL(url)

  } catch (err) {
    error = err.message
  } finally {
    loading = false
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
      disabled={loading}
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
      disabled={loading}
    >
      {loading ? 'Preparing download...' : 'Download entire bundle as ZIP'}
    </button>

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
    disabled={currentPage === 1}
  >
    ← Previous
  </button>

  <div class="page-numbers">
    {#each Array(totalPages) as _, i}
      <button
        class:active={currentPage === i + 1}
        onclick={() => currentPage = i + 1}
      >
        {i + 1}
      </button>
    {/each}
  </div>

  <button
    onclick={() => currentPage++}
    disabled={currentPage === totalPages}
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
</style>