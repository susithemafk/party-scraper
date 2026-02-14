import React, { useState, useCallback, useMemo } from "react"
import axios from "axios"
import "./App.css"
import { ScraperSection } from "./components/ScraperSection"
import { InstagramGeneratorPage } from "./components/InstagramGenerator"
import { AiProcessor } from "./components/AiProcessor"
import { artbarParser } from "./parsers/artbar"
import { kabinetParser } from "./parsers/kabinet"
import { sonoParser } from "./parsers/sono"
import { fledaParser } from "./parsers/fleda"
import { perpetuumParser } from "./parsers/perpetuum"
import { patroParser } from "./parsers/patro"
import { metroParser } from "./parsers/metro"
import { raParser } from "./parsers/ra"
import { bobyhallParser } from "./parsers/bobyhall"
import { ScrapedItem } from "./types"

const VENUES = [
    { title: "Bobyhall", url: "https://bobyhall.cz/program-bobyhall/", parser: bobyhallParser },
    { title: "Fraktal", url: "https://ra.co/clubs/224489", parser: raParser },
    { title: "Metro Music Bar", url: "https://www.metromusic.cz/program/", parser: metroParser },
    { title: "První patro", url: "https://patrobrno.cz/", parser: patroParser },
    { title: "Perpetuum", url: "https://www.perpetuumklub.cz/program/", parser: perpetuumParser },
    { title: "Fléda", url: "https://www.fleda.cz/program/", parser: fledaParser },
    { title: "Sono Music Club", url: "https://www.sono.cz/program/", parser: sonoParser },
    { title: "Kabinet Múz", url: "https://www.kabinetmuz.cz/program", parser: kabinetParser },
    { title: "Artbar", url: "https://www.artbar.club/shows", parser: artbarParser },
]

const App: React.FC = () => {
    const [triggerAll, setTriggerAll] = useState(0)
    const [allResults, setAllResults] = useState<Record<string, ScrapedItem[]>>({})
    const [copiedAll, setCopiedAll] = useState(false)
    const [savedAll, setSavedAll] = useState(false)
    const [globalOnlyToday, setGlobalOnlyToday] = useState(true)
    const [view, setView] = useState<"scraper" | "instagram">("scraper")

    const handleFetchAll = useCallback(() => {
        setAllResults({})
        setTriggerAll((prev) => prev + 1)
    }, [])

    const handleResult = useCallback((title: string, items: ScrapedItem[] | null) => {
        if (items) {
            setAllResults((prev) => {
                // Only update if the items have actually changed to avoid unnecessary re-renders
                if (prev[title] === items) return prev
                return { ...prev, [title]: items }
            })
        }
    }, [])

    const aggregatedResults = useMemo(() => {
        const flattened = Object.values(allResults).flat()

        // Deduplicate by URL
        const seenUrls = new Set<string>()
        const unique = flattened.filter((item) => {
            if (!item.url) return true
            if (seenUrls.has(item.url)) return false
            seenUrls.add(item.url)
            return true
        })

        return unique.sort((a, b) => {
            if (!a.date) return 1
            if (!b.date) return -1
            return a.date.localeCompare(b.date)
        })
    }, [allResults])

    const handleCopyAll = useCallback(() => {
        const output: Record<string, { date: string | null; url: string }[]> = {}

        Object.entries(allResults).forEach(([venue, items]) => {
            if (items && items.length > 0) {
                output[venue] = items.map((item) => ({
                    date: item.date,
                    url: item.url,
                }))
            }
        })

        if (Object.keys(output).length === 0) return

        navigator.clipboard.writeText(JSON.stringify(output, null, 4)).then(() => {
            setCopiedAll(true)
            setTimeout(() => setCopiedAll(false), 2000)
        })
    }, [allResults])

    const handleSaveInputFile = useCallback(async () => {
        const output: Record<string, { date: string | null; url: string }[]> = {}

        Object.entries(allResults).forEach(([venue, items]) => {
            if (items && items.length > 0) {
                output[venue] = items.map((item) => ({
                    date: item.date,
                    url: item.url,
                }))
            }
        })

        if (Object.keys(output).length === 0) return

        try {
            await axios.post("http://localhost:3001/save-json", output)
            setSavedAll(true)
            setTimeout(() => setSavedAll(false), 2000)
        } catch (err) {
            console.error("Save failed:", err)
            alert("Failed to save input.json")
        }
    }, [allResults])

    return (
        <div className="container">
            <div className="view-selector" style={{ display: "flex", gap: "1rem", justifyContent: "center", marginBottom: "2rem" }}>
                <button
                    onClick={() => setView("scraper")}
                    style={{
                        padding: "0.5rem 1.5rem",
                        borderRadius: "2rem",
                        border: "1px solid var(--primary)",
                        background: view === "scraper" ? "var(--primary)" : "transparent",
                        color: "white",
                        cursor: "pointer"
                    }}
                >
                    Scraper Dashboard
                </button>
                <button
                    onClick={() => setView("instagram")}
                    style={{
                        padding: "0.5rem 1.5rem",
                        borderRadius: "2rem",
                        border: "1px solid var(--primary)",
                        background: view === "instagram" ? "var(--primary)" : "transparent",
                        color: "white",
                        cursor: "pointer"
                    }}
                >
                    Instagram Generator
                </button>
            </div>

            {view === "instagram" ? (
                <InstagramGeneratorPage data={allResults} />
            ) : (
                <>
                    <h1>Party Scraper</h1>
                    <p className="subtitle">Automated Event Intelligence</p>

                    <div className="bulk-controls" style={{ marginBottom: "2rem", display: "flex", gap: "1rem", justifyContent: "center", alignItems: "center" }}>
                        <button onClick={handleFetchAll} className="fetch-all-btn">
                            FETCH ALL SCRAPERS ({VENUES.length})
                        </button>
                        <label className="global-filter" style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontSize: "0.9rem", color: "var(--text-muted)" }}>
                            <input
                                type="checkbox"
                                checked={globalOnlyToday}
                                onChange={(e) => setGlobalOnlyToday(e.target.checked)}
                                style={{ width: "1.1rem", height: "1.1rem", accentColor: "var(--primary)" }}
                            />
                            ONLY TODAY (GLOBAL)
                        </label>
                        {aggregatedResults.length > 0 && (
                            <div style={{ display: "flex", gap: "1rem" }}>
                                <button
                                    onClick={handleCopyAll}
                                    className="copy-btn"
                                    style={{ background: copiedAll ? "var(--success)" : "var(--primary)" }}
                                >
                                    {copiedAll ? "Copied All (JSON)!" : `Copy All (${aggregatedResults.length})`}
                                </button>
                                <button
                                    onClick={handleSaveInputFile}
                                    className="copy-btn"
                                    style={{
                                        background: savedAll ? "var(--success)" : "transparent",
                                        border: "1px solid var(--primary)",
                                        color: "var(--text)"
                                    }}
                                >
                                    {savedAll ? "Saved to input.json!" : "Save input.json"}
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="main-content">
                        <AiProcessor inputData={aggregatedResults} />

                        {VENUES.map((venue) => (
                            <ScraperSection
                                key={venue.title}
                                title={venue.title}
                                defaultUrl={venue.url}
                                parserFunc={venue.parser}
                                onResult={handleResult}
                                onlyToday={globalOnlyToday}
                                setOnlyToday={setGlobalOnlyToday}
                            />
                        ))}
                    </div>
                </>
            )}
        </div>
    )
}

export default App
