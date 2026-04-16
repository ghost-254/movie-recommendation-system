const FALLBACK_POSTER = `data:image/svg+xml,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" width="342" height="513" viewBox="0 0 342 513">
    <rect width="342" height="513" fill="#e6ecf5"/>
    <rect x="32" y="70" width="278" height="373" rx="10" fill="#d1dbea"/>
    <text x="171" y="248" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="24" fill="#3f4e67">No Poster</text>
  </svg>`
)}`;

export function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

export function formatReleaseYear(releaseDate) {
  if (!releaseDate) {
    return "Unknown";
  }

  const year = String(releaseDate).slice(0, 4);
  return year || "Unknown";
}

export function formatDateTime(dateText) {
  if (!dateText) {
    return "Unknown date";
  }

  const parsed = new Date(dateText);
  if (Number.isNaN(parsed.getTime())) {
    return "Unknown date";
  }

  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function truncateText(text, maxLength = 180) {
  if (typeof text !== "string" || text.length <= maxLength) {
    return text || "";
  }

  return `${text.slice(0, maxLength).trim()}...`;
}

export function escapeHtml(value) {
  const text = String(value ?? "");
  const replacements = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  return text.replace(/[&<>"']/g, (char) => replacements[char]);
}

export function getPosterUrl(posterPath, width = "w342") {
  if (!posterPath) {
    return FALLBACK_POSTER;
  }
  return `https://image.tmdb.org/t/p/${width}${posterPath}`;
}

export function formatSentiment(label) {
  if (!label) {
    return "Unknown";
  }
  return label
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
