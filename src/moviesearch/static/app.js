document.addEventListener('DOMContentLoaded', () => {
    const advancedSearchForm = document.getElementById('advanced-search-form');
    const recommendationForm = document.getElementById('recommendation-form');
    const resultsContainer = document.getElementById('results');
  
    // Advanced Search
    advancedSearchForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const searchData = {
        genres: Array.from(document.querySelectorAll('input[name="genre"]:checked'))
          .map(el => el.value),
        min_year: document.getElementById('min-year').value || null,
        max_year: document.getElementById('max-year').value || null,
        min_rating: parseFloat(document.getElementById('min-rating').value) || null,
        sort_by: document.getElementById('sort-by').value,
        limit: parseInt(document.getElementById('result-limit').value) || 10
      };
  
      try {
        const response = await fetch('/advanced_search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(searchData)
        });
  
        const result = await response.json();
        renderResults(result.results);
      } catch (error) {
        console.error('Advanced Search Error:', error);
      }
    });
  
    // Recommendations
    recommendationForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const movieTitle = document.getElementById('recommendation-input').value.trim();
  
      try {
        const response = await fetch('/recommendations', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ title: movieTitle })
        });
  
        const recommendations = await response.json();
        renderRecommendations(recommendations);
      } catch (error) {
        console.error('Recommendations Error:', error);
      }
    });
  
    function renderResults(results) {
      resultsContainer.innerHTML = results.map(movie => `
        <div class="card mb-3">
          <div class="card-body">
            <h5 class="card-title">${movie.title}</h5>
            <p class="card-text">${movie.description}</p>
            <p class="text-muted">
              Genre: ${movie.genre} | 
              Rating: ${movie.rating} | 
              Year: ${movie.release_year}
            </p>
          </div>
        </div>
      `).join('');
    }
  
    function renderRecommendations(recommendations) {
      resultsContainer.innerHTML = `
        <h3>Recommended Movies</h3>
        ${recommendations.map(movie => `
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">${movie.title}</h5>
              <p class="card-text">${movie.description}</p>
              <p class="text-muted">
                Genre: ${movie.genre} | 
                Similarity Score: ${movie.similarity_score.toFixed(2)}
              </p>
            </div>
          </div>
        `).join('')}
      `;
    }
  });


document.addEventListener('DOMContentLoaded', () => {
    const advancedSearchForm = document.getElementById('advanced-search-form');
    const recommendationForm = document.getElementById('recommendation-form');
    const regularSearchForm = document.getElementById('regular-search-form');
    const resultsContainer = document.getElementById('results');
    
    // Add Movie Chat functionality
    const movieChatForm = document.getElementById('movie-chat-form');
    const movieChatInput = document.getElementById('movie-chat-input');

    if (movieChatForm) {
        movieChatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const chatQuery = movieChatInput.value.trim();

            if (!chatQuery) return;

            try {
                const response = await fetch('/movie_chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: chatQuery })
                });

                const result = await response.json();

                // If there's an error, display it
                if (result.error) {
                    resultsContainer.innerHTML = `
                        <div class="alert alert-danger">
                            Error: ${result.error}
                        </div>
                    `;
                    return;
                }

                // Render the AI response and any context movies
                renderMovieChat(result.response, result.context_movies);
            } catch (error) {
                console.error('Movie Chat Error:', error);
                resultsContainer.innerHTML = `
                    <div class="alert alert-danger">
                        Error performing movie chat: ${error.message}
                    </div>
                `;
            }
        });
    }

    function renderMovieChat(response, contextMovies) {
        // Clear previous results
        resultsContainer.innerHTML = `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">Movie Assistant Response</h5>
                    <p class="card-text">${response}</p>
                </div>
            </div>
        `;

        // If there are context movies, render them
        if (contextMovies && contextMovies.length > 0) {
            resultsContainer.innerHTML += `
                <div class="card mb-3">
                    <div class="card-header">
                        Relevant Movies
                    </div>
                    <div class="card-body">
                        ${contextMovies.map(movie => `
                            <div class="mb-2">
                                <h6>${movie.title}</h6>
                                <p class="text-muted">
                                    ${movie.description} | 
                                    Genre: ${movie.genre} | 
                                    Year: ${movie.release_year} | 
                                    Rating: ${movie.rating}
                                </p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    }

    // Regular Search
    if (regularSearchForm) {
        regularSearchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const searchQuery = document.getElementById('search-input').value.trim();
        
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: searchQuery })
                });
        
                const results = await response.json();
                renderResults(results);
            } catch (error) {
                console.error('Search Error:', error);
                resultsContainer.innerHTML = `<div class="alert alert-danger">Error performing search: ${error.message}</div>`;
            }
        });
    }
  
    // Advanced Search
    if (advancedSearchForm) {
        advancedSearchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const searchData = {
                genres: Array.from(document.querySelectorAll('input[name="genre"]:checked'))
                    .map(el => el.value),
                min_year: document.getElementById('min-year').value || null,
                max_year: document.getElementById('max-year').value || null,
                min_rating: parseFloat(document.getElementById('min-rating').value) || null,
                sort_by: document.getElementById('sort-by').value,
                limit: parseInt(document.getElementById('result-limit').value) || 10
            };
    
            try {
                const response = await fetch('/advanced_search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(searchData)
                });
    
                const result = await response.json();
                renderResults(result.results);
            } catch (error) {
                console.error('Advanced Search Error:', error);
                resultsContainer.innerHTML = `<div class="alert alert-danger">Error performing advanced search: ${error.message}</div>`;
            }
        });
    }
  
    // Recommendations
    if (recommendationForm) {
        recommendationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const movieTitle = document.getElementById('recommendation-input').value.trim();
    
            try {
                const response = await fetch('/recommendations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ title: movieTitle })
                });
    
                const recommendations = await response.json();
                renderRecommendations(recommendations);
            } catch (error) {
                console.error('Recommendations Error:', error);
                resultsContainer.innerHTML = `<div class="alert alert-danger">Error getting recommendations: ${error.message}</div>`;
            }
        });
    }
  
    function renderResults(results) {
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<div class="alert alert-info">No results found.</div>';
            return;
        }
        
        resultsContainer.innerHTML = results.map(movie => `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${movie.title}</h5>
                    <p class="card-text">${movie.description}</p>
                    <p class="text-muted">
                        Genre: ${movie.genre} | 
                        Rating: ${movie.rating} | 
                        Year: ${movie.release_year}
                        ${movie.score ? ` | Relevance Score: ${movie.score.toFixed(2)}` : ''}
                    </p>
                </div>
            </div>
        `).join('');
    }
  
    function renderRecommendations(recommendations) {
        if (!recommendations || recommendations.length === 0) {
            resultsContainer.innerHTML = '<div class="alert alert-info">No recommendations found.</div>';
            return;
        }
        
        resultsContainer.innerHTML = `
            <h3>Recommended Movies</h3>
            ${recommendations.map(movie => `
                <div class="card mb-3">
                    <div class="card-body">
                        <h5 class="card-title">${movie.title}</h5>
                        <p class="card-text">${movie.description}</p>
                        <p class="text-muted">
                            Genre: ${movie.genre} | 
                            Similarity Score: ${movie.similarity_score ? movie.similarity_score.toFixed(2) : 'N/A'}
                        </p>
                    </div>
                </div>
            `).join('')}
        `;
    }
});


