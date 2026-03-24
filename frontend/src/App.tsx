import React, { useState, useCallback, useMemo, useEffect } from "react"
import "./App.css"
import { ScraperSection } from "./components/ScraperSection"
import { AiProcessor } from "./components/AiProcessor"
import { StudioEditor } from "./components/StudioEditor"
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
    {
        title: "Bobyhall",
        url: "https://bobyhall.cz/program-bobyhall/",
        baseUrl: "https://bobyhall.cz/",
        parser: bobyhallParser,
    },
    {
        title: "Fraktal",
        url: "https://ra.co/clubs/224489/events",
        baseUrl: "https://ra.co/",
        parser: raParser,
    },
    {
        title: "pul.pit",
        url: "https://ra.co/clubs/206733/events",
        baseUrl: "https://ra.co/",
        parser: raParser,
    },
    {
        title: "Metro Music Bar",
        url: "https://www.metromusic.cz/program/",
        baseUrl: "https://www.metromusic.cz/",
        parser: metroParser,
    },
    {
        title: "První patro",
        url: "https://patrobrno.cz/",
        baseUrl: "https://patrobrno.cz/",
        parser: patroParser,
    },
    {
        title: "Perpetuum",
        url: "https://www.perpetuumklub.cz/program/",
        baseUrl: "https://www.perpetuumklub.cz/",
        parser: perpetuumParser,
    },
    {
        title: "Fléda",
        url: "https://www.fleda.cz/program/",
        baseUrl: "https://www.fleda.cz/",
        parser: fledaParser,
    },
    {
        title: "Sono Music Club",
        url: "https://www.sono.cz/program/",
        baseUrl: "https://www.sono.cz/",
        parser: sonoParser,
    },
    {
        title: "Kabinet Múz",
        url: "https://www.kabinetmuz.cz/program",
        baseUrl: "https://www.kabinetmuz.cz/",
        parser: kabinetParser,
    },
    {
        title: "Artbar",
        url: "https://www.artbar.club/shows",
        baseUrl: "https://www.artbar.club/",
        parser: artbarParser,
    },
]

