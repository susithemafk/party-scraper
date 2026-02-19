import React, { useState, useCallback, useMemo } from "react"
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
    { title: "Fraktal", url: "https://ra.co/clubs/224489/events", parser: raParser },
    { title: "pul.pit", url: "https://ra.co/clubs/206733/events", parser: raParser },
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
    const [expandAllCounter, setExpandAllCounter] = useState(0)
    const [collapseAllCounter, setCollapseAllCounter] = useState(0)
    const [allResults, setAllResults] = useState<Record<string, ScrapedItem[]>>({})
    const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({})
    const [aiResults, setAiResults] = useState<Record<string, any[]>>({})
    const [copiedAll, setCopiedAll] = useState(false)
    const [globalOnlyToday, setGlobalOnlyToday] = useState(true)
    const [view, setView] = useState<"scraper" | "instagram">("scraper")

    const handleFetchAll = useCallback(() => {
        setAllResults({})
        setTriggerAll((prev) => prev + 1)
    }, [])

    const handleLoading = useCallback((title: string, isLoading: boolean) => {
        setLoadingStates((prev) => {
            if (prev[title] === isLoading) return prev;
            return { ...prev, [title]: isLoading };
        });
    }, [])

    const handleAiComplete = useCallback((results: Record<string, any[]>) => {
        setAiResults(results)
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
        // Flatten with venue info included
        const flattened = Object.entries(allResults).flatMap(([venue, items]) =>
            items.map(item => ({ ...item, venue }))
        )

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

    const hasAiResults = Object.keys(aiResults).length > 0
    const activeScrapersCount = Object.values(loadingStates).filter(Boolean).length
    const isAnyLoading = activeScrapersCount > 0

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
                        cursor: "pointer",
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
                        cursor: "pointer",
                    }}
                >
                    Instagram Generator
                </button>
            </div>

            <div className="main-content-wrapper" style={{ display: view === "instagram" ? "none" : "block" }}>
                <h1>Party Scraper</h1>
                <p className="subtitle">Automated Event Intelligence</p>

                <div
                    className="bulk-controls"
                    style={{ marginBottom: "2rem", display: "flex", flexWrap: "wrap", gap: "1rem", justifyContent: "center", alignItems: "center" }}
                >
                    <div style={{ position: "relative" }}>
                        <button onClick={handleFetchAll} className="fetch-all-btn" disabled={isAnyLoading}>
                            {isAnyLoading ? `FETCHING... (${activeScrapersCount}/${VENUES.length})` : `FETCH ALL SCRAPERS (${VENUES.length})`}
                        </button>
                        {isAnyLoading && (
                            <div className="fetching-loader-bar"></div>
                        )}
                    </div>

                    <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button
                            className="secondary-button"
                            style={{ padding: "0.5rem 1rem", fontSize: "0.8rem" }}
                            onClick={() => setExpandAllCounter(prev => prev + 1)}
                        >
                            <i className="bi bi-arrows-expand"></i> OPEN ALL
                        </button>
                        <button
                            className="secondary-button"
                            style={{ padding: "0.5rem 1rem", fontSize: "0.8rem" }}
                            onClick={() => setCollapseAllCounter(prev => prev + 1)}
                        >
                            <i className="bi bi-arrows-collapse"></i> CLOSE ALL
                        </button>
                    </div>

                    <label
                        className="global-filter"
                        style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontSize: "0.9rem", color: "var(--text-muted)" }}
                    >
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
                            <button onClick={handleCopyAll} className="copy-btn" style={{ background: copiedAll ? "var(--success)" : "var(--primary)" }}>
                                {copiedAll ? "Copied All (JSON)!" : `Copy All (${aggregatedResults.length})`}
                            </button>
                        </div>
                    )}
                </div>

                <div className="main-content">
                    <AiProcessor inputData={aggregatedResults} onComplete={handleAiComplete} />

                    {VENUES.map((venue) => (
                        <ScraperSection
                            key={venue.title}
                            title={venue.title}
                            defaultUrl={venue.url}
                            parserFunc={venue.parser}
                            onResult={handleResult}
                            onLoading={(isLoading) => handleLoading(venue.title, isLoading)}
                            onlyToday={globalOnlyToday}
                            setOnlyToday={setGlobalOnlyToday}
                            trigger={triggerAll}
                            expandTrigger={expandAllCounter}
                            collapseTrigger={collapseAllCounter}
                        />
                    ))}
                </div>
            </div>

            <div className="generator-wrapper" style={{ display: view === "instagram" ? "block" : "none" }}>
                <InstagramGeneratorPage data={hasAiResults ? aiResults : allResults} />
            </div>
        </div>
    )
}

export default App
