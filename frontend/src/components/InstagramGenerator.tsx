import React, { useRef, useCallback, useState } from 'react';
import { toJpeg } from 'html-to-image';

// --- Definice Typů ---
interface EventDetail {
  title: string;
  date: string;
  time: string;
  place: string;
  venue?: string; // Přidané pole pro název klubu
  price: string | null;
  description: string;
  image_url: string;
}

interface PostProps {
  event: EventDetail;
}

// --- Komponenta pro jeden post ---
const InstagramPost: React.FC<PostProps> = ({ event }) => {
  const postRef = useRef<HTMLDivElement>(null);

  // Pomocná konstanta pro CORS proxy
  const proxiedImageUrl = event.image_url
    ? `http://localhost:3001/proxy-image?url=${encodeURIComponent(event.image_url)}`
    : null;

  const exportImage = useCallback(() => {
    if (postRef.current === null) return;

    // Export v rozlišení 1080x1080
    // Pro export obrázků z cizích domén je NUTNÉ mít crossOrigin="anonymous" na <img>
    // a server musí posílat CORS hlavičky.
    toJpeg(postRef.current, {
      quality: 0.95,
      canvasWidth: 1080,
      canvasHeight: 1080,
      cacheBust: true, // Pomáhá obcházet cache u některých CORS problémů
    })
      .then((dataUrl) => {
        const link = document.createElement('a');
        link.download = `post-${event.title.substring(0, 15).replace(/\s+/g, '-')}.jpg`;
        link.href = dataUrl;
        link.click();
      })
      .catch((err) => {
        console.error('Export selhal:', err);
        alert('Export se nezdařil. Často je to kvůli CORS restrikcím na obrázky z jiných webů.');
      });
  }, [event.title]);

  return (
    <div style={{ marginBottom: '60px', textAlign: 'center' }}>
      <div style={{ transform: 'scale(0.5)', transformOrigin: 'top center', height: '540px', width: '540px', boxShadow: '0 20px 50px rgba(0,0,0,0.5)' }}>
        {/* Container pro export - 1080x1080 */}
        <div
            ref={postRef}
            style={{
            width: '1080px',
            height: '1080px',
            position: 'relative',
            overflow: 'hidden',
            backgroundColor: '#000',
            fontFamily: '"Inter", "Helvetica", "Arial", sans-serif',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
            textAlign: 'left',
            color: 'white',
            }}
        >
            {/* Podkladový obrázek */}
            {proxiedImageUrl ? (
                <img
                    src={proxiedImageUrl}
                    alt={event.title}
                    crossOrigin="anonymous"
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        zIndex: 1,
                    }}
                    onError={(e) => {
                        console.error("Image load failed through proxy:", event.image_url);
                        // Fallback color if image fails
                        (e.target as HTMLImageElement).style.display = 'none';
                    }}
                />
            ) : (
                <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: '#1e293b', zIndex: 1 }} />
            )}

            {/* Gradientní vrstva pro čitelnost textu */}
            <div
            style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                height: '60%',
                background: 'linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.5) 50%, transparent 100%)',
                zIndex: 2,
            }}
            />

            {/* Textový obsah */}
            <div style={{ position: 'relative', zIndex: 3, padding: '60px' }}>

            {/* Badge s časem */}
            <div style={{
                display: 'inline-block',
                backgroundColor: '#FF3B30',
                color: 'white',
                padding: '8px 20px',
                fontSize: '28px',
                fontWeight: 800,
                borderRadius: '50px',
                marginBottom: '20px',
                textTransform: 'uppercase'
            }}>
                DNES | {event.time || "20:00"}
            </div>

            {/* Název akce - Maximální důraz */}
            <h1 style={{
                fontSize: '72px',
                lineHeight: 1.1,
                fontWeight: 900,
                margin: '0 0 20px 0',
                textTransform: 'uppercase',
                letterSpacing: '-1px',
                wordWrap: 'break-word',
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden'
            }}>
                {event.title || "Název akce"}
            </h1>

            {/* Místo konání */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                fontSize: '36px',
                fontWeight: 500,
                color: '#E5E5E5',
            }}>
                <span style={{ marginRight: '15px' }}>📍</span>
                {event.venue || event.place || "Brno"}
            </div>
            </div>
        </div>
      </div>

      {/* Ovládací tlačítko (neexportuje se) */}
      <button
        onClick={exportImage}
        className="fetch-all-btn"
        style={{
          marginTop: '20px',
          padding: '12px 24px',
          background: 'var(--primary)'
        }}
      >
        Stáhnout JPEG (1080x1080)
      </button>
    </div>
  );
};

// --- Hlavní stránka s iterací přes JSON ---
export const InstagramGeneratorPage: React.FC<{ data: Record<string, any[]> }> = ({ data }) => {
  const [jsonInput, setJsonInput] = useState("");
  const [manualData, setManualData] = useState<Record<string, any[]> | null>(null);

  const displayData = manualData || data;
  const allEvents = Object.entries(displayData).flatMap(([venueName, events]) =>
    Array.isArray(events) ? events.map(event => ({ ...event, venue: venueName })) : []
  ).filter(e => e.title); // Filter out raw scraped items without titles

  const handleApplyJson = () => {
    try {
      const parsed = JSON.parse(jsonInput);
      setManualData(parsed);
    } catch (e) {
      alert("Invalid JSON format. Please paste JSON from output.json");
    }
  };

  return (
    <div style={{ padding: '20px', backgroundColor: '#0f172a', minHeight: '100vh', color: 'white' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '20px' }}>Instagram Content Generator</h1>

      <div style={{ maxWidth: '800px', margin: '0 auto 40px auto', background: 'rgba(255,255,255,0.05)', padding: '20px', borderRadius: '12px' }}>
        <h3 style={{ marginBottom: '10px' }}>Paste processed JSON (e.g. from output.json)</h3>
        <textarea
            style={{ width: '100%', height: '100px', marginBottom: '10px', background: '#1e293b', color: 'white' }}
            placeholder='{ "Venue": [ { "title": "...", "image_url": "..." } ] }'
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
        />
        <button onClick={handleApplyJson} className="copy-btn" style={{ background: 'var(--primary)' }}>Apply JSON Data</button>
        {manualData && <button onClick={() => setManualData(null)} style={{ marginLeft: '10px', background: 'transparent', border: '1px solid #ef4444', color: '#ef4444', padding: '0.4rem 1rem', borderRadius: '0.4rem', cursor: 'pointer' }}>Clear Manual Data</button>}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {allEvents.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <p>No events found to generate posts.</p>
                <p>Please paste processed results from <strong>output.json</strong> above.</p>
            </div>
        ) : (
            allEvents.map((event, idx) => (
                <InstagramPost key={idx} event={event} />
            ))
        )}
      </div>
    </div>
  );
};
