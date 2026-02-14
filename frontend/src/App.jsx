import "./App.css"
import { ScraperSection } from "./components/ScraperSection"
import { AiProcessor } from "./components/AiProcessor"
import { artbarParser } from "./parsers/artbar"

function App() {
    return (
        <div className="container">
            <h1>Party Scraper</h1>
            <p className="subtitle">Automated Event Intelligence</p>

            <div className="main-content">
                <ScraperSection title="Artbar Club" defaultUrl="https://www.artbar.club/shows" parserFunc={artbarParser} />

                {/* AI Processor Section - Separate as requested */}
                <AiProcessor />
            </div>
        </div>
    )
}

export default App