const App: React.FC = () => {
    const [triggerAll, setTriggerAll] = useState(0)
    const [expandAllCounter, setExpandAllCounter] = useState(0)
    const [collapseAllCounter, setCollapseAllCounter] = useState(0)
    const [allResults, setAllResults] = useState<Record<string, ScrapedItem[]>>({})
    const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({})
    const [aiResults, setAiResults] = useState<Record<string, any[]>>({})
    const [studioData, setStudioData] = useState<Record<string, any[]>>({})
    const [copiedAll, setCopiedAll] = useState(false)
    const [globalOnlyToday, setGlobalOnlyToday] = useState(false)
    const [weekAnchorDate, setWeekAnchorDate] = useState(new Date().toISOString().split("T")[0])
    const [view, setView] = useState<"scraper" | "studio">("scraper")

    const getWeekBounds = useCallback((dateStr: string) => {
        const base = new Date(`${dateStr}T00:00:00`)
        const day = base.getDay()
        const diffToMonday = day === 0 ? -6 : 1 - day

        const monday = new Date(base)
        monday.setDate(base.getDate() + diffToMonday)

        const sunday = new Date(monday)
        sunday.setDate(monday.getDate() + 6)

        const toIso = (d: Date) => {
            const year = d.getFullYear()
            const month = String(d.getMonth() + 1).padStart(2, "0")
            const date = String(d.getDate()).padStart(2, "0")
            return `${year}-${month}-${date}`
        }

        const toShort = (d: Date) => `${d.getDate()}.${d.getMonth() + 1}.`

        return {
            start: toIso(monday),
            end: toIso(sunday),
            label: `${toShort(monday)} - ${toShort(sunday)}`,
        }
    }, [])

    const handleFetchAll = useCallback(() => {
        setAllResults({})
        setTriggerAll((prev) => prev + 1)
    }, [])

    const handleLoading = useCallback((title: string, isLoading: boolean) => {
        setLoadingStates((prev) => {
            if (prev[title] === isLoading) return prev
            return { ...prev, [title]: isLoading }
        })
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
        const flattened = Object.entries(allResults).flatMap(([venue, items]) => items.map((item) => ({ ...item, venue })))

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

    const selectedWeek = useMemo(() => getWeekBounds(weekAnchorDate), [weekAnchorDate, getWeekBounds])

    const weekFilteredAggregatedResults = useMemo(
        () => aggregatedResults.filter((item) => !!item.date && item.date >= selectedWeek.start && item.date <= selectedWeek.end),
        [aggregatedResults, selectedWeek],
    )

    const handleCopyAll = useCallback(() => {
        const output: Record<string, { date: string | null; url: string }[]> = {}

        weekFilteredAggregatedResults.forEach((item) => {
            const venue = item.venue || "Other"
            if (!output[venue]) output[venue] = []
            output[venue].push({
                date: item.date,
                url: item.url,
            })
        })

        if (Object.keys(output).length === 0) return

        navigator.clipboard.writeText(JSON.stringify(output, null, 4)).then(() => {
            setCopiedAll(true)
            setTimeout(() => setCopiedAll(false), 2000)
        })
    }, [weekFilteredAggregatedResults])

    const hasAiResults = Object.keys(aiResults).length > 0
    const baseResults = useMemo(() => (hasAiResults ? aiResults : allResults), [hasAiResults, aiResults, allResults])

    useEffect(() => {
        if (Object.keys(studioData).length === 0) {
            setStudioData(baseResults)
        }
    }, [baseResults, studioData])

    const finalResults = Object.keys(studioData).length > 0 ? studioData : baseResults

    const activeScrapersCount = Object.values(loadingStates).filter(Boolean).length
    const isAnyLoading = activeScrapersCount > 0

    return (
        <div className="container">
            <div>
                <div
                    className="view-selector"
                    style={{
                        display: "flex",
                        gap: "1rem",
                        justifyContent: "center",
                        marginBottom: "2rem",
                    }}
                >
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
                        onClick={() => setView("studio")}
                        style={{
                            padding: "0.5rem 1.5rem",
                            borderRadius: "2rem",
                            border: "1px solid var(--primary)",
                            background: view === "studio" ? "var(--primary)" : "transparent",
                            color: "white",
                            cursor: "pointer",
                        }}
                    >
                        Studio
                    </button>
                </div>

                <div className="main-content-wrapper" style={{ display: view === "scraper" ? "block" : "none" }}>
                    <h1>Party Scraper</h1>
                    <p className="subtitle">Automated Event Intelligence</p>

                    <div
                        className="bulk-controls"
                        style={{
                            marginBottom: "2rem",
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "1rem",
                            justifyContent: "center",
                            alignItems: "center",
                        }}
                    >
                        <div style={{ position: "relative" }}>
                            <button onClick={handleFetchAll} className="fetch-all-btn" disabled={isAnyLoading}>
                                {isAnyLoading ? `FETCHING... (${activeScrapersCount}/${VENUES.length})` : `FETCH ALL SCRAPERS (${VENUES.length})`}
                            </button>
                            {isAnyLoading && <div className="fetching-loader-bar"></div>}
                        </div>

                        <div style={{ display: "flex", gap: "0.5rem" }}>
                            <button
                                className="secondary-button"
                                style={{ padding: "0.5rem 1rem", fontSize: "0.8rem" }}
                                onClick={() => setExpandAllCounter((prev) => prev + 1)}
                            >
                                <i className="bi bi-arrows-expand"></i> OPEN ALL
                            </button>
                            <button
                                className="secondary-button"
                                style={{ padding: "0.5rem 1rem", fontSize: "0.8rem" }}
                                onClick={() => setCollapseAllCounter((prev) => prev + 1)}
                            >
                                <i className="bi bi-arrows-collapse"></i> CLOSE ALL
                            </button>
                        </div>

                        <label
                            className="global-filter"
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "0.5rem",
                                cursor: "pointer",
                                fontSize: "0.9rem",
                                color: "var(--text-muted)",
                            }}
                        >
                            <input
                                type="checkbox"
                                checked={globalOnlyToday}
                                onChange={(e) => setGlobalOnlyToday(e.target.checked)}
                                style={{
                                    width: "1.1rem",
                                    height: "1.1rem",
                                    accentColor: "var(--primary)",
                                }}
                            />
                            ONLY TODAY (GLOBAL)
                        </label>
                        <label
                            className="global-filter"
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "0.5rem",
                                fontSize: "0.9rem",
                                color: "var(--text-muted)",
                            }}
                        >
                            WEEK DATE
                            <input
                                type="date"
                                value={weekAnchorDate}
                                onChange={(e) => setWeekAnchorDate(e.target.value)}
                                style={{
                                    background: "#0f172a",
                                    color: "#e2e8f0",
                                    border: "1px solid var(--border)",
                                    borderRadius: "0.4rem",
                                    padding: "0.4rem 0.6rem",
                                }}
                            />
                            <span style={{ fontWeight: 700 }}>{selectedWeek.label}</span>
                        </label>

                        {weekFilteredAggregatedResults.length > 0 && (
                            <div style={{ display: "flex", gap: "1rem" }}>
                                <button
                                    onClick={handleCopyAll}
                                    className="copy-btn"
                                    style={{
                                        background: copiedAll ? "var(--success)" : "var(--primary)",
                                    }}
                                >
                                    {copiedAll ? "Copied All (JSON)!" : `Copy All (${weekFilteredAggregatedResults.length})`}
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="main-content">
                        <AiProcessor inputData={weekFilteredAggregatedResults} onComplete={handleAiComplete} switchToStudio={() => setView("studio")} />

                        {VENUES.map((venue) => (
                            <ScraperSection
                                key={venue.title}
                                title={venue.title}
                                defaultUrl={venue.url}
                                baseUrl={venue.baseUrl}
                                parserFunc={venue.parser}
                                onResult={handleResult}
                                onLoading={(isLoading) => handleLoading(venue.title, isLoading)}
                                onlyToday={globalOnlyToday}
                                setOnlyToday={setGlobalOnlyToday}
                                weekStart={selectedWeek.start}
                                weekEnd={selectedWeek.end}
                                trigger={triggerAll}
                                expandTrigger={expandAllCounter}
                                collapseTrigger={collapseAllCounter}
                            />
                        ))}
                    </div>
                </div>

                <div className="studio-wrapper" style={{ display: view === "studio" ? "block" : "none" }}>
                    <StudioEditor data={finalResults} onChange={setStudioData} />
                </div>
            </div>
        </div>
    )
}

export default App
