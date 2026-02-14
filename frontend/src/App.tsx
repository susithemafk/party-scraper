import React, { useState, useCallback, useMemo } from "react"
import "./App.css"
import { ScraperSection } from "./components/ScraperSection"
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

const App: React.FC = () => {
    const [triggerAll, setTriggerAll] = useState(0)
    const [allResults, setAllResults] = useState<Record<string, ScrapedItem[]>>({})
    const [copiedAll, setCopiedAll] = useState(false)

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
        const unique = flattened.filter(item => {
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
        if (aggregatedResults.length === 0) return
        navigator.clipboard.writeText(JSON.stringify(aggregatedResults, null, 4)).then(() => {
            setCopiedAll(true)
            setTimeout(() => setCopiedAll(false), 2000)
        })
    }, [aggregatedResults])

    return (
        <div className="container">
            <h1>Party Scraper</h1>
            <p className="subtitle">Automated Event Intelligence</p>

            <div className="bulk-controls" style={{ marginBottom: "2rem", display: "flex", gap: "1rem", justifyContent: "center" }}>
                <button onClick={handleFetchAll} className="fetch-all-btn">
                    FETCH ALL SCRAPERS
                </button>
                {aggregatedResults.length > 0 && (
                    <button
                        onClick={handleCopyAll}
                        className="copy-btn"
                        style={{ background: copiedAll ? "var(--success)" : "var(--primary)" }}
                    >
                        {copiedAll ? "Copied All!" : `Copy All (${aggregatedResults.length})`}
                    </button>
                )}
            </div>

            <div className="main-content">
                <ScraperSection
                    title="Bobyhall"
                    defaultUrl="https://bobyhall.cz/program-bobyhall/"
                    parserFunc={bobyhallParser}
                    triggerFetch={triggerAll}
                    onResult={handleResult}
                />

                <ScraperSection
                    title="Fraktal (via RA)"
                    defaultUrl="https://ra.co/clubs/224489"
                    parserFunc={raParser}
                    triggerFetch={triggerAll}
                    onResult={handleResult}
                />

                <ScraperSection
                    title="Metro Music Bar"
                    defaultUrl="https://www.metromusic.cz/program/"
                    parserFunc={metroParser}
                    triggerFetch={triggerAll}
                    onResult={handleResult}
                />

                <ScraperSection
                    title="První patro"
                    defaultUrl="https://patrobrno.cz/"
                    parserFunc={patroParser}
                    triggerFetch={triggerAll}
                    onResult={handleResult}
                />

                <ScraperSection
                    title="Perpetuum"
                    defaultUrl="https://www.perpetuumklub.cz/program/"
                    parserFunc={perpetuumParser}
                    triggerFetch={triggerAll}
                    onResult={handleResult}
                />

                <ScraperSection
                    title="Fléda"
                    defaultUrl="https://www.fleda.cz/program/"
                    parserFunc={fledaParser}
                    triggerFetch={triggerAll}
                    onResult={handleResult}
                />

                <ScraperSection
                    title="Sono Music Club"
                    defaultUrl="https://www.sono.cz/program/"
                    parserFunc={sonoParser}
                    triggerFetch={triggerAll}
                    onResult={handleResult}
                />

                <ScraperSection
                    title="Kabinet Múz"
                    defaultUrl="https://www.kabinetmuz.cz/program"
                    parserFunc={kabinetParser}
                    triggerFetch={triggerAll}
                    onResult={handleResult}
                />

                <ScraperSection
                    title="Artbar Club"
                    defaultUrl="https://www.artbar.club/shows"
                    parserFunc={artbarParser}
                    triggerFetch={triggerAll}
                    onResult={handleResult}
                />
            </div>
        </div>
    )
}

export default App
