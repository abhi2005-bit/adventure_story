import { useEffect, useState } from 'react';

const loadingSteps = [
  { id: 'world', label: 'Crafting your world...', icon: '🌍' },
  { id: 'characters', label: 'Breathing life into characters...', icon: '👤' },
  { id: 'plot', label: 'Weaving the narrative...', icon: '📖' },
  { id: 'choices', label: 'Designing meaningful choices...', icon: '🎯' },
  { id: 'final', label: 'Finalizing your adventure...', icon: '✨' },
];

function LoadingStatus({ theme }) {
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState(new Set());

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep(prev => {
        if (prev < loadingSteps.length - 1) {
          setCompletedSteps(prevSet => new Set([...prevSet, loadingSteps[prev].id]));
          return prev + 1;
        }
        return prev;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loading-screen" role="status" aria-live="polite" aria-label="Generating story">
      <div className="loading-animation" aria-hidden="true">
        <div className="loading-ring" />
        <div className="loading-ring" />
        <div className="loading-ring" />
      </div>

      <h1 className="loading-title">Generating Your Adventure</h1>
      <p className="loading-subtitle">
        {theme ? `A ${theme} tale awaits...` : 'Crafting a unique story just for you...'}
      </p>

      <div className="loading-steps" role="list" aria-label="Generation progress">
        {loadingSteps.map((step, index) => {
          const isActive = index === activeStep;
          const isCompleted = completedSteps.has(step.id);
          
          return (
            <div
              key={step.id}
              className={`loading-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
              role="listitem"
              aria-current={isActive ? 'step' : undefined}
            >
              <div className="loading-step-icon" aria-hidden="true">
                {isCompleted ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                ) : (
                  <span style={{ fontSize: '1.125rem' }}>{step.icon}</span>
                )}
              </div>
              <span>{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default LoadingStatus;