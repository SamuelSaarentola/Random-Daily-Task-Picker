<style>
     {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        overflow: hidden;
        background: #000;
    }
    canvas {
        display: block;
        width: 100%;
        height: 100vh;
    }
    .content {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 10;
        text-align: center;
        color: white;
        pointer-events: none;
    }
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 40px rgba(255, 255, 255, 0.4)) drop-shadow(0 0 80px rgba(138, 43, 226, 0.3));
        animation: glowPulse 3s ease-in-out infinite alternate;
    }
    @keyframes glowPulse {
        from {
            filter: drop-shadow(0 0 40px rgba(255, 255, 255, 0.4)) drop-shadow(0 0 80px rgba(138, 43, 226, 0.3));
        }
        to {
            filter: drop-shadow(0 0 60px rgba(255, 255, 255, 0.6)) drop-shadow(0 0 120px rgba(0, 191, 255, 0.4));
        }
    }
    
    .buttons {
        display: flex;
        justify-content: center;
        gap: 24px;
        margin-top: 40px;
        pointer-events: auto;
    }
    .glass-button {
        position: relative;
        padding: 16px 40px;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        color: #fff;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
        border: 1.5px solid transparent;
        border-radius: 40px;
        backdrop-filter: blur(30px);
        box-shadow:
            0 8px 32px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.2),
            inset 0 -1px 0 rgba(255, 255, 255, 0.05);
        overflow: hidden;
        cursor: pointer;
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        pointer-events: auto;
    }
   
    .glass-button::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 40px;
        padding: 1.5px;
        background: linear-gradient(135deg,
            rgba(255, 255, 255, 0.4) 0%,
            rgba(138, 43, 226, 0.4) 25%,
            rgba(0, 191, 255, 0.4) 50%,
            rgba(255, 105, 180, 0.4) 75%,
            rgba(255, 255, 255, 0.4) 100%);
        background-size: 200% 200%;
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        animation: borderFlow 3s linear infinite;
        opacity: 0.6;
        transition: opacity 0.5s ease;
    }
    @keyframes borderFlow {
        0% { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }
    .glass-button::after {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 40px;
        background: radial-gradient(circle at var(--x, 50%) var(--y, 50%),
            rgba(255, 255, 255, 0.2) 0%,
            transparent 50%);
        opacity: 0;
        transition: opacity 0.5s ease;
    }
    .glass-button:hover {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
        box-shadow:
            0 12px 48px rgba(138, 43, 226, 0.3),
            0 0 80px rgba(0, 191, 255, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.3),
            inset 0 -1px 0 rgba(255, 255, 255, 0.1);
        transform: translateY(-3px) scale(1.02);
    }
    .glass-button:hover::before {
        opacity: 1;
        animation-duration: 2s;
    }
    .glass-button:hover::after {
        opacity: 1;
    }
    .glass-button:active {
        transform: translateY(-1px) scale(0.98);
        box-shadow:
            0 6px 24px rgba(138, 43, 226, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }
    .glass-button .shimmer {
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255, 255, 255, 0.1) 45%,
            rgba(255, 255, 255, 0.3) 50%,
            rgba(255, 255, 255, 0.1) 55%,
            transparent 100%
        );
        transform: rotate(30deg);
        animation: shimmer 3s infinite;
        pointer-events: none;
    }
    @keyframes shimmer {
        0% { transform: translateX(-100%) rotate(30deg); }
        100% { transform: translateX(100%) rotate(30deg); }
    }
    .glass-button:hover .shimmer {
        animation-duration: 1.5s;
    }
    .glass-button span {
        position: relative;
        z-index: 1;
    }
</style>
<canvas id="canvas"></canvas>
<div class="content">
    <div class="buttons">
        <button class="glass-button">
            <span class="shimmer"></span>
            <span>Discover</span>
        </button>
        <button class="glass-button">
            <span class="shimmer"></span>
            <span>Join Now</span>
        </button>
    </div>
</div>
