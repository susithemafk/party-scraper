import { useState } from "react"
import "./App.css"
import { ScraperSection } from "./components/ScraperSection"
import { AiProcessor } from "./components/AiProcessor"
import { artbarParser } from "./parsers/artbar"

function App() {
    const [scrapedItems, setScrapedItems] = useState([])

    const handleScrapedData = (newData) => {
        setScrapedItems((prev) => {
            const combined = [...prev, ...newData]
            return combined
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
