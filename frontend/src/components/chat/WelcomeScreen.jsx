import React from 'react';
import { Orbit } from 'lucide-react';

/**
 * Welcome screen — Copilot/ChatGPT minimal style.
 * Just the heading and subtitle. Input bar is the composer at the bottom.
 * No upload zone, no cards, no chips on the welcome screen.
 */
export default function WelcomeScreen({ onAsk }) {
  return (
    <div className="welcome">
      <div className="welcome-brand">
        <div className="welcome-logo"><Orbit size={28} /></div>
        <h1 className="welcome-title">What can I help with?</h1>
        <p className="welcome-subtitle">
          Ask anything about your satellite imagery.
        </p>
      </div>
    </div>
  );
}
