import { toJpeg } from "html-to-image"
import React, { useCallback, useRef } from "react"
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
    const proxiedImageUrl = event.image_url ? `http://localhost:8000/proxy-image?url=${encodeURIComponent(event.image_url)}` : null

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
                            {/* <div className={styles.locationBadge}>{event.venue || event.place || "Brno"}</div> */}
                        </div>

                        {/* Název akce - Maximální důraz */}
                        <h1 className={styles.actionTitle}>{event.title || "Název akce"}</h1>

                        <div className={styles.actionDetails}>
                            {/* Místo */}
                            {event.venue && <div className={styles.detailItem}>{event.venue}</div>}

                            {/* Čas */}
                            {event.time && " | "}
                            {event.time && <div className={styles.detailItem}>{event.time}</div>}

                            {/* Cena */}
                            {event.price && " | "}
                            {event.price && <div className={styles.detailItem}>{event.price}</div>}
                        </div>
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

// --- Hlavní stránka s iterací přes data z AI Processor ---
export const InstagramGeneratorPage: React.FC<{ data: Record<string, any[]> }> = ({ data }) => {
    const allEvents = Object.entries(data)
        .flatMap(([venueName, events]) => (Array.isArray(events) ? events.map((event) => ({
            venue: venueName, // Default to the key
            ...event // If event already has a venue (from AI), it will overwrite the default
        })) : []))
        .filter((e) => e.title) // Filter out raw scraped items without titles

    return (
        <div className={styles.pageContainer}>
            <h1 style={{ textAlign: "center", marginBottom: "20px" }}>Instagram Content Generator</h1>

            <div className={styles.eventsList}>
                {allEvents.length === 0 ? (
                    <div className={styles.emptyState}>
                        <p>No processed events found.</p>
                        <p>
                            Please run the <strong>AI Processor</strong> in the Scraper Dashboard first.
                        </p>
                    </div>
                ) : (
                    allEvents.map((event, idx) => <InstagramPost key={idx} event={event} />)
                )}
            </div>
        </div>
    )
}
