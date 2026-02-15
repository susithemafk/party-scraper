import React, { useRef, useCallback, useState } from "react"
import { toJpeg } from "html-to-image"
import axios from "axios"
import styles from "./InstagramGenerator.module.css"

// --- Definice Typů ---
interface EventDetail {
    title: string
    date: string
    time: string
    place: string
    venue?: string // Přidané pole pro název klubu
    price: string | null
    description: string
    image_url: string
}

interface PostProps {
    event: EventDetail
}

// --- Komponenta pro jeden post ---
const InstagramPost: React.FC<PostProps> = ({ event }) => {
    const postRef = useRef<HTMLDivElement>(null)

    // Pomocná konstanta pro CORS proxy
    const proxiedImageUrl = event.image_url ? `http://localhost:3001/proxy-image?url=${encodeURIComponent(event.image_url)}` : null

    const exportImage = useCallback(() => {
        if (postRef.current === null) return

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
                const link = document.createElement("a")
                link.download = `post-${event.title.substring(0, 15).replace(/\s+/g, "-")}.jpg`
                link.href = dataUrl
                link.click()
            })
            .catch((err) => {
                console.error("Export selhal:", err)
                alert("Export se nezdařil. Často je to kvůli CORS restrikcím na obrázky z jiných webů.")
            })
    }, [event.title])

    return (
        <div className={styles.postContainer}>
            <div className={styles.previewScale}>
                {/* Container pro export - 1080x1080 */}
                <div ref={postRef} className={styles.exportCanvas}>
                    {/* Podkladový obrázek */}
                    {proxiedImageUrl ? (
                        <img
                            src={proxiedImageUrl}
                            alt={event.title}
                            crossOrigin="anonymous"
                            className={styles.backgroundImage}
                            onError={(e) => {
                                console.error("Image load failed through proxy:", event.image_url)
                                // Fallback color if image fails
                                ;(e.target as HTMLImageElement).style.display = "none"
                            }}
                        />
                    ) : (
                        <div className={styles.fallbackBackground} />
                    )}

                    {/* Místo konání */}
                    <div className={styles.locationContainer}>{event.venue || event.place || "Brno"}</div>

                    {/* Gradientní vrstva pro čitelnost textu */}
                    <div className={styles.gradientOverlay} />

                    {/* Textový obsah */}
                    <div className={styles.textContent}>
                        {/* Badge s časem */}
                        <div className={styles.timeBadgeContainer}>
                            <div className={styles.timeBadge}>DNES {event.time && `| ${event.time}`}</div>
							<div className={styles.locationBadge}>{event.venue || event.place || "Brno"}</div>
                        </div>

                        {/* Název akce - Maximální důraz */}
                        <h1 className={styles.actionTitle}>{event.title || "Název akce"}</h1>
                    </div>
                </div>
            </div>

            {/* Ovládací tlačítko (neexportuje se) */}
            <button onClick={exportImage} className={styles.downloadBtn}>
                Stáhnout JPEG (1080x1080)
            </button>
        </div>
    )
}

// --- Hlavní stránka s iterací přes JSON ---
export const InstagramGeneratorPage: React.FC<{ data: Record<string, any[]> }> = ({ data }) => {
    const [jsonInput, setJsonInput] = useState("")
    const [manualData, setManualData] = useState<Record<string, any[]> | null>(null)

    const displayData = manualData || data
    const allEvents = Object.entries(displayData)
        .flatMap(([venueName, events]) => (Array.isArray(events) ? events.map((event) => ({ ...event, venue: venueName })) : []))
        .filter((e) => e.title) // Filter out raw scraped items without titles

    const handleApplyJson = () => {
        try {
            const parsed = JSON.parse(jsonInput)
            setManualData(parsed)
        } catch (e) {
            alert("Invalid JSON format. Please paste JSON from output.json")
        }
    }

    const handleLoadOutputJson = async () => {
        try {
            const response = await axios.get("http://localhost:3001/load-output")
            setManualData(response.data)
            setJsonInput(JSON.stringify(response.data, null, 4))
        } catch (err) {
            console.error("Failed to load output.json:", err)
            alert("Could not load output.json. Make sure the backend is running and the file exists.")
        }
    }

    return (
        <div className={styles.pageContainer}>
            <h1 style={{ textAlign: "center", marginBottom: "20px" }}>Instagram Content Generator</h1>

            <div className={styles.jsonInputSection}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                    <h3 style={{ margin: 0 }}>Paste processed JSON (e.g. from output.json)</h3>
                    <button onClick={handleLoadOutputJson} className="copy-btn" style={{ background: "var(--success)" }}>
                        Load output.json from disk
                    </button>
                </div>
                <textarea
                    className={styles.textarea}
                    placeholder='{ "Venue": [ { "title": "...", "image_url": "..." } ] }'
                    value={jsonInput}
                    onChange={(e) => setJsonInput(e.target.value)}
                />
                <button onClick={handleApplyJson} className="copy-btn" style={{ background: "var(--primary)" }}>
                    Apply JSON Data
                </button>
                {manualData && (
                    <button onClick={() => setManualData(null)} className={styles.clearBtn}>
                        Clear Manual Data
                    </button>
                )}
            </div>

            <div className={styles.eventsList}>
                {allEvents.length === 0 ? (
                    <div className={styles.emptyState}>
                        <p>No events found to generate posts.</p>
                        <p>
                            Please paste processed results from <strong>output.json</strong> above.
                        </p>
                    </div>
                ) : (
                    allEvents.map((event, idx) => <InstagramPost key={idx} event={event} />)
                )}
            </div>
        </div>
    )
}
