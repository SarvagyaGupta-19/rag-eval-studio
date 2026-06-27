import React, { useEffect, useState } from 'react';

export type Mood = "watching" | "friendly" | "confusion" | "joy" | "upset" | "sly" | "angry";

interface ChatbotCharacterProps {
  mood?: Mood;
  className?: string;
}

export function ChatbotCharacter({ mood = "watching", className = "" }: ChatbotCharacterProps) {
  const [blink, setBlink] = useState(false);

  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  // Random blinking effect
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlink(true);
      setTimeout(() => setBlink(false), 150); // Blink duration
    }, 4000 + Math.random() * 3000); // Random interval between 4s and 7s

    return () => clearInterval(blinkInterval);
  }, []);

  // Mouse tracking effect
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // Normalize mouse position to [-1, 1] based on window center
      const x = (e.clientX / window.innerWidth) * 2 - 1;
      const y = (e.clientY / window.innerHeight) * 2 - 1;
      setMousePos({ x, y });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const getEyeStyles = () => {
    let pupilX = 0;
    let pupilY = 0;
    let eyeScaleY = 1;
    let eyeScaleX = 1;
    let eyeRotL = 0;
    let eyeRotR = 0;

    switch (mood) {
      case "confusion":
        pupilX = -4;
        pupilY = 0;
        eyeScaleY = 0.8;
        break;
      case "sly":
        pupilX = 6;
        pupilY = -2;
        eyeScaleY = 0.7;
        break;
      case "upset":
        pupilX = 0;
        pupilY = 4;
        eyeScaleY = 0.6;
        eyeRotL = 10;
        eyeRotR = -10;
        break;
      case "joy":
        pupilX = 0;
        pupilY = -3;
        eyeScaleY = 0.4;
        eyeScaleX = 1.2;
        break;
      case "angry":
        pupilX = 0;
        pupilY = -2;
        eyeScaleY = 0.7;
        eyeRotL = 25;
        eyeRotR = -25;
        break;
      case "friendly":
        pupilX = 0;
        pupilY = 0;
        eyeScaleY = 0.8;
        break;
      case "watching":
      default:
        // Track the mouse cursor
        pupilX = mousePos.x * 8;
        pupilY = mousePos.y * 8;
        break;
    }

    if (blink) {
      eyeScaleY = 0.1;
      eyeScaleX = 1.1;
    }

    return { pupilX, pupilY, eyeScaleX, eyeScaleY, eyeRotL, eyeRotR };
  };

  const { pupilX, pupilY, eyeScaleX, eyeScaleY, eyeRotL, eyeRotR } = getEyeStyles();

  return (
    <div className={`relative flex items-center justify-center ${className}`} style={{ animation: "orb-float 4s ease-in-out infinite" }}>
      
      {/* Outer Glow behind the SVG */}
      <div className="absolute inset-[15%] rounded-full bg-gradient-to-tr from-cyan-500 via-purple-600 to-fuchsia-500 opacity-40 blur-[25px] animate-pulse"></div>

      <svg viewBox="0 0 100 100" className="w-full h-full relative z-10">
        <defs>
          <linearGradient id="neon-border" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#38bdf8" /> {/* cyan */}
            <stop offset="50%" stopColor="#a855f7" /> {/* purple */}
            <stop offset="100%" stopColor="#e879f9" /> {/* fuchsia */}
          </linearGradient>
          <radialGradient id="glass-inner" cx="40%" cy="40%" r="60%">
            <stop offset="0%" stopColor="rgba(40, 20, 60, 0.4)" />
            <stop offset="100%" stopColor="rgba(10, 5, 20, 0.9)" />
          </radialGradient>
        </defs>

        {/* Particles */}
        <circle cx="15" cy="30" r="1.5" fill="#38bdf8" className="animate-pulse" style={{ animationDuration: '2s' }} />
        <circle cx="85" cy="20" r="1" fill="#e879f9" className="animate-ping" style={{ animationDuration: '3s' }} />
        <circle cx="20" cy="75" r="1" fill="#a855f7" className="animate-pulse" style={{ animationDuration: '4s' }} />
        <circle cx="80" cy="70" r="1.5" fill="#38bdf8" className="animate-ping" style={{ animationDuration: '2.5s' }} />
        <circle cx="50" cy="10" r="1" fill="#ffffff" className="animate-pulse" style={{ animationDuration: '1.5s' }} />

        {/* Orb Body */}
        <circle 
          cx="50" 
          cy="50" 
          r="36" 
          fill="url(#glass-inner)" 
          stroke="url(#neon-border)"
          strokeWidth="4"
          className="transition-all duration-500 ease-in-out hover:stroke-[5px]"
        />

        {/* Left Pill Eye */}
        <g style={{ 
            transform: `translate(${pupilX}px, ${pupilY}px) scale(${eyeScaleX}, ${eyeScaleY}) rotate(${eyeRotL}deg)`, 
            transformOrigin: '38px 50px', 
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)' 
        }}>
          <rect x="34" y="38" width="8" height="24" rx="4" fill="#ffffff" className="drop-shadow-[0_0_8px_rgba(255,255,255,0.6)]" />
        </g>

        {/* Right Pill Eye */}
        <g style={{ 
            transform: `translate(${pupilX}px, ${pupilY}px) scale(${eyeScaleX}, ${eyeScaleY}) rotate(${eyeRotR}deg)`, 
            transformOrigin: '62px 50px', 
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)' 
        }}>
          <rect x="58" y="38" width="8" height="24" rx="4" fill="#ffffff" className="drop-shadow-[0_0_8px_rgba(255,255,255,0.6)]" />
        </g>

        {/* Glossy Highlight for Glass effect */}
        <path d="M22,35 C28,18 45,12 60,18 C45,22 30,28 22,35 Z" fill="rgba(255,255,255,0.15)" />

      </svg>
      
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes orb-float {
          0%, 100% { transform: translateY(0px) scale(1); }
          50% { transform: translateY(-10px) scale(1.02); }
        }
      `}} />
    </div>
  );
}
