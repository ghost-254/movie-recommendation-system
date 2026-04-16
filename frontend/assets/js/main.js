import { searchMovies } from "./api.js";
import { escapeHtml, formatReleaseYear, getPosterUrl, truncateText } from "./utils.js";

const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const resultsContainer = document.getElementById("results");
const statusMessage = document.getElementById("status-message");

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("status-error", isError);
}

function renderResults(movies) {
  resultsContainer.innerHTML = "";

  if (!movies.length) {
    resultsContainer.innerHTML = "<p class='muted'>No results found. Try another movie title.</p>";
    return;
  }

  const cardsHtml = movies
    .map((movie) => {
      const title = escapeHtml(movie.title || "Untitled movie");
      const releaseYear = formatReleaseYear(movie.release_date);
      const overview = escapeHtml(truncateText(movie.overview || "No overview available.", 170));
      const posterUrl = getPosterUrl(movie.poster_path);
      const voteAverage =
        typeof movie.vote_average === "number" ? movie.vote_average.toFixed(1) : "Not available";

      return `
        <article class="movie-card">
          <img src="${posterUrl}" alt="Poster for ${title}" loading="lazy" />
          <div class="movie-card-body">
            <h3>${title}</h3>
            <p class="meta">${releaseYear} | Rating: ${voteAverage}</p>
            <p>${overview}</p>
            <a class="button-link" href="movie.html?id=${movie.id}">View Analysis</a>
          </div>
        </article>
      `;
    })
    .join("");

  resultsContainer.innerHTML = cardsHtml;
}

async function handleSearch(event) {
  event.preventDefault();
  const query = searchInput.value.trim();

  if (!query) {
    setStatus("Please enter a movie title before searching.", true);
    return;
  }

  setStatus("Searching TMDb...");
  resultsContainer.innerHTML = "";

  try {
    const response = await searchMovies(query);
    const movies = Array.isArray(response.results) ? response.results : [];
    setStatus(`Found ${movies.length} result(s) for "${query}".`);
    renderResults(movies);
  } catch (error) {
    setStatus(error.message, true);
    resultsContainer.innerHTML = "";
  }
}

searchForm.addEventListener("submit", handleSearch);
