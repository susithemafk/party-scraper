import { toJpeg } from "html-to-image"
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react"
import styles from "./InstagramGenerator.module.css"

const formatDate = (dateStr: string) => {
    if (!dateStr) return ""
    const parts = dateStr.split("-")
    if (parts.length === 3) {
        const [year, month, day] = parts
        return `${day}. ${month}. ${year}`
    }
    return dateStr
}

// --- Definice Typů ---
interface EventDetail {
    id?: string // Unikátní identifikátor pro potřeby renderování a cache
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

// --- Komponenta pro úvodní post ---
const InstagramTitlePost = React.memo<{
    id: string
    imageUrl: string | null
    venues: string
    isSelected: boolean
    onToggle: () => void
    onRefresh: () => void
    registerRef: (el: HTMLDivElement | null) => void
}>(({ id, imageUrl, venues, isSelected, onToggle, onRefresh, registerRef }) => {
    const localRef = useRef<HTMLDivElement | null>(null)
    const [imageDataUrl, setImageDataUrl] = useState<string | null>(null)

    useEffect(() => {
        if (!imageUrl) {
            setImageDataUrl(null)
            return
        }

        setImageDataUrl(null) // Reset while loading new image
        const controller = new AbortController()
        const fetchImage = async () => {
            try {
                const proxyUrl = `http://localhost:8000/proxy-image?url=${encodeURIComponent(imageUrl)}&cb=${Date.now()}`
                const response = await fetch(proxyUrl, { signal: controller.signal })
                if (!response.ok) return
                const blob = await response.blob()
                const reader = new FileReader()
                reader.onloadend = () => setImageDataUrl(reader.result as string)
                reader.readAsDataURL(blob)
            } catch (err) {
                console.error("[Title Refresh] Failed to fetch image:", err)
            }
        }
        fetchImage()
        return () => controller.abort()
    }, [imageUrl])

    const handleRef = useCallback(
        (el: HTMLDivElement | null) => {
            localRef.current = el
            registerRef(el)
        },
        [registerRef],
    )

    const formattedDate = useMemo(() => {
        const d = new Date()
        return `${String(d.getDate()).padStart(2, "0")}. ${String(d.getMonth() + 1).padStart(2, "0")}.`
    }, [])

    return (
        <div className={`${styles.postContainer} ${isSelected ? styles.selected : ""}`}>
            <div className={styles.selectionOverlay}>
                <input type="checkbox" checked={isSelected} onChange={onToggle} className={styles.checkbox} />
            </div>

            <div className={styles.previewScale}>
                <div ref={handleRef} className={styles.exportCanvas} data-event-id={id}>
                    {imageDataUrl ? (
                        <img src={imageDataUrl} className={styles.backgroundImage} crossOrigin="anonymous" alt="Title BG" />
                    ) : (
                        <div className={styles.fallbackBackground} />
                    )}
                    <div
                        className={styles.gradientOverlay}
                        style={{ height: "100%", background: "linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.4) 100%)" }}
                    />
                    <div
                        className={styles.textContent}
                        style={{
                            height: "100%",
                            display: "flex",
                            flexDirection: "column",
                            justifyContent: "center",
                            alignItems: "center",
                            textAlign: "center",
                            padding: "0 80px",
                        }}
                    >
                        <h1 className={styles.actionTitle} style={{ fontSize: "120px", marginBottom: "40px", WebkitLineClamp: "unset" }}>
                            AKCE V BRNĚ
                        </h1>
                        <div style={{ width: "200px", height: "12px", background: "#306be1", marginBottom: "40px" }} />
                        <h2 className={styles.actionTitle} style={{ fontSize: "100px", opacity: 0.9 }}>
                            {formattedDate}
                        </h2>
                        {venues && (
                            <div
                                style={{
                                    fontSize: "32px",
                                    fontWeight: "800",
                                    marginTop: "40px",
                                    textTransform: "uppercase",
                                    letterSpacing: "4px",
                                    opacity: 0.8,
                                    borderTop: "2px solid rgba(255, 255, 255, 0.8)",
                                    paddingTop: "20px",
                                }}
                            >
                                {venues}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className={styles.buttonGroup}>
                <button onClick={onRefresh} className={styles.downloadBtn}>
                    Změnit pozadí
                </button>
            </div>
        </div>
    )
})

// --- Komponenta pro jeden post ---
const InstagramPost = React.memo<PostProps>(({ event, isSelected, onToggle, registerRef }) => {
    // Odstraněn lokální ref a setRefs, protože registerRef už je stabilní callback z rodiče
    // a my potřebujeme zajistit, aby rodič měl přesný odkaz na tento DOM element.
    // Pro vlastní potřeby (toJpeg v rámci komponenty) můžeme použít přímo forwardRef nebo jen ID.
    // Ale zde, 'registerRef' ukládá náš div do `postRefs.current` v rodiči.

    // Pomocná konstanta pro CORS proxy s unikátním ID pro každou instanci, aby se předešlo záměně v cache
    const proxiedImageUrl = useMemo(() => {
        if (!event.image_url) return null
        const encodedUrl = encodeURIComponent(event.image_url)
        // Přidáme unikátní sůl (timestamp), abychom vynutili nové stažení při každém renderu identity
        const salt = event.id ? `&s=${encodeURIComponent(event.id)}` : ""
        return `http://localhost:8000/proxy-image?url=${encodedUrl}${salt}`
    }, [event.image_url, event.id])

    // Lokální toJpeg volání (pro tlačítko 'Publikovat na Instagram' uvnitř karty)
    // Zde musíme získat ten samý element, který jsme registrovali.
    // Nejjednodušší je uložit si ho i lokálně, ale opatrně s synchronizací.
    const localRef = useRef<HTMLDivElement | null>(null)
    const [isPublishing, setIsPublishing] = useState(false)
    const [publishStatus, setPublishStatus] = useState<string | null>(null)
    const [imageDataUrl, setImageDataUrl] = useState<string | null>(null)

    // Pre-fetch image and convert to Data URL to ensure html-to-image doesn't fail or cache-collide
    useEffect(() => {
        if (!event.image_url) {
            setImageDataUrl(null)
            return
        }

        const controller = new AbortController()
        const fetchImage = async () => {
            try {
                // Add a timestamp to bypass any local browser cache that might hold an error or stale image
                const proxyUrl = `http://localhost:8000/proxy-image?url=${encodeURIComponent(event.image_url)}&cb=${Date.now()}`
                console.log(`[Pre-fetch] Starting: ${event.title} -> ${proxyUrl}`)
                const response = await fetch(proxyUrl, { signal: controller.signal })

                if (!response.ok) {
                    const text = await response.text()
                    throw new Error(`Status ${response.status}: ${text}`)
                }

                const blob = await response.blob()
                console.log(`[Pre-fetch] Blob received: ${event.title}, ${blob.size} bytes, type: ${blob.type}`)

                const reader = new FileReader()
                reader.onloadend = () => {
                    setImageDataUrl(reader.result as string)
                    console.log(`[Pre-fetch] Data URL ready: ${event.title}`)
                }
                reader.readAsDataURL(blob)
            } catch (err: any) {
                if (err.name !== "AbortError") {
                    console.error(`[Pre-fetch] Error for ${event.title}:`, err)
                }
            }
        }

        fetchImage()
        return () => controller.abort()
    }, [event.image_url, event.title])

    const handleRef = useCallback(
        (el: HTMLDivElement | null) => {
            localRef.current = el
            registerRef(el)
        },
        [registerRef],
    )

    const publishToInstagram = useCallback(async () => {
        if (!localRef.current) return

        setIsPublishing(true)
        setPublishStatus("Generuji obrázek...")

        try {
            // Wait for image to be Data URL
            const img = localRef.current.querySelector("img")
            if (img && !img.src.startsWith("data:")) {
                setPublishStatus("Načítám podklad...")
                let attempts = 0
                while (img && !img.src.startsWith("data:") && attempts < 50) {
                    await new Promise((r) => setTimeout(r, 100))
                    attempts++
                }
            }

            const dataUrl = await toJpeg(localRef.current, {
                quality: 0.95,
                canvasWidth: 1080,
                canvasHeight: 1080,
                cacheBust: false,
            })

            console.log(`[Generated] Image generated for ${event.title}, size: ${dataUrl.length}`)

            setPublishStatus("Odesílám do prohlížeče...")

            const formattedDate = formatDate(event.date)
            const caption = `Akce v Brně ${formattedDate} \n\n#brno #party #akcebrno #kamvbrne`

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
    }, [event.title, event.date]) // removed postRef from dependency since we use localRef

    const exportImage = useCallback(async () => {
        if (!localRef.current) return

        try {
            // Wait for image to be Data URL
            const img = localRef.current.querySelector("img")
            if (img && !img.src.startsWith("data:")) {
                let attempts = 0
                while (img && !img.src.startsWith("data:") && attempts < 50) {
                    await new Promise((r) => setTimeout(r, 100))
                    attempts++
                }
            }

            const dataUrl = await toJpeg(localRef.current, {
                quality: 0.95,
                canvasWidth: 1080,
                canvasHeight: 1080,
                cacheBust: false,
            })

            const link = document.createElement("a")
            link.download = `post-${event.title.substring(0, 15).replace(/\s+/g, "-")}.jpg`
            link.href = dataUrl
            link.click()
        } catch (err) {
            console.error("Export selhal:", err)
            alert("Export se nezdařil.")
        }
    }, [event.title]) // removed postRef

    return (
        <div className={`${styles.postContainer} ${isSelected ? styles.selected : ""}`}>
            <div className={styles.selectionOverlay}>
                <input type="checkbox" checked={isSelected} onChange={onToggle} className={styles.checkbox} />
            </div>

            <div className={styles.previewScale}>
                <div ref={handleRef} className={styles.exportCanvas} data-event-id={event.id}>
                    {imageDataUrl ? (
                        <img
                            key={imageDataUrl.substring(0, 100)} // Unique key for data URL
                            src={imageDataUrl}
                            alt={event.title}
                            crossOrigin="anonymous"
                            className={styles.backgroundImage}
                            loading="eager"
                            onLoad={() => console.log(`[Image Ready] ${event.title}`)}
                            onError={(e) => {
                                console.error("Image display failed:", event.title)
                                ;(e.target as HTMLImageElement).style.display = "none"
                            }}
                        />
                    ) : proxiedImageUrl ? (
                        <div className={styles.loadingBackground}>Loading Image...</div>
                    ) : (
                        <div className={styles.fallbackBackground} />
                    )}

                    <div className={styles.locationContainer}>{event.venue || event.place || "Brno"}</div>
                    <div className={styles.gradientOverlay} />
                    <div className={styles.textContent}>
                        <div className={styles.timeBadgeContainer}>
                            <div className={styles.timeBadge}>DNES {event.time && `| ${event.time}`}</div>
                        </div>

                        <h1 className={styles.actionTitle}>{event.title || "Název akce"}</h1>

                        <div className={styles.actionDetails}>
                            {event.venue && <div className={styles.detailItem}>{event.venue}</div>}
                            {event.time && " | "}
                            {event.time && <div className={styles.detailItem}>{event.time}</div>}
                            {event.price && " | "}
                            {event.price && <div className={styles.detailItem}>{event.price}</div>}
                        </div>
                    </div>
                </div>
            </div>

            <div className={styles.buttonGroup}>
                <button onClick={exportImage} className={styles.downloadBtn}>
                    Stáhnout JPEG
                </button>
                <button onClick={publishToInstagram} className={`${styles.downloadBtn} ${styles.publishBtn}`} disabled={isPublishing}>
                    {isPublishing ? "Publikuji..." : "Publikovat na Instagram"}
                </button>
            </div>
            {publishStatus && <div className={styles.statusIndicator}>{publishStatus}</div>}
        </div>
    )
})

// --- Hlavní stránka s iterací přes data z AI Processor ---
export const InstagramGeneratorPage: React.FC<{ data: Record<string, any[]> }> = ({ data }) => {
    const [selectedIndices, setSelectedIndices] = useState<Set<string>>(new Set())
    const [isBatchPublishing, setIsBatchPublishing] = useState(false)
    const [batchStatus, setBatchStatus] = useState<string | null>(null)
    const [hasInitializedSelection, setHasInitializedSelection] = useState(false)
    const [titleImageIndex, setTitleImageIndex] = useState(0)
    const postRefs = useRef<Record<string, HTMLDivElement | null>>({})

    const allEvents = useMemo(() => {
        return Object.entries(data)
            .flatMap(([venueName, events]) =>
                Array.isArray(events)
                    ? events.map((event, idx) => {
                          // Robustní ID: venue + title + date + index, očištěné od diakritiky a mezer
                          const slug = (text: string) =>
                              text
                                  .normalize("NFD")
                                  .replace(/[\u0300-\u036f]/g, "")
                                  .replace(/[^a-zA-Z0-9]/g, "_")

                          const id = `${slug(venueName)}-${slug(event.title || "event")}-${slug(event.date || "date")}-${idx}`
                          return {
                              venue: venueName,
                              ...event,
                              id: id,
                          }
                      })
                    : [],
            )
            .filter((e) => e.title)
    }, [data])

    const titleImageUrl = useMemo(() => {
        if (allEvents.length === 0) return null
        const withImg = allEvents.filter((e) => e.image_url)
        if (withImg.length === 0) return allEvents[0].image_url
        return withImg[titleImageIndex % withImg.length].image_url
    }, [allEvents, titleImageIndex])

    const venuesString = useMemo(() => {
        const uniqueVenues = Array.from(new Set(allEvents.map((e) => e.venue).filter(Boolean)))
        return uniqueVenues.join(" | ")
    }, [allEvents])

    // Auto-select all events when they are first loaded
    useEffect(() => {
        if (allEvents.length > 0 && !hasInitializedSelection) {
            const ids = allEvents.map((e) => e.id)
            ids.unshift("title-post")
            setSelectedIndices(new Set(ids))
            setHasInitializedSelection(true)
        }
    }, [allEvents, hasInitializedSelection])

    const toggleSelection = useCallback((id: string) => {
        setSelectedIndices((prev) => {
            const newSet = new Set(prev)
            if (newSet.has(id)) {
                newSet.delete(id)
            } else {
                newSet.add(id)
            }
            return newSet
        })
    }, [])

    const registerRef = useCallback((id: string, el: HTMLDivElement | null) => {
        postRefs.current[id] = el
    }, [])

    const selectAll = useCallback(() => {
        const ids = allEvents.map((e) => e.id)
        ids.unshift("title-post")
        setSelectedIndices(new Set(ids))
    }, [allEvents])

    const deselectAll = useCallback(() => {
        setSelectedIndices(new Set())
    }, [])

    const publishBatch = async () => {
        if (selectedIndices.size === 0) {
            alert("Vyberte alespoň jednu akci k publikování.")
            return
        }

        setIsBatchPublishing(true)
        setBatchStatus(`Generuji ${selectedIndices.size} obrázků...`)

        try {
            const imagesBase64: string[] = []

            // Order: title-post first if selected, then events
            const idsToProcess: string[] = []
            if (selectedIndices.has("title-post")) {
                idsToProcess.push("title-post")
            }

            // Use order from allEvents for the rest
            const selectedEvents = allEvents.filter((e) => selectedIndices.has(e.id))
            selectedEvents.forEach((e) => idsToProcess.push(e.id))

            for (const id of idsToProcess) {
                const ref = postRefs.current[id]
                if (ref) {
                    console.log(`[Batch] processing: ${id}`)
                    // Wait for image to be fully ready in the DOM
                    const img = ref.querySelector("img") as HTMLImageElement
                    if (img) {
                        // Check if it's already a Data URL (which we pre-fetched)
                        if (!img.src.startsWith("data:")) {
                            console.log(`[Batch] Waiting for Data URL for: ${id}`)
                            // Wait up to 5 seconds for the pre-fetch to complete
                            let attempts = 0
                            while (!img.src.startsWith("data:") && attempts < 50) {
                                await new Promise((r) => setTimeout(r, 100))
                                attempts++
                            }
                        }
                    }

                    await new Promise((r) => setTimeout(r, 400))

                    const dataUrl = await toJpeg(ref, {
                        quality: 0.95,
                        canvasWidth: 1080,
                        canvasHeight: 1080,
                        cacheBust: false,
                    })
                    imagesBase64.push(dataUrl)
                    console.log(`[Batch] captured image for ${id}, size: ${dataUrl.length}`)
                } else {
                    console.warn(`[Batch] Ref not found for: ${id}`)
                }
            }

            setBatchStatus("Odesílám dávku na Instagram...")

            const firstEvent = selectedEvents[0]
            const formattedDate = firstEvent?.date ? formatDate(firstEvent.date) : new Date().toLocaleDateString("cs-CZ")
            const caption = `Akce v Brně ${formattedDate} \n\n#brno #party #akcebrno #kamvbrne`

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
                    <button onClick={selectAll} className={styles.downloadBtn}>
                        Vybrat vše
                    </button>
                    <button onClick={deselectAll} className={styles.downloadBtn}>
                        Zrušit výběr
                    </button>
                    <button
                        onClick={publishBatch}
                        disabled={isBatchPublishing || selectedIndices.size === 0}
                        className={`${styles.downloadBtn} ${styles.publishBtn}`}
                    >
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
                    <>
                        <InstagramTitlePost
                            id="title-post"
                            imageUrl={titleImageUrl}
                            venues={venuesString}
                            isSelected={selectedIndices.has("title-post")}
                            onToggle={() => toggleSelection("title-post")}
                            onRefresh={() => setTitleImageIndex((prev) => prev + 1)}
                            registerRef={(el) => registerRef("title-post", el)}
                        />
                        {allEvents.map((event) => (
                            <InstagramPost
                                key={event.id}
                                event={event}
                                isSelected={selectedIndices.has(event.id)}
                                onToggle={() => toggleSelection(event.id)}
                                registerRef={(el) => registerRef(event.id, el)}
                            />
                        ))}
                    </>
                )}
            </div>
        </div>
    )
}
