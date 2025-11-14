import { useState } from 'react';
import './HelloWorld.css';

interface HelloWorldResponse {
  response: string;
}

export function HelloWorld() {
  const [serverResponse, setServerResponse] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleClick = async () => {
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/hello-world', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'Hello World!'
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: HelloWorldResponse = await response.json();
      setServerResponse(data.response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error communicating with backend:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="hello-world-container">
      <h2>Frontend-Backend Communication Test</h2>
      <button
        onClick={handleClick}
        disabled={isLoading}
        className="hello-world-button"
      >
        {isLoading ? 'Sending...' : 'Click me!'}
      </button>

      {serverResponse && (
        <div className="response-container">
          <h3>Server Response:</h3>
          <p className="server-response">{serverResponse}</p>
        </div>
      )}

      {error && (
        <div className="error-container">
          <p className="error-message">Error: {error}</p>
        </div>
      )}
    </div>
  );
}
