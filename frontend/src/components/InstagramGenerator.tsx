import { toJpeg } from "html-to-image"
import React, { useCallback, useRef, useState } from "react"
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
    isSelected: boolean
    onToggle: () => void
    registerRef: (el: HTMLDivElement | null) => void
}

// --- Komponenta pro jeden post ---
const InstagramPost: React.FC<PostProps> = ({ event, isSelected, onToggle, registerRef }) => {
    const postRef = useRef<HTMLDivElement>(null)
    const [isPublishing, setIsPublishing] = useState(false)
    const [publishStatus, setPublishStatus] = useState<string | null>(null)

    // Handle local ref and parent registration
    const setRefs = useCallback(
        (el: HTMLDivElement | null) => {
            // @ts-ignore
            postRef.current = el
            registerRef(el)
        },
        [registerRef]
    )

    // Pomocná konstanta pro CORS proxy
    const proxiedImageUrl = event.image_url ? `http://localhost:8000/proxy-image?url=${encodeURIComponent(event.image_url)}` : null

    const publishToInstagram = useCallback(async () => {
        if (postRef.current === null) return

        setIsPublishing(true)
        setPublishStatus("Generuji obrázek...")

        try {
            const dataUrl = await toJpeg(postRef.current, {
                quality: 0.95,
                canvasWidth: 1080,
                canvasHeight: 1080,
                cacheBust: true,
            })

            setPublishStatus("Odesílám do prohlížeče...")

            const caption = `Akce v Brně ${event.date} \n\n#brno #party #akcebrno #kamvbrne`

            const response = await fetch("http://localhost:8000/ig-publish", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    images_base64: [dataUrl],
                    caption: caption,
                    location_name: "Brno, Czech Republic",
                }),
            })

            if (!response.ok) {
                const errData = await response.json()
                throw new Error(errData.detail || "Chyba při publikování")
            }

            setPublishStatus("Publikováno!")
            setTimeout(() => setPublishStatus(null), 5000)
        } catch (err: any) {
            console.error("Publish failed:", err)
            alert(`Publikování selhalo: ${err.message}`)
            setPublishStatus(null)
        } finally {
            setIsPublishing(false)
        }
    }, [event])

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
        <div className={`${styles.postContainer} ${isSelected ? styles.selected : ""}`}>
            <div className={styles.selectionOverlay}>
                <input type="checkbox" checked={isSelected} onChange={onToggle} className={styles.checkbox} />
            </div>

            <div className={styles.previewScale}>
                {/* Container pro export - 1080x1080 */}
                <div ref={setRefs} className={styles.exportCanvas}>
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
            <div className={styles.buttonGroup}>
                <button onClick={exportImage} className={styles.downloadBtn}>
                    Stáhnout JPEG (1080x1080)
                </button>
                <button onClick={publishToInstagram} className={`${styles.downloadBtn} ${styles.publishBtn}`} disabled={isPublishing}>
                    {isPublishing ? "Publikuji..." : "Publikovat na Instagram"}
                </button>
            </div>
            {publishStatus && <div className={styles.statusIndicator}>{publishStatus}</div>}
        </div>
    )
}

// --- Hlavní stránka s iterací přes data z AI Processor ---
export const InstagramGeneratorPage: React.FC<{ data: Record<string, any[]> }> = ({ data }) => {
    const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set())
    const [isBatchPublishing, setIsBatchPublishing] = useState(false)
    const [batchStatus, setBatchStatus] = useState<string | null>(null)
    const postRefs = useRef<Record<number, HTMLDivElement | null>>({})

    const allEvents = Object.entries(data)
        .flatMap(([venueName, events]) =>
            Array.isArray(events)
                ? events.map((event) => ({
                      venue: venueName, // Default to the key
                      ...event, // If event already has a venue (from AI), it will overwrite the default
                  }))
                : [],
        )
        .filter((e) => e.title) // Filter out raw scraped items without titles

    const toggleSelection = (idx: number) => {
        const newSet = new Set(selectedIndices)
        if (newSet.has(idx)) {
            newSet.delete(idx)
        } else {
            newSet.add(idx)
        }
        setSelectedIndices(newSet)
    }

    const publishBatch = async () => {
        if (selectedIndices.size === 0) {
            alert("Vyberte alespoň jednu akci k publikování.")
            return
        }

        setIsBatchPublishing(true)
        setBatchStatus(`Generuji ${selectedIndices.size} obrázků...`)

        try {
            const imagesBase64: string[] = []
            const sortedIndices = Array.from(selectedIndices).sort((a, b) => a - b)

            for (const idx of sortedIndices) {
                const ref = postRefs.current[idx]
                if (ref) {
                    const dataUrl = await toJpeg(ref, {
                        quality: 0.95,
                        canvasWidth: 1080,
                        canvasHeight: 1080,
                        cacheBust: true,
                    })
                    imagesBase64.push(dataUrl)
                }
            }

            setBatchStatus("Odesílám dávku na Instagram...")

            // Create a collective caption
            const caption = `Akce v Brně ${allEvents[sortedIndices[0]]?.date || new Date().toLocaleDateString("cs-CZ")} \n\n#brno #party #akcebrno #kamvbrne`


            const response = await fetch("http://localhost:8000/ig-publish", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    images_base64: imagesBase64,
                    caption: caption,
                    location_name: "Brno, Czech Republic",
                }),
            })

            if (!response.ok) {
                const errData = await response.json()
                throw new Error(errData.detail || "Chyba při hromadném publikování")
            }

            setBatchStatus("Dávka úspěšně publikována!")
            setTimeout(() => setBatchStatus(null), 5000)
            setSelectedIndices(new Set())
        } catch (err: any) {
            console.error("Batch publish failed:", err)
            alert(`Hromadné publikování selhalo: ${err.message}`)
            setBatchStatus(null)
        } finally {
            setIsBatchPublishing(false)
        }
    }

    return (
        <div className={styles.pageContainer}>
            <h1 style={{ textAlign: "center", marginBottom: "20px" }}>Instagram Content Generator</h1>

            {allEvents.length > 0 && (
                <div className={styles.batchActions}>
                    <div className={styles.selectionInfo}>{selectedIndices.size} vybráno</div>
                    <button onClick={publishBatch} disabled={isBatchPublishing || selectedIndices.size === 0} className={`${styles.downloadBtn} ${styles.publishBtn}`}>
                        {isBatchPublishing ? "Publikuji dávku..." : `Publikovat vybrané (${selectedIndices.size})`}
                    </button>
                    {batchStatus && <div className={styles.batchStatus}>{batchStatus}</div>}
                </div>
            )}

            <div className={styles.eventsList}>
                {allEvents.length === 0 ? (
                    <div className={styles.emptyState}>
                        <p>No processed events found.</p>
                        <p>
                            Please run the <strong>AI Processor</strong> in the Scraper Dashboard first.
                        </p>
                    </div>
                ) : (
                    allEvents.map((event, idx) => (
                        <InstagramPost
                            key={idx}
                            event={event}
                            isSelected={selectedIndices.has(idx)}
                            onToggle={() => toggleSelection(idx)}
                            registerRef={(el) => (postRefs.current[idx] = el)}
                        />
                    ))
                )}
            </div>
        </div>
    )
}
