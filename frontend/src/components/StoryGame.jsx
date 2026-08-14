import { useState, useEffect, useCallback, useMemo } from 'react';

function StoryGame({ story, onNewStory, onMakeChoice }) {
  const [currentNodeId, setCurrentNodeId] = useState(null);
  const [isEnding, setIsEnding] = useState(false);
  const [isWinningEnding, setIsWinningEnding] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [storyData, setStoryData] = useState(story);

  // Memoize current node to avoid recalculating
  const currentNodeMemo = useMemo(() => {
    if (!currentNodeId || !storyData?.all_nodes) return null;
    return storyData.all_nodes[currentNodeId];
  }, [currentNodeId, storyData?.all_nodes]);

  // Initialize with root node when storyData changes
  useEffect(() => {
    if (storyData && storyData.root_nodes) {
      setCurrentNodeId(storyData.root_nodes.id);
    }
  }, [storyData]);

  // Load node data when currentNodeId or storyData changes
  useEffect(() => {
    if (currentNodeMemo) {
      setIsEnding(currentNodeMemo.is_ending);
      setIsWinningEnding(currentNodeMemo.is_winning_ending);
      setError('');
    }
  }, [currentNodeMemo]);

  const handleChoice = useCallback(async (optionText, optionNodeId) => {
    if (!storyData || isLoading) return;

    setIsLoading(true);
    setError('');

    try {
      // If option already has a node_id, navigate directly
      if (optionNodeId) {
        setCurrentNodeId(optionNodeId);
        setIsLoading(false);
        return;
      }

      // Otherwise, call API to generate next node
      const response = await onMakeChoice(storyData.id, currentNodeId, optionText);
      
      // Update story data with new nodes from response
      if (response.story && response.story.all_nodes) {
        setStoryData(prev => ({
          ...prev,
          all_nodes: { ...prev.all_nodes, ...response.story.all_nodes },
          current_state: response.story.current_state,
          max_depth: response.story.max_depth,
        }));
      }

      // Navigate to the new node
      if (response.current_node) {
        setCurrentNodeId(response.current_node.id);
      }
    } catch (err) {
      setError('Failed to make choice. Please try again.');
      console.error('Choice error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [storyData, currentNodeId, onMakeChoice, isLoading]);

  const handleRestart = useCallback(() => {
    if (storyData && storyData.root_nodes) {
      setCurrentNodeId(storyData.root_nodes.id);
      setError('');
    }
  }, [storyData]);

  if (!storyData) {
    return null;
  }

  const theme = storyData.current_state?.theme || 'Adventure';

  return (
    <div className="game-screen" role="main">
      {/* Game Header */}
      <header className="game-header" role="banner">
        <div className="game-title-section">
          <div className="game-title-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div className="game-title-text">
            <h1>{storyData.title || 'Untitled Adventure'}</h1>
            <span className="story-theme">{theme}</span>
          </div>
        </div>

        <div className="game-progress" role="status" aria-live="polite">
          <div className="progress-bar-container" aria-hidden="true">
            <div 
              className="progress-bar" 
              style={{ width: `${Math.min((currentNodeMemo?.depth || 0) * 20, 100)}%` }}
            />
          </div>
          <span className="progress-text">
            Chapter {currentNodeMemo?.depth ? currentNodeMemo.depth + 1 : 1}
          </span>
        </div>

        <div className="game-actions">
          <button 
            className="btn btn-ghost btn-sm btn-icon"
            onClick={handleRestart}
            disabled={isLoading}
            aria-label="Restart story"
            title="Restart"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
              <path d="M3 3v5h5"/>
            </svg>
          </button>
          {onNewStory && (
            <button 
              className="btn btn-secondary btn-sm"
              onClick={onNewStory}
              disabled={isLoading}
            >
              New Adventure
            </button>
          )}
        </div>
      </header>

      {/* Error Message */}
      {error && (
        <div className="card" style={{ 
          borderColor: 'var(--accent-danger)', 
          background: 'rgba(239, 68, 68, 0.1)',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          animation: 'fadeIn 0.3s ease'
        }} role="alert">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" style={{ color: 'var(--accent-danger)', flexShrink: 0 }}>
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span style={{ color: 'var(--text-secondary)' }}>{error}</span>
          <button 
            onClick={() => setError('')}
            className="btn btn-ghost btn-sm"
            style={{ marginLeft: 'auto', padding: '0.25rem' }}
            aria-label="Dismiss error"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      )}

      {/* Story Card */}
      <article className="story-card card card-glow" role="article" aria-label="Story content">
        <div className="story-content">
          {currentNodeMemo ? (
            <>
              {!isEnding ? (
                <>
                  {currentNodeMemo.content.split('\n\n').map((paragraph, index) => (
                    <p key={index} className="story-paragraph">
                      {paragraph}
                    </p>
                  ))}
                </>
              ) : (
                <div className="story-ending">
                  <div 
                    className={`ending-icon ${isWinningEnding ? 'winning' : 'losing'}`}
                    aria-hidden="true"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      {isWinningEnding ? (
                        <>
                          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                          <polyline points="22 4 12 14.01 9 11.01"/>
                        </>
                      ) : (
                        <>
                          <circle cx="12" cy="12" r="10"/>
                          <line x1="15" y1="9" x2="9" y2="15"/>
                          <line x1="9" y1="9" x2="15" y2="15"/>
                        </>
                      )}
                    </svg>
                  </div>
                  <h2 className={`ending-title ${isWinningEnding ? 'winning' : 'losing'}`}>
                    {isWinningEnding ? 'Victory!' : 'Journey\'s End'}
                  </h2>
                  <p className="ending-description">
                    {isWinningEnding 
                      ? 'You have successfully completed your adventure. Your choices led to a triumphant conclusion.'
                      : 'Your adventure has come to an end. Perhaps another path would have led to a different outcome.'}
                  </p>
                </div>
              )}

              {/* Choices Area */}
              {!isEnding && currentNodeMemo.options && currentNodeMemo.options.length > 0 && (
                <div className="choices-area" role="region" aria-label="Available choices">
                  <div className="choices-label">
                    Choose your path
                  </div>
                  <div className="choices-grid">
                    {currentNodeMemo.options.map((option, index) => (
                      <button
                        key={option.node_id || index}
                        className="choice-btn"
                        onClick={() => handleChoice(option.text, option.node_id)}
                        disabled={isLoading}
                        aria-busy={isLoading}
                      >
                        <span className="choice-number">{index + 1}</span>
                        <div>
                          <span className="choice-text">{option.text}</span>
                          {option.consequence && (
                            <span className="choice-consequence">{option.consequence}</span>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Game Controls at bottom of story card */}
              <div className="game-controls">
                <button 
                  className="btn btn-secondary"
                  onClick={handleRestart}
                  disabled={isLoading}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                    <path d="M3 3v5h5"/>
                  </svg>
                  Restart Chapter
                </button>
                {onNewStory && (
                  <button 
                    className="btn btn-primary"
                    onClick={onNewStory}
                    disabled={isLoading}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                      <path d="M2 17l10 5 10-5"/>
                      <path d="M2 12l10 5 10-5"/>
                    </svg>
                    New Adventure
                  </button>
                )}
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
              <p>Loading story...</p>
            </div>
          )}
        </div>
      </article>
    </div>
  );
}

export default StoryGame;