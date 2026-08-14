import { useState } from 'react';

const themeSuggestions = [
  { id: 'fantasy', label: 'Fantasy Kingdom', icon: '🏰', description: 'Dragons, magic, and ancient realms' },
  { id: 'cyberpunk', label: 'Cyberpunk City', icon: '🌆', description: 'Neon streets, hackers, and megacorps' },
  { id: 'mystery', label: 'Detective Mystery', icon: '🔍', description: 'Crime, clues, and noir atmosphere' },
  { id: 'space', label: 'Space Survival', icon: '🚀', description: 'Starships, aliens, and the void' },
  { id: 'horror', label: 'Haunted Mansion', icon: '👻', description: 'Ghosts, secrets, and dread' },
  { id: 'post-apocalyptic', label: 'Wasteland', icon: '☢️', description: 'Survival, scavengers, and ruins' },
  { id: 'pirate', label: 'Pirate Adventure', icon: '🏴‍☠️', description: 'High seas, treasure, and betrayal' },
  { id: 'superhero', label: 'Superhero Origin', icon: '⚡', description: 'Powers, villains, and responsibility' },
];

const features = [
  { icon: '🎭', label: 'Branching Narrative' },
  { icon: '🧠', label: 'AI-Powered Choices' },
  { icon: '🎯', label: 'Meaningful Consequences' },
  { icon: '🏁', label: 'Multiple Endings' },
];

function ThemeInput({ onStart }) {
  const [theme, setTheme] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = theme.trim();
    
    if (!trimmed) {
      setError('Please enter a theme for your adventure');
      return;
    }
    
    if (trimmed.length < 3) {
      setError('Theme must be at least 3 characters');
      return;
    }
    
    setError('');
    setIsLoading(true);
    
    try {
      await onStart(trimmed);
    } catch {
      setError('Failed to start adventure. Please try again.');
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setTheme(suggestion.label);
    setError('');
  };

  const handleInputChange = (e) => {
    setTheme(e.target.value);
    if (error) setError('');
  };

  return (
    <div className="start-screen" role="main">
      <article className="card card-glow">
        <header className="start-header">
          <div className="start-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <h1 className="start-title">CREATE YOUR OWN ADVENTURE</h1>
          <p className="start-tagline">
            Every decision changes the story. Choose a world, make your choices, shape your ending.
          </p>
          
          <div className="start-features" role="list" aria-label="Game features">
            {features.map((feature, index) => (
              <span key={index} className="feature-pill" role="listitem">
                <span aria-hidden="true">{feature.icon}</span>
                <span>{feature.label}</span>
              </span>
            ))}
          </div>
        </header>

        <form className="theme-input-form" onSubmit={handleSubmit} noValidate>
          <div className="input-group">
            <label htmlFor="theme-input" className="input-label">
              What world will you explore?
            </label>
            <input
              id="theme-input"
              type="text"
              className={`input-field ${error ? 'error' : ''}`}
              placeholder="e.g., A detective investigating a murder in Mumbai"
              value={theme}
              onChange={handleInputChange}
              onFocus={() => setError('')}
              disabled={isLoading}
              aria-describedby={error ? 'theme-error' : undefined}
              aria-invalid={!!error}
              autoComplete="off"
              autoFocus
            />
            {error && (
              <p id="theme-error" className="input-error" role="alert">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                {error}
              </p>
            )}
          </div>

          <button 
            type="submit" 
            className="btn btn-primary btn-lg" 
            style={{ width: '100%' }}
            disabled={isLoading || !theme.trim()}
            aria-busy={isLoading}
          >
            {isLoading ? (
              <>
                <svg className="animate-spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <circle cx="12" cy="12" r="10" strokeOpacity="0.25"/>
                  <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/>
                </svg>
                Generating your adventure...
              </>
            ) : (
              'Begin Adventure'
            )}
          </button>
        </form>

        <section className="theme-suggestions" aria-labelledby="suggestions-heading">
          <span id="suggestions-heading" className="suggestions-label">Or choose a suggested theme:</span>
          <div className="suggestions-grid" role="list">
            {themeSuggestions.map((suggestion) => (
              <button
                key={suggestion.id}
                type="button"
                className="suggestion-btn"
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={isLoading}
                role="listitem"
                aria-label={`${suggestion.label}: ${suggestion.description}`}
              >
                <span aria-hidden="true" style={{ fontSize: '1.125rem' }}>{suggestion.icon}</span>
                <span>{suggestion.label}</span>
              </button>
            ))}
          </div>
        </section>

        <footer className="start-footer">
          <p>
            Powered by AI • Your choices create a unique story every time
          </p>
        </footer>
      </article>
    </div>
  );
}

export default ThemeInput;
