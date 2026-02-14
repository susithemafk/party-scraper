import React, { useState } from "react"
import "./App.css"
import { ScraperSection } from "./components/ScraperSection"
import { AiProcessor } from "./components/AiProcessor"
import { artbarParser } from "./parsers/artbar"
import { ScrapedItem } from "./types"

const App: React.FC = () => {
    const [scrapedItems, setScrapedItems] = useState<ScrapedItem[]>([])

    const handleScrapedData = (newData: ScrapedItem[]) => {
        setScrapedItems((prev) => {
            const combined = [...prev, ...newData]
            // Simple uniqueness filter
            const seen = new Set()
            return combined.filter(item => {
                const key = `${item.url}-${item.date}`
                if (seen.has(key)) return false
                seen.add(key)
                return true
            })
        })
    }

    return (
        <div className="container">
            <h1>Party Scraper</h1>
            <p className="subtitle">Automated Event Intelligence</p>

            <div className="main-content">
                <ScraperSection title="Artbar Club" defaultUrl="https://www.artbar.club/shows" parserFunc={artbarParser} onResult={handleScrapedData} />

                {/* AI Processor Section - Separate as requested */}
                <AiProcessor inputData={scrapedItems} />
            </div>
        </div>
    )
}

export default App
